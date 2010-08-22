import logging
from lib.webapp import RequestHandler, SecureRequestHandler

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
                        })
                return self.render('pools/dashboard.html', ctx)


class PoolsHandler(SecureRequestHandler):

    def post(self):
        form = forms.PoolForm(self.request.params)
        if form.is_valid():
            form.cleaned_data['manager'] = self.account
            pool = form.save()
            return self.redirect_to('pool', pool.key().id())
        else:
            self.response.out.write(str(form.errors))
            self.set_status(400)


class PoolHandler(SecureRequestHandler):
    pass


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
