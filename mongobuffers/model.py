import datetime
import copy 
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
      
class Model(object):
    __metaclass__ = ModelType
    collection = ''
    
    def __init__(self, data=None, **kwargs):
        if data is None:
            self.data = {}
            return
            
        if isinstance(data, dict):
            self.data = data
        else:
            self.data = kwargs
    
    def _has_field(self, name):
        return name in self.map_name_to_field
        
    def _get_field(self, name):
        return self.map_name_to_field.get(name) 
        
    def _get_field_by_id(self, id):
        return self.map_id_to_field.get(id)
      
    def get_field_id(self, name):
        if not self._has_field(name):
            raise Exception("Field %s not defined." % name)
        return self.map_name_to_field.get(name).get_id()
         
    def _set_field(self, name, value):
        field = self._get_field(name)
        self[field.get_tag()] = value
        
    def get_id(self):
        return self.data.get('_id', None)
        
    def get(self, name):
        if not self._has_field(name):
            raise Exception("Field %s not defined." % name)
            
        field = self._get_field(name)
        field_id = field.get_id()
        field_type = field.get_type()
        
        if field.required is True:
            # ensure required are set
            if field_id not in self.data:
                raise Exception("Required field %s not set in model %s (id:%s)" % (name, self.__class__.__name__, self.get_id()))
            return self.data.get(field_id)
            
        if field_id not in self.data:
            return field_type()
        return self.data.get(field_id) 
        
    def set(self, name, value):
        if not self._has_field(name):
            raise Exception("Field %s not defined." % name)
        
        field = self._get_field(name)
        field_id = field.get_id()
        field_type = field.get_type()
        self.data[field_id] = value
        
    def set_immediate(self, field, value):
        if not isinstance(field, list):
            field = [field]
            value = [value]
        elif isinstance(field, list) and not isinstance(value, list):
            raise Exception("if fields is a list, values must be a list too.")
        
        _field_ids = []
        
        for field in field:
            if not self._has_field(name):
                raise Exception("Field %s not defined." % name)
                
            _field_ids.append(self._get_field(name).get_id())
            
        update_dict = dict(zip(_field_ids, value))
        
        match_options = {
            '_id':self.get_id()
        }
        
        set_options = {
            '$set':update_dict
        }
        self.get_collection().update(match_options, set_options)    
    
    # connectivity
    def get_collection_name(self):
        if not self.collection:
            raise Exception("Collection name not defined on class %s" % self.__class__.__name__)
        return self.collection
        
    def get_collection(self):
        return getattr(self.get_connection(), self.get_collection_name())
        
    def get_connection(self):
        return self.connection
      
    def save(self):
        id = self.get_collection().save(self.data)
        
        if self.get_id() is None:
            self.data['_id'] = id
        
    @classmethod
    def set_connection(cls, connection):
        cls.connection = connection
        
    @classmethod
    def connect(cls, connection):
        ''' Returns a copy of this class that uses connection as its connection. '''
        cls_copy = copy.deepcopy(cls)
        cls_copy.set_connection(connection)
        return cls_copy
        
