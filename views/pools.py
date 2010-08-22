import logging
from lib.webapp import RequestHandler


class IndexHandler(RequestHandler):

    def get(self):


class PoolsHandler(RequestHandler):
    pass


class PoolHandler(RequestHandler):
        if not self.account:
            return self.render('pools/index.html')
        else:
            pools = self.account.pools.fetch(1000)
            entries = self.account.entries.fetch(1000)
            ctx = {
                'form': forms.PoolForm(),
                }
            if not pools and not entries:
                return self.render('pools/start.html', ctx)
            else:
                ctx.update({
                        'pools': pools,
                        'entries': entries,
                        })
                return self.render('pools/dashboard.html', ctx)
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
