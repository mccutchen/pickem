def url(*args, **kwargs):
    from main import app
    try:
        return app.url_for(*args, **kwargs)
    except KeyError, e:
        logging.warn('URL error: %s' % e)
        return '/xxx'
