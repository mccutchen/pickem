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
        picks = week.picks.fetch(1000) if week.closed else []

        invite_url = self.url_for(
            'join-pool', pool.key().id(), pool.invite_code, _full=True)
        ctx = dict(pool=pool,
                   entries=entries,
                   active_entries=active_entries,
                   unpaid_entries=unpaid_entries,
                   season=week.parent(),
                   week=week,
                   picks=picks,
                   invite_url=invite_url)
        return self.render('pools/pool.html', ctx)


class JoinHandler(RequestHandler):
    pass


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
            template = 'pools/entry.html'
        else:
            template = 'pools/public_entry.html'
        return self.render(template, ctx)


class PicksHandler(SecureRequestHandler):
    pass


class PickHandler(SecureRequestHandler):

    @objects_required('Pool', 'Entry')
    def get(self, pool, entry, week_num):
        season = models.Season.current()
        week = self.get_week(week_num, season=season)
        pick_key = db.Key.from_path(
            'Pick', week.key().id(), parent=entry.key())
        pick = db.get(pick_key)
        weeks = season.weeks.fetch(25)
        ctx = dict(season=season,
                   weeks=weeks,
                   week=week,
                   pool=pool,
                   entry=entry,
                   pick=pick,
                   picks=entry.picks.fetch(1000))

        if entry.account.key() == self.request.account.key():
            template = 'pools/pick.html'
        else:
            template = 'pools/public_entry.html'
        return self.render(template, ctx)

    @objects_required('Pool', 'Entry')
    def post(self, pool, entry, week_num):
        week = self.get_week(week_num)
        team_slug = self.request.POST.get('pick')
        if team_slug is None:
            raise HTTPBadRequest('Pick required')
        team = models.Team.get_by_key_name(team_slug)
        if team is None:
            raise HTTPBadRequest('Unknown team: %s' % team_slug)
        game = week.find_game_for(team)
        if game is None:
            raise HTTPBadRequest('No game for %s in week %s' % (team, week))

        # We should have enough data to create the pick (in a transaction)
        pick_key = db.Key.from_path(
            'Pick', week.key().id(), parent=entry.key())
        def txn():
            pick = db.get(pick_key)
            if pick is None:
                pick = models.Pick(
                    key=pick_key,
                    week=week,
                    game=game,
                    team=team)
                pick.put()
            return pick
        pick = db.run_in_transaction(txn)

        url = self.url_for(
            'pick', pool.key().id(), entry.key().id(), week_num)
        return self.redirect_to(url)

    def get_week(self, week_num, season=None):
        season = season or models.Season.current()
        week_key = db.Key.from_path(
            'Week', int(week_num), parent=season.key())
        week = db.get(week_key)
        if week is None:
            raise HTTPNotFound('Week %s not found' % week_num)
        return week


class ManagePoolHandler(SecureRequestHandler):
    pass
