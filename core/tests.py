from pypath import pypath;pypath()
import unittest
from google.appengine.api import memcache
from google.appengine.ext import db
from google.appengine.ext import testbed
from models import Entry

class EntryTestCase(unittest.TestCase):
    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()

    def DummyEntryInsert(self):
        e = Entry(title="First Entry",
                  body_html="body_html",
                  body_markdown="body_markdown"
            )
        e.put()
        self.assertEqual(1, db.Query(Entry).count())

    def tearDown(self):
        self.testbed.deactivate()

if __name__ == '__main__':
    unittest.main()
