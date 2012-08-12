import unittest
import datetime
from mongobuffers.api import Model, Field, UndefinedFieldError

class TestSubModel(Model):
    title = Field(1, type=str, required=False)
    text = Field(2, type=str, required=False)
    tags = Field(3, type=str, required=False, repeated=True)
    
class TestModel(Model):
    title = Field(1, type=str, required=False)
    tags = Field(3, type=str, required=False, repeated=True)
    date = Field(4, type=datetime.datetime, required=False)
    videos = Field(5, type=str, required=False, repeated=True)
    text = Field(7, type=str, required=False)
    url = Field(9, type=str, required=False, info='''''')
    submodel = Field(10, type=TestSubModel, required=False)
    
class TestBuffersBasic(unittest.TestCase):
    def setUp(self):
        self.test_buffer = TestModel({"9":'http://www.google.com', "3":['tag1', 'tag2'], "10":{"1":'title'}})
    
    def test_get(self):
        ''' Getting fields. '''
        self.assertEquals(self.test_buffer.get('url'), 'http://www.google.com')
        self.assertTrue(isinstance(self.test_buffer.get('tags'), list))
        self.assertEquals(self.test_buffer.get('tags'), ['tag1', 'tag2'])
        
    def test_get_undefined_repeated(self):
        self.assertTrue(isinstance(self.test_buffer.get('videos'), list))
    
    def test_set(self):
        ''' Setting fields. '''
        self.test_buffer.set('url', 'http://www.google.com')
        self.assertEquals(self.test_buffer.get('url'), 'http://www.google.com')
        
    def test_set_repeated(self):
        ''' Setting fields with repeated values. '''
        self.test_buffer.set('tags', ['tag1', 'tag2' ,'tag3'])
        self.assertEquals(self.test_buffer.get('tags'), ['tag1', 'tag2','tag3'])
       
    def test_set_repeated_with_invalid(self):
        self.assertRaises(ValueError, self.test_buffer.set, 'tags', ['tag1', 1])
        
    def test_set_repeated_with_uniterable(self):
        ''' Field marked as repeated accept only lists. '''
        self.assertRaises(ValueError, self.test_buffer.set, 'tags', 'tag1')
        
    def test_set_undefined_field(self):
        ''' Setting of undefined fields should raise an UndefinedFieldError. '''
        self.assertRaises(UndefinedFieldError, self.test_buffer.set, 'invalid', 'tag1')
        
    def test_submodel_get(self):
        ''' Getting submodels. '''
        submodel = self.test_buffer.get('submodel')
        self.assertTrue(isinstance(submodel, TestSubModel))
        self.assertEquals(submodel.get('title'), 'title')
     
    def test_submodel_set(self):
        ''' Setting submodels. '''
        newsubmodel = TestSubModel({"1":"test"})
        print "NEW SUBMODEL", newsubmodel.serialize()
        self.test_buffer.set('submodel', newsubmodel)
        submodel = self.test_buffer.get('submodel')
        self.assertEquals(submodel.get('title'), 'test')
        print "AFTER SET SUBMODEL", self.test_buffer.serialize()
        self.assertEquals(self.test_buffer.serialize(), {"9": 'http://www.google.com', "10": {"1": 'test'}, "3": ['tag1', 'tag2']})
        
    def test_invalid_submodel_set(self):
        "TEST SUBMODEL SET WITH INVALID"
        self.assertRaises(ValueError, self.test_buffer.set, 'submodel', 'invalid')
        
if __name__ == '__main__':
    unittest.main()
