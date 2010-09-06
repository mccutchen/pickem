#!/usr/bin/env python
import os, sys

extpath = os.path.join(os.path.dirname(__file__), 'ext')
if extpath not in sys.path:
    sys.path.append(extpath)

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

from ext.webapp2 import WSGIApplication

from google.appengine.dist import use_library
use_library('django', '1.1')

import urls
import settings

app = WSGIApplication(urls.urls, debug=settings.DEBUG)

def main():
    app.run()

if __name__ == '__main__':
    main()
