#!/usr/bin/env python
import os
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
