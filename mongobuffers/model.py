import datetime
import copy 
import types

from mongobuffers.errors import UndefinedFieldError
from mongobuffers.field import Field
    
class ModelType(type):
    def __init__(cls, name, bases, dict):
        type.__init__(cls, name, bases, dict)
        
        cls.map_name_to_field = {}
        cls.map_id_to_field = {}
        
        for k,v in dict.iteritems():
            
            if not isinstance(v, Field):
                continue
                
            cls.map_name_to_field[k] = v
            cls.map_id_to_field[v.get_id()] = v
        print cls.map_id_to_field
       
class Model(object):
    __metaclass__ = ModelType
    collection = ''
    
    def __init__(self, data=None, **kwargs):
        if data is None:
            self.data = {}
            return
            
        if isinstance(data, dict):
            self.data = {}
            for k,v in data.iteritems():
                if isinstance(k, int):
                    k = str(k)
                self.data[k] = v
        else:
            self.data = kwargs
    
    @classmethod  
    def _has_field(self, name):
        return name in self.map_name_to_field
    
    @classmethod    
    def _get_field(self, name):
        return self.map_name_to_field.get(name) 
        
    @classmethod
    def _get_field_by_id(self, id):
        return self.map_id_to_field.get(id)
      
    @classmethod
    def get_field_id(self, name):
        if not self._has_field(name):
            raise UndefinedFieldError("Field %s not defined." % name)
        return self.map_name_to_field.get(name).get_id()
         
    def _set_field(self, name, value):
        field = self._get_field(name)
        self[field.get_tag()] = value
        
    def get_id(self):
        return self.data.get('_id', None)
        
    def get(self, name):
        if not self._has_field(name):
            raise UndefinedFieldError("Field %s not defined." % name)
            
        field = self._get_field(name)
        field_id = field.get_id()
        field_type = field.get_type()
        field_repeats = field.get_repeated()
        
        if field.required is True:
            # ensure required are set
            if field_id not in self.data:
                raise Exception("Required field %s not set in model %s (id:%s)" % (name, self.__class__.__name__, self.get_id()))
                
            val = self.data.get(field_id)
            if isinstance(val, dict) and Model in field_type.__mro__:
                val = field_type(val)
            
        #print "Get", name, "Actual id", field_id
        
        if field_id not in self.data:
            if field_repeats:
                return []
                
            return field_type()
         
        val = self.data.get(field_id)
        
        if isinstance(val, dict) and isinstance(field_type, (type, types.ClassType)):
            val = field_type(val)
        return val
        
        
    def prepare_for_storage(self, name, field, value):
        field_id = field.get_id()
        field_type = field.get_type()
        field_repeats = field.get_repeated()
        
        if field_repeats:
            # repeatable fields must be lists
            if not isinstance(value, list):
                raise ValueError("Cannot set %s. Value must be a list of %s" % (name, field_type))
            
            # validate each of the lists values
            for i, v in enumerate(value):
                if isinstance(v, field_type):
                    continue
                raise ValueError("Invalid repeated field value at %s for list '%s'. Each item be of type %s. Got %s" % (i, name, field_type, type(v)))
        else:
            if not isinstance(value, field_type):
                raise ValueError("Cannot set %s. Value must be a %s" % (name, field_type))
         
        if isinstance(value, Model):
            if field_type not in value.__class__.__mro__:
                raise ValueError("Setting a submodel field with an invalid type. Must be %s as defined in %s" % (field_type, self.__class__.__name__))
            print "Serializing model value", name
            val = value.serialize()
        else:
            val = value
        return val        
        
    @classmethod    
    def spec(self, spec):
        ''' Returns mongo search spec with symbolic names converted into field ids. 
        '''
        newspec = {}
        for k, v in spec.iteritems():
            newk = k
            
            if not k.startswith('$') and not k == "_id":
                if not self._has_field(k):
                    raise UndefinedFieldError("Field %s not defined." % k)
                newk= self._get_field(k).get_id()
                    
            if isinstance(v, dict):
                newspec[newk] = self.spec(v)
            elif isinstance(v, list):
                newspec[newk] = []
                
                for listv in v:
                    if isinstance(listv, dict):
                        newspec[newk].append(self.spec(listv))
                    else:
                        newspec[newk].append(v)
            else:
                newspec[newk] = v
        return newspec
                
                
        
    def set(self, name, value):
        if not self._has_field(name):
            raise UndefinedFieldError("Field %s not defined." % name)
        
        field = self._get_field(name)
        field_id = field.get_id()
        field_type = field.get_type()
        field_repeats = field.get_repeated()
        
        self.data[field_id] = self.prepare_for_storage(name, field, value)
        
    def set_immediate_multi(self, names, values):
        ''' Immediately set multiple fields at the same.
            
            This uses the mongo update call to update only whats necessary.
        '''
        if not isinstance(names, list) or not isinstance(values, list):
            raise Exception("fields and values must both be lists")
        
        _field_ids = []
        _values = []
        
        for name, value in zip(names, values):
            if not self._has_field(name):
                raise UndefinedFieldError("Field %s not defined." % name)
            
            field = self._get_field(name)
            _field_ids.append(field.get_id())
            _values.append(self.prepare_for_storage(name, field, value))
        
        update_dict = dict(zip(_field_ids, _values))
        
        match_options = {
            '_id':self.get_id()
        }
        
        set_options = {
            '$set':update_dict
        }
        self.get_collection().update(match_options, set_options)    
        
    def set_immediate(self, name, value):
        ''' Set a field or fields immediately in the database.
        
            This uses the mongo update call to update only whats necessary.
        
            Args:
            
                name: A field name
                
                value: A field value
        '''
        
        if not self._has_field(name):
            raise UndefinedFieldError("Field %s not defined." % name)
            
        field = self._get_field(name)
        
        value = self.prepare_for_storage(name, field, value)
            
        update_dict = {field.get_id(): value}
        
        match_options = {
            '_id':self.get_id()
        }
        
        set_options = {
            '$set':update_dict
        }
        self.get_collection().update(match_options, set_options, safe=True)    
    
    def save(self):
        id = self.get_collection().save(self.data, safe=True)
        
        # store the id back
        if self.get_id() is None:
            self.data['_id'] = id
            
        return id
        
    @classmethod
    def get_collection_name(self):
        if not self.collection:
            raise Exception("Collection name not defined on class %s" % self.__class__.__name__)
        return self.collection
        
    @classmethod
    def get_collection(self):
        return getattr(self.get_database(), self.get_collection_name())
        
    @classmethod
    def get_database(self):
        return self.database
      
    @classmethod
    def set_database(cls, database):
        cls.database = database
        
    @classmethod
    def connect(cls, database):
        ''' Returns a copy of this class that uses connection as its connection. '''
        cls_copy = copy.deepcopy(cls)
        cls_copy.set_database(database)
        
        # patch in some methods of the collections object
        collection = cls_copy.get_collection()
        for method in ['remove', 'find', 'find_one','count','create_index','ensure_index','drop_index', 'drop_indexes', 'group', 'find_and_modify']:
            setattr(cls_copy, method, getattr(collection, method))
        
        return cls_copy
        
    def serialize(self):
        return self.data
