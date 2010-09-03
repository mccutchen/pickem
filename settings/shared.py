import os, sys

PROJECT_ROOT = os.path.realpath(
    os.path.dirname(
        os.path.dirname(__file__)))

# See if we're running in production or in development
PRODUCTION = 'Development' not in os.environ.get('SERVER_SOFTWARE', '')
DEBUG = not PRODUCTION

TEMPLATE_DIR = os.path.join(PROJECT_ROOT, 'templates')


##############################################################################
# Secrets -- These settings MUST be set in secrets.py, which should not be
# kept in version control.  They should be kept, uh, secret.
##############################################################################
FB_APP_ID = ''
FB_APP_SECRET = ''

# Used to sign cookies. Generate with something like `os.urandom(30)`
SECRET = None
