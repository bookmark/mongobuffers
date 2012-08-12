import unittest
import datetime
from mongobuffers.api import Model, Field

class TestBuffer(Model):
    source_feed_title = Field(1, type=unicode, required=False)
    source_feed_summary = Field(2, type=unicode, required=False)
    source_feed_tags = Field(3, type=list, required=False)
    date_crawled = Field(4, type=datetime.datetime, required=False)
    videos = Field(5, type=list, required=False)
    tokens = Field(6, type=list, required=False)
    article_text = Field(7, type=unicode, required=False)
    source_name = Field(8, type=unicode, required=False)
    canonical_url = Field(9, type=unicode, required=False, info=''' The canonical url.
    
        This is primarily set after crawling a document; after following 301/302 redirects.
        
        This can be set by reading the canonical meta element.
    ''')
    
class TestBuffersBasic(unittest.TestCase):
    def setUp(self):
        pass
    
    def test_buffer_get(self):
        self.test_buffer = TestBuffer({9:'http://www.google.com'})
        self.assertEquals(self.test_buffer.get('canonical_url'), 'http://www.google.com')
        print self.test_buffer.data
        
    def test_buffer_set(self):
        self.test_buffer = TestBuffer()
        self.test_buffer.set('canonical_url', 'http://www.google.com')
        self.assertEquals(self.test_buffer.get('canonical_url'), 'http://www.google.com')
        print self.test_buffer.data
        
        
if __name__ == '__main__':
    unittest.main()
