import logging
from ext.webapp2 import uri_for

def url(*args, **kwargs):
    try:
        return uri_for(*args, **kwargs)
    except KeyError, e:
        logging.warn('URL error: %s' % e)
        return '/xxx'
