import logging
from lib.webapp import RequestHandler


class IndexHandler(RequestHandler):

    def get(self):
        return self.render('index.html')


class PoolsHandler(RequestHandler):
    pass


class PoolHandler(RequestHandler):
    pass


class EntriesHandler(RequestHandler):
    pass


class EntryHandler(RequestHandler):
    pass


class PicksHandler(RequestHandler):
    pass


class PickHandler(RequestHandler):
    pass


class ManagePoolHandler(RequestHandler):
    pass
