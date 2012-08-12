import datetime
import copy 
import types

from mongobuffers.errors import UndefinedFieldError
from mongobuffers.field import Field
    
class ModelType(type):
    def __init__(cls, name, bases, dict):
        # mangle the class
        # remove any fields so that __setattr__/__getattr__ work in instances
        fields = {}
        for k,v in dict.iteritems():
            if isinstance(v, Field):
                fields[k] = v
                delattr(cls, k)
                continue
            
        type.__init__(cls, name, bases, dict)
        
        #print "CLASS DICT", cls.__dict__
        # index the fields
        cls.map_name_to_field = {}
        cls.map_id_to_field = {}
        
        for k,v in fields.iteritems():
            cls.map_name_to_field[k] = v
            cls.map_id_to_field[v.get_id()] = v
        #print cls.map_id_to_field
       
class Model(object):
    __metaclass__ = ModelType
    _collection = ''
    _database = None
    _data = None
    
    __reserved__ = ['_data','get_id', '_has_field', '_get_field', '_get_field_by_id',
    'get_field_id', '_set_field', 'get', 'set', '_prepare_for_storage', 'spec', 'set','set_immediate_multi','set_immediate',
    'save','_collection','database','connect','serialize','set_database','get_database','get_collection','get_collection_name'
    ]
    def __init__(self, data=None, **kwargs):
        if data is None:
            self._data = {}
            return
            
        if isinstance(data, dict):
            self._data = {}
            for k,v in data.iteritems():
                if isinstance(k, int):
                    k = str(k)
                self._data[k] = v
        else:
            self._data = kwargs
            
    def get_id(self):
        return self._data.get('_id', None)
     
    def __setitem__(self, name, value):
        ''' Used by mongo. Do not use Model[]. '''
        return self._data.__setitem__(name, value)
        
    def __setattr__(self, name, value):
        if name in self.__reserved__:
            self.__dict__[name] = value
            return
        
        self.set(name, value)
        
    def __getattr__(self, name):
        if name in self.__reserved__:
            return self.__dict__[name]
        
        val = self.get(name)        
        
        print "GETATTR",name, val
        return val
        
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
        
       
    def get(self, name):
        if not self._has_field(name):
            raise UndefinedFieldError("Field %s not defined." % name)
            
        field = self._get_field(name)
        field_id = field.get_id()
        field_type = field.get_type()
        field_repeats = field.get_repeated()
        field_default = field.get_default()
        
        if field.required is True:
            # ensure required are set
            if field_id not in self._data:
                raise Exception("Required field %s not set in model %s (id:%s)" % (name, self.__class__.__name__, self.get_id()))
                
            val = self._data.get(field_id)
            if isinstance(val, dict) and Model in field_type.__mro__:
                val = field_type(val)
            
        #print "Get", name, "Actual id", field_id
        
        if field_id not in self._data:
            if field_repeats:
                return []
                
            # result a default value
            return field_default
         
        val = self._data.get(field_id)
        
        if isinstance(val, dict) and isinstance(field_type, (type, types.ClassType)):
            val = field_type(val)
        return val
        
        
    def _prepare_for_storage(self, name, field, value):
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
        
        val = self._prepare_for_storage(name, field, value)
        self._data[field_id] = val
        return val
        
    def set_immediate_multi(self, names, values):
        ''' Immediately set multiple fields at the same.
            
            This uses the mongo update call to update only whats necessary.
        '''
        if not isinstance(names, list) or not isinstance(values, list):
            raise Exception("fields and values must both be lists")
        
        _field_ids = []
        _values = []
        
        for name, value in zip(names, values):
            # set in memory first
            self.set(name, value)
            field = self._get_field(name)
            _field_ids.append(field.get_id())
            _values.append(self._prepare_for_storage(name, field, value))
        
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
        # set in memory first
        self.set(name, value)
        
        field = self._get_field(name)
        
        value = self._prepare_for_storage(name, field, value)
            
        update_dict = {field.get_id(): value}
        
        match_options = {
            '_id':self.get_id()
        }
        
        set_options = {
            '$set':update_dict
        }
        self.get_collection().update(match_options, set_options, safe=True)    
    
    def save(self):
        id = self.get_collection().save(self._data, safe=True)
        
        # store the id back
        if self.get_id() is None:
            self._data['_id'] = id
            
        return id
        
    @classmethod
    def get_collection_name(self):
        if not self._collection:
            raise Exception("Collection name not defined on class %s" % self.__name__)
        return self._collection
        
    @classmethod
    def get_collection(self):
        return getattr(self.get_database(), self.get_collection_name())
        
    @classmethod
    def get_database(self):
        return self._database
      
    @classmethod
    def set_database(cls, database):
        cls._database = database
        
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
        return self._data
