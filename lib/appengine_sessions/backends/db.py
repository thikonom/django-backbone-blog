""" Fix Django's 'write-through' (cache and datastore storage) session
backend to work with Appengine's datastore, along with whatever cache
backend is in settings.

Basically a reworking of django.contrib.sessions.backends.db, so have
a look there for definitive docs.
"""

import datetime

from google.appengine.ext import db

from django.contrib.sessions.backends.base import  CreateError
from django.contrib.sessions.backends.db import SessionStore as DBStore
from django.core.exceptions import SuspiciousOperation
from django.utils.encoding import force_unicode


class SessionStore(DBStore):
    """Implements a session store using Appengine's datastore API instead
    of Django's abstracted DB API (since we no longer have nonrel -- just
    vanilla Django)
    """
    def __init__(self, session_key=None):
        super(SessionStore, self).__init__(session_key)

    def load(self):
        s = Session.get_by_key_name('session-%s' % self.session_key)

        if s:
            if s.expire_date > datetime.datetime.now():
                try:
                    return self.decode(force_unicode(s.session_data))
                except SuspiciousOperation:
                    return {}
        self.create()
        return {}

    def exists(self, session_key):
        s = Session.get_by_key_name('session-%s' % session_key)
        return s is not None

    def save(self, must_create=False):
        """Create and save a Session object using db.run_in_transaction, with
        key_name = 'session-%s' % session_key, raising CreateError if
        unsuccessful.
        """
        s = Session.get_by_key_name('session-%s' % self.session_key)
        if must_create:
            if s:
                raise CreateError()

        session_data = self._get_session(no_load=must_create)

        def txn():
            s = Session(
                key_name='session-%s' % self.session_key,
                session_key='session-%s' % self.session_key,
                session_data=self.encode(session_data),
                expire_date=self.get_expiry_date()
            )
            s.put()

        # This is tricky and probably needs some sanity checking, because
        # TransactionFailedError can be raised, but the transaction can still
        # go on to be committed to the datastore. As far as I can see there's
        # no way to manually roll it back at that point. No idea how to test
        # this either.
        try:
            db.run_in_transaction(txn)
        except (db.TransactionFailedError, db.Rollback):
            raise CreateError()

    def delete(self, session_key=None):
        if session_key is None:
            if self._session_key is None:
                return
            session_key = self._session_key

        db.delete(db.Key.from_path('Session', 'session-%s' % session_key))


# Again, circular import fix
from appengine_sessions.models import Session
