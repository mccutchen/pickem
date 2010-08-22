#!/usr/bin/env python
from ext.webapp2 import WSGIApplication

import urls
import settings

app = WSGIApplication(urls.urls, debug=settings.DEBUG)

def main():
    app.run()

if __name__ == '__main__':
    main()
