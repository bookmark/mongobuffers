class Field(object):
    ''' Holds information about a particular field.
    
        Args:
        
            id(integer): required - A numeric unique id in the history of all the models fields.
            
        Kwargs:
        
            type(type): required - The type the field should conform to. Can be str, int, datetime or another model.
            
            required(boolean): optional - Whether the field is required for the model to validate.
            
            repeated(boolean): optional - Whether the field can contain multiple values.
            
            info(str): optional - A place to store a comment or note about the field.
    '''
    def __init__(self, id, type=None, required=False, repeated=False, info=None):
        self.id = id
        self.type = type
        self.required = required
        self.info = info
        self.repeated = repeated
        
    def get_id(self):
        ''' Returns the fields id.
        
            The id is converted to a string because mongo allows only string keys in documents.
        '''
        return str(self.id)
        
    def get_type(self):
        ''' Returns the type the field should be.
        '''
        return self.type
        
    def get_required(self):
        ''' Returns true if the field is required. 
        
            Required is permanent.
        '''
        return self.required
                
    def get_info(self):
        ''' Returns the help/info string. 
        '''
        return self.info
    
    def get_repeated(self):
        ''' Returns true if the field is repeatable.
        
            Repeatable fields are modeled as lists.
            
            Fields marked as repeatable cannot be changed to unrepeatable.
        '''
        return self.repeated
        
    def __repr__(self):
        return "Field(%s, type=%s, required=%s)" % (self.get_id(), self.get_type(), self.get_required())
