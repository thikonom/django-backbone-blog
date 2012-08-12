import base64
from datetime import datetime, timedelta
import pickle
import unittest

from google.appengine.ext import testbed

from appengine_sessions.backends.db import SessionStore as DatabaseSession
from appengine_sessions.backends.cached_db import SessionStore as CacheDBSession
from appengine_sessions.models import Session
from appengine_sessions.middleware import SessionMiddleware
from django.conf import settings
from django.http import HttpResponse
from django.utils.hashcompat import md5_constructor


class SessionTestsMixin(object):
    # This does not inherit from TestCase to avoid any tests being run with this
    # class, which wouldn't work, and to allow different TestCase subclasses to
    # be used.

    backend = None # subclasses must specify

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        self.session = self.backend()
        for s in Session.all():
            s.delete()

    def tearDown(self):
        # NB: be careful to delete any sessions created; stale sessions fill up
        # the /tmp (with some backends) and eventually overwhelm it after lots
        # of runs (think buildbots)
        self.session.delete()
        self.testbed.deactivate()

    def test_new_session(self):
        self.assertFalse(self.session.modified)
        self.assertFalse(self.session.accessed)

    def test_get_empty(self):
        self.assertEqual(self.session.get('cat'), None)

    def test_store(self):
        self.session['cat'] = "dog"
        self.assertTrue(self.session.modified)
        self.assertEqual(self.session.pop('cat'), 'dog')

    def test_pop(self):
        self.session['some key'] = 'exists'
        # Need to reset these to pretend we haven't accessed it:
        self.accessed = False
        self.modified = False

        self.assertEqual(self.session.pop('some key'), 'exists')
        self.assertTrue(self.session.accessed)
        self.assertTrue(self.session.modified)
        self.assertEqual(self.session.get('some key'), None)

    def test_pop_default(self):
        self.assertEqual(self.session.pop('some key', 'does not exist'),
                         'does not exist')
        self.assertTrue(self.session.accessed)
        self.assertFalse(self.session.modified)

    def test_setdefault(self):
        self.assertEqual(self.session.setdefault('foo', 'bar'), 'bar')
        self.assertEqual(self.session.setdefault('foo', 'baz'), 'bar')
        self.assertTrue(self.session.accessed)
        self.assertTrue(self.session.modified)

    def test_update(self):
        self.session.update({'update key': 1})
        self.assertTrue(self.session.accessed)
        self.assertTrue(self.session.modified)
        self.assertEqual(self.session.get('update key', None), 1)

    def test_has_key(self):
        self.session['some key'] = 1
        self.session.modified = False
        self.session.accessed = False
        self.assertTrue(self.session.has_key('some key'))
        self.assertTrue(self.session.accessed)
        self.assertFalse(self.session.modified)

    def test_values(self):
        self.assertEqual(self.session.values(), [])
        self.assertTrue(self.session.accessed)
        self.session['some key'] = 1
        self.assertEqual(self.session.values(), [1])

    def test_iterkeys(self):
        self.session['x'] = 1
        self.session.modified = False
        self.session.accessed = False
        i = self.session.iterkeys()
        self.assertTrue(hasattr(i, '__iter__'))
        self.assertTrue(self.session.accessed)
        self.assertFalse(self.session.modified)
        self.assertEqual(list(i), ['x'])

    def test_itervalues(self):
        self.session['x'] = 1
        self.session.modified = False
        self.session.accessed = False
        i = self.session.itervalues()
        self.assertTrue(hasattr(i, '__iter__'))
        self.assertTrue(self.session.accessed)
        self.assertFalse(self.session.modified)
        self.assertEqual(list(i), [1])

    def test_iteritems(self):
        self.session['x'] = 1
        self.session.modified = False
        self.session.accessed = False
        i = self.session.iteritems()
        self.assertTrue(hasattr(i, '__iter__'))
        self.assertTrue(self.session.accessed)
        self.assertFalse(self.session.modified)
        self.assertEqual(list(i), [('x',1)])

    def test_clear(self):
        self.session['x'] = 1
        self.session.modified = False
        self.session.accessed = False
        self.assertEqual(self.session.items(), [('x',1)])
        self.session.clear()
        self.assertEqual(self.session.items(), [])
        self.assertTrue(self.session.accessed)
        self.assertTrue(self.session.modified)

    def test_save(self):
        self.session.save()
        self.assertTrue(self.session.exists(self.session.session_key))

    def test_delete(self):
        self.session.delete(self.session.session_key)
        self.assertFalse(self.session.exists(self.session.session_key))

    def test_flush(self):
        self.session['foo'] = 'bar'
        self.session.save()
        prev_key = self.session.session_key
        self.session.flush()
        self.assertFalse(self.session.exists(prev_key))
        self.assertNotEqual(self.session.session_key, prev_key)
        self.assertTrue(self.session.modified)
        self.assertTrue(self.session.accessed)

    def test_cycle(self):
        self.session['a'], self.session['b'] = 'c', 'd'
        self.session.save()
        prev_key = self.session.session_key
        prev_data = self.session.items()
        self.session.cycle_key()
        self.assertNotEqual(self.session.session_key, prev_key)
        self.assertEqual(self.session.items(), prev_data)

    def test_invalid_key(self):
        # Submitting an invalid session key (either by guessing, or if the db has
        # removed the key) results in a new key being generated.
        try:
            session = self.backend('1')
            session.save()
            self.assertNotEqual(session.session_key, '1')
            self.assertEqual(session.get('cat'), None)
            session.delete()
        finally:
            # Some backends leave a stale cache entry for the invalid
            # session key; make sure that entry is manually deleted
            session.delete('1')

    # Custom session expiry
    def test_default_expiry(self):
        # A normal session has a max age equal to settings
        self.assertEqual(self.session.get_expiry_age(), settings.SESSION_COOKIE_AGE)

        # So does a custom session with an idle expiration time of 0 (but it'll
        # expire at browser close)
        self.session.set_expiry(0)
        self.assertEqual(self.session.get_expiry_age(), settings.SESSION_COOKIE_AGE)

    def test_custom_expiry_seconds(self):
        # Using seconds
        self.session.set_expiry(10)
        delta = self.session.get_expiry_date() - datetime.now()
        self.assertTrue(delta.seconds in (9, 10))

        age = self.session.get_expiry_age()
        self.assertTrue(age in (9, 10))

    def test_custom_expiry_timedelta(self):
        # Using timedelta
        self.session.set_expiry(timedelta(seconds=10))
        delta = self.session.get_expiry_date() - datetime.now()
        self.assertTrue(delta.seconds in (9, 10))

        age = self.session.get_expiry_age()
        self.assertTrue(age in (9, 10))

    def test_custom_expiry_datetime(self):
        # Using fixed datetime
        self.session.set_expiry(datetime.now() + timedelta(seconds=10))
        delta = self.session.get_expiry_date() - datetime.now()
        self.assertTrue(delta.seconds in (9, 10))

        age = self.session.get_expiry_age()
        self.assertTrue(age in (9, 10))

    def test_custom_expiry_reset(self):
        self.session.set_expiry(None)
        self.session.set_expiry(10)
        self.session.set_expiry(None)
        self.assertEqual(self.session.get_expiry_age(), settings.SESSION_COOKIE_AGE)

    def test_get_expire_at_browser_close(self):
        # Tests get_expire_at_browser_close with different settings and different
        # set_expiry calls
        try:
            try:
                original_expire_at_browser_close = settings.SESSION_EXPIRE_AT_BROWSER_CLOSE
                settings.SESSION_EXPIRE_AT_BROWSER_CLOSE = False

                self.session.set_expiry(10)
                self.assertFalse(self.session.get_expire_at_browser_close())

                self.session.set_expiry(0)
                self.assertTrue(self.session.get_expire_at_browser_close())

                self.session.set_expiry(None)
                self.assertFalse(self.session.get_expire_at_browser_close())

                settings.SESSION_EXPIRE_AT_BROWSER_CLOSE = True

                self.session.set_expiry(10)
                self.assertFalse(self.session.get_expire_at_browser_close())

                self.session.set_expiry(0)
                self.assertTrue(self.session.get_expire_at_browser_close())

                self.session.set_expiry(None)
                self.assertTrue(self.session.get_expire_at_browser_close())

            except:
                raise
        finally:
            settings.SESSION_EXPIRE_AT_BROWSER_CLOSE = original_expire_at_browser_close

    def test_decode(self):
        # Ensure we can decode what we encode
        data = {'a test key': 'a test value'}
        encoded = self.session.encode(data)
        self.assertEqual(self.session.decode(encoded), data)

    def test_decode_django12(self):
        # Ensure we can decode values encoded using Django 1.2
        # Hard code the Django 1.2 method here:
        def encode(session_dict):
            pickled = pickle.dumps(session_dict, pickle.HIGHEST_PROTOCOL)
            pickled_md5 = md5_constructor(pickled + settings.SECRET_KEY).hexdigest()
            return base64.encodestring(pickled + pickled_md5)

        data = {'a test key': 'a test value'}
        encoded = encode(data)
        self.assertEqual(self.session.decode(encoded), data)


class DatabaseSessionTests(SessionTestsMixin, unittest.TestCase):

    backend = DatabaseSession

    def test_session_get_decoded(self):
        """
        Test we can use Session.get_decoded to retrieve data stored
        in normal way
        """
        self.session['x'] = 1
        self.session.save()

        s = Session.get_by_key_name('session-%s' % self.session.session_key)

        self.assertEqual(s.get_decoded(), {'x': 1})

    def test_sessionmanager_save(self):
        """
        Test SessionManager.save method
        """
        # Create a session
        self.session['y'] = 1
        self.session.save()

        s = Session.get_by_key_name('session-%s' % self.session.session_key)


class CacheDBSessionTests(SessionTestsMixin, unittest.TestCase):

    backend = CacheDBSession


class FakeRequest(object):
    def __init__(self):
        self.COOKIES = {}

class SessionMiddlewareTests(unittest.TestCase):
    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        self.old_SESSION_COOKIE_SECURE = settings.SESSION_COOKIE_SECURE

    def tearDown(self):
        self.testbed.deactivate()
        settings.SESSION_COOKIE_SECURE = self.old_SESSION_COOKIE_SECURE

    def test_secure_session_cookie(self):
        settings.SESSION_COOKIE_SECURE = True

        request = FakeRequest()
        response = HttpResponse('Session test')
        middleware = SessionMiddleware()

        # Simulate a request the modifies the session
        middleware.process_request(request)
        request.session['hello'] = 'world'

        # Handle the response through the middleware
        response = middleware.process_response(request, response)
        self.assertTrue(response.cookies[settings.SESSION_COOKIE_NAME]['secure'])
