import logging
import datetime
from itertools import groupby

from google.appengine.ext import db

from lib.webapp import RequestHandler
from lib.decorators import objects_required

import models
import forms


class SeasonHandler(RequestHandler):

    @objects_required('Season')
    def get(self, season):
        weeks = season.weeks.fetch(25)
        pool_count = season.pools.count()
        entry_count = db.Query(models.Entry).ancestor(season).count()
        ctx = dict(season=season,
                   weeks=weeks,
                   pool_count=pool_count,
                   entry_count=entry_count)
        return self.render('seasons/season.html', ctx)


class WeekHandler(RequestHandler):

    @objects_required('Season', 'Week')
    def get(self, season, week):
        games = groupby(week.games.fetch(25), lambda g: g.start.date())
        ctx = dict(season=season,
                   week=week,
                   games=games)
        return self.render('seasons/week.html', ctx)
