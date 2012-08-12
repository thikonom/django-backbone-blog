from google.appengine.ext import db


class Session(db.Model):
    session_key = db.StringProperty()
    session_data = db.TextProperty()
    expire_date = db.DateTimeProperty()

    def get_decoded(self):
        return SessionStore().decode(self.session_data)


# At the bottom to win against circular imports
from appengine_sessions.backends.db import SessionStore
