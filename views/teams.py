import logging
import datetime
from itertools import groupby

from google.appengine.ext import db

from lib.webapp import RequestHandler
from lib.decorators import objects_required

import models
import forms


class TeamsHandler(RequestHandler):
    pass

class TeamHandler(RequestHandler):
    @objects_required('Team')
    def get(self, team):
        pass