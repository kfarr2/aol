import os
from django.test.runner import DiscoverRunner

class AOLRunner(DiscoverRunner):
    def setup_databases(self, *args, **kwargs):
        to_return = super(AOLRunner, self).setup_databases(*args, **kwargs)
        from django.db import connection
        from django.conf import settings
        cursor = connection.cursor()
        path = settings.ROOT("aol", "test.sql")
        sql = open(path).read()
        cursor.execute(sql)
        return to_return
