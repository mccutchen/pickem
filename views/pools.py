import logging
import datetime

from google.appengine.ext import db
from webob.exc import HTTPNotFound, HTTPBadRequest

from lib.webapp import RequestHandler, SecureRequestHandler
from lib.decorators import objects_required

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
                        'week': models.Week.next(),
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

    @objects_required('Pool')
    def get(self, pool):
        entries = pool.entries.fetch(1000)
        active_entries = pool.active_entries.fetch(1000)
        unpaid_entries = pool.unpaid_entries.fetch(1000)
        week = models.Week.current()
        if not week:
            week = models.Week.next()
        picks = week.picks.fetch(1000) if week.started else []
        ctx = dict(pool=pool,
                   entries=entries,
                   active_entries=active_entries,
                   unpaid_entries=unpaid_entries,
                   season=week.parent(),
                   week=week,
                   picks=picks)
        return self.render('pools/pool.html', ctx)


class EntriesHandler(SecureRequestHandler):
    pass


class EntryHandler(SecureRequestHandler):

    @objects_required('Pool', 'Entry')
    def get(self, pool, entry):
        season = models.Season.current()
        weeks = season.weeks.fetch(25)
        week =  models.Week.next()
        ctx = dict(season=season,
                   weeks=weeks,
                   week=week,
                   pool=pool,
                   entry=entry,
                   picks=entry.picks.fetch(1000))

        if entry.account.key() == self.request.account.key():
            template = 'pools/my_entry.html'
        else:
            template = 'pools/public_entry.html'
        return self.render(template, ctx)


class PicksHandler(SecureRequestHandler):
    pass


class PickHandler(SecureRequestHandler):

    @objects_required('Pool', 'Entry')
    def get(self, pool, entry, week_num):
        season = models.Season.current()
        week_key = db.Key.from_path(
            'Week', int(week_num), parent=season.key())
        week = db.get(week_key)
        if week is None:
            raise HTTPNotFound('Week %s not found' % week_num)
        weeks = season.weeks.fetch(25)
        ctx = dict(season=season,
                   weeks=weeks,
                   week=week,
                   pool=pool,
                   entry=entry,
                   picks=entry.picks.fetch(1000))

        if entry.account.key() == self.request.account.key():
            template = 'pools/my_entry.html'
        else:
            template = 'pools/public_entry.html'
        return self.render(template, ctx)


class ManagePoolHandler(SecureRequestHandler):
    pass
