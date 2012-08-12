#!/usr/bin/env python

from pypath import pypath
pypath()
import sys

# Don't allow `runserver` just yet, we haven't wrapped it here
if 'runserver' in sys.argv:
    sys.stderr.write(
        "Error: please uses `dev_appserver.py` to run your development server\n")
    sys.exit(1)


from django.core.management import execute_manager

try:
    import settings # Assumed to be in the same directory.
except ImportError:
    sys.stderr.write(
        "Error: Can't find the file `settings.py` in the directory"
        "containing %r. It appears you've customized things.\nYou'll have"
        "to run django-admin.py, passing it your settings module.\n(If the"
        "file `settings.py` does indeed exist, it's causing an ImportError"
        "somehow.)\n" % __file__)
    sys.exit(1)

if __name__ == "__main__": execute_manager(settings)
