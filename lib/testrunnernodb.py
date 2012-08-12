from django.test.simple import DjangoTestSuiteRunner

class TestRunnerNoDb(DjangoTestSuiteRunner):
    """ Subclass django's simple test runner and don't use the database (there
    won't be one if the app uses the datastore. """

    def setup_databases(self, **kwargs):
        pass

    def teardown_databases(self, old_config, **kwargs):
        pass
