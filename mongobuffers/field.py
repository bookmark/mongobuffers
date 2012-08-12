class Field(object):
    def __init__(self, id, type=None, required=None, info=None):
        self.id = id
        self.type = type
        self.required = required
        self.info = info
        
    def get_id(self):
        return self.id
        
    def get_type(self):
        return self.type
        
    def get_required(self):
        return self.required
                
    def get_info(self):
        return self.info
