import logging
import datetime

from lib.webapp import RequestHandler
from lib.decorators import objects_required

import models
import forms


class SeasonHandler(RequestHandler):

    @objects_required('Season')
    def get(self, season):
        assert False, season


class WeekHandler(RequestHandler):

    @objects_required('Season', 'Week')
    def get(self, season, week):
        assert False, (season, week)
