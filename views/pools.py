import logging
import datetime

from lib.webapp import RequestHandler, SecureRequestHandler
from lib.decorators import pool_required, entry_required

import models
import forms


class IndexHandler(RequestHandler):

    def get(self):
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
                        'slate': models.Slate.next(),
                        })
                return self.render('pools/dashboard.html', ctx)


class PoolsHandler(SecureRequestHandler):

    def post(self):
        form = forms.PoolForm(self.request.params)
        if form.is_valid():
            form.cleaned_data['manager'] = self.account
            pool = form.save()
            pool.add_entry(self.account)
            return self.redirect(
                self.url_for('pool', pool.key().id()))
        else:
            self.response.out.write(str(form.errors))
            self.set_status(400)


class PoolHandler(SecureRequestHandler):

    @pool_required
    def get(self, pool):
        entries = pool.entries.fetch(1000)
        active_entries = pool.active_entries.fetch(1000)
        unpaid_entries = pool.unpaid_entries.fetch(1000)
        ctx = dict(pool=pool,
                   entries=entries,
                   active_entries=active_entries,
                   unpaid_entries=unpaid_entries)
        return self.render('pools/pool.html', ctx)


class EntriesHandler(SecureRequestHandler):
    pass


class EntryHandler(SecureRequestHandler):
    pass


class PicksHandler(SecureRequestHandler):
    pass


class PickHandler(SecureRequestHandler):
    pass


class ManagePoolHandler(SecureRequestHandler):
    pass
