#!/usr/bin/env python
from ext.webapp2 import WSGIApplication
import urls

app = WSGIApplication(urls.urls)

def main():
    app.run()

if __name__ == '__main__':
    main()
