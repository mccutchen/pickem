#!/usr/bin/env python
import os, sys

extpath = os.path.join(os.path.dirname(__file__), 'ext')
if extpath not in sys.path:
    sys.path.append(extpath)

from ext.webapp2 import WSGIApplication

from google.appengine.dist import use_library
use_library('django', '1.1')

from data.urls import urls
import settings

app = WSGIApplication(urls, debug=settings.DEBUG)

def main():
    app.run()

if __name__ == '__main__':
    main()
