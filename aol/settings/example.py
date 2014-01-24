import sys

# For some reason we can't have a "POSTGIS_VERSION" variable since that
# interferes with something else, so I added a "YOUR_" prefix.
YOUR_POSTGIS_VERSION = 2

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': '',                      # Or path to database file if using sqlite3.
        # The following settings are not used with sqlite3:
        'USER': '',
        'PASSWORD': '',
        'HOST': '',                      # Empty for localhost through domain sockets or '127.0.0.1' for localhost through TCP.
        'PORT': '',                      # Set to empty string for default.
        'OPTIONS': {
            'options': '-c search_path=public'
        }
    }
}

# specify the test user for the db
if 'test' in sys.argv:
    DATABASES['default']['USER'] = 'super'
    DATABASES['default']['PASSWORD'] = 'user'

# Make this unique, and don't share it with anybody.
SECRET_KEY = ''

