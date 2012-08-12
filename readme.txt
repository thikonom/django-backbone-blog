##A streamlined Django and App Engine integration.

Run locally:

    git clone git@github.com:potatolondon/djappengine.git
    cd djappengine
    dev_appserver .

Visit <http://localhost:8000> to marvel at your work.

Now deploy to appspot, first set up an app on <http://appengine.google.com> and replace `application` in `app.yaml` with the name of your app (in your text editor or like this):

    sed -i '' 's/djappeng1ne/myappid/' app.yaml

You're ready to deploy:

    appcfg.py update .

The Django app in `core` is there to get you started. Have a look around.

##Running tests

    python manage.py test core
    .
    ----------------------------------------------------------------------
    Ran 1 test in 0.000s

djappengine uses a custom test runner that doesn't try to use a database. This is because djappengine is designed primarily to be used with 
[App Engine's models](https://developers.google.com/appengine/docs/python/datastore/datamodeling), and not with Django's ORM. If you're using
CloudSQL, comment out the [TEST_RUNNER](https://github.com/potatolondon/djappengine/blob/master/settings.py#L29) line in `settings.py`.

[core/tests.py](https://github.com/potatolondon/djappengine/blob/master/core/tests.py) is an example test that sets App Engine's 
[testbed](https://developers.google.com/appengine/docs/python/tools/localunittesting).

## So what's going on?

### app.yaml

- Sets up static resources
- Points all other paths to the WSGI app


### main.py

- Sets up env variables and the path
- Determines if we're running locally
- Routes logging for production
- Defines the WSGI app


### manage.py

- Friendly reminder not to use `runserver`, use `dev_appserver.py` for now
- Sorts out paths using dev_appserver

### settings.py

- Sets up caching
- Sets up sessions

### urls.py

- Just points to core’s url config

### lib/pypath.py

- Uses `dev_appserver` to set up the python path

### lib/memcache.py

- So App Engine's memcache is seen by django

### lib/testrunnernodb.py

- A custom test runner that lets you use Djanog's simple test runner to run tests with [App Engine's testbed](https://developers.google.com/appengine/docs/python/tools/localunittesting) and without a database.

### core

- A simple example app to get you started


## What's missing

[Something missing? [please raise an issue](https://github.com/potatolondon/djappengine/issues?state=open).