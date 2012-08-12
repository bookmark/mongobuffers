import pymongo


import unittest
import datetime
from mongobuffers.api import Model, Field, UndefinedFieldError

from bson.objectid import ObjectId
class TestSubModel(Model):
    title = Field(1, type=str, required=False)
    text = Field(2, type=str, required=False)
    tags = Field(3, type=str, required=False, repeated=True)
    
class TestModel(Model):
    collection = "test"
    title = Field(1, type=str, required=False)
    tags = Field(3, type=str, required=False, repeated=True)
    date = Field(4, type=datetime.datetime, required=False)
    videos = Field(5, type=str, required=False, repeated=True)
    text = Field(7, type=str, required=False)
    url = Field(9, type=str, required=False, info='''''')
    submodel = Field(10, type=TestSubModel, required=False)
    summary = Field(11, type=str, required=False)
    iscached = Field(12, type=str, required=False)
    cache_had_exception = Field(13, type=str, required=False)
    http_status = Field(14, type=str, required=False)
    feed_link = Field(15, type=str, required=False)
    cache_attempts = Field(16, type=str, required=False)
    
class TestBuffersBasic(unittest.TestCase):
    def setUp(self):
        self.test_buffer = TestModel({"9":'http://www.google.com', "3":['tag1', 'tag2'], "10":{"1":'title'}})
        c = pymongo.Connection("mongo1")
        self.db = c.unittests
        
    def test_connect(self):
        self.TestModel = TestModel.connect(self.db)
    
    def test_search_spec(self):
        testspec = TestModel.spec({
            '$or':[
                    {
                        '$or': [{
                            'iscached':{'$exists':False}}, 
                            {'iscached':False}
                        ],
                        'cache_had_exception': {'$exists':False},
                        'http_status':{'$not':{'$in':[404, 302]}},
                        'feed_link':{'$exists':True},
                        'cache_attempts':{'$exists':False}
                    },
                    {
                        '$or': [{
                            'iscached':{'$exists':False}}, 
                            {'iscached':False}
                        ],
                        'cache_attempts':{'$lt':5},
                        'http_status':{'$not':{'$in':[404, 302]}},
                        'feed_link':{'$exists':True},
                    }
            ]
        })
        
        check_spec = {'$or': [{'$or': [{'12': {'$exists': False}}, {'12':
        False}], '13': {'$exists': False}, '15': {'$exists': True}, '14':
        {'$not': {'$in': [[404, 302], [404, 302]]}}, '16': {'$exists': False}},
        {'$or': [{'12': {'$exists': False}}, {'12': False}], '15': {'$exists':
        True}, '14': {'$not': {'$in': [[404, 302], [404, 302]]}}, '16': {'$lt':
        5}}]}
        
        self.assertEquals(testspec, check_spec)
        
        
    def test_save(self):
        self.TestModel = TestModel.connect(self.db)
        new = self.TestModel({"9":'http://www.google.com', "3":['tag1', 'tag2'], "10":{"1":'title'}})
        id = new.save()
        print 'ID', id
        new.set_immediate('title', 'test-immediate')
        new.set_immediate_multi(['text', 'summary'], ['test-immediate-multi:Text', 'test-immediate-multi:summary'])
        self.assertTrue(isinstance(new.get_id(), ObjectId))
    
    def test_find(self):
        self.TestModel = TestModel.connect(self.db)
        new = self.TestModel({"9":'http://www.google.com', "3":['tag1', 'tag2'], "10":{"1":'title'}})
        id = new.save()
        
        print 'After find', self.TestModel.find_one({'_id': id})
        spec = TestModel.spec({"title":"test-immediate"})
        print "SEARCH SPEC", spec
        print 'After find', self.TestModel.find_one(spec)
        self.fail()
        
if __name__ == '__main__':
    unittest.main()
