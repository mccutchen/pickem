import datetime
import hashlib
import logging
from itertools import groupby

from google.appengine.ext import db

from lib.caching import cachemodel, uncachemodel


class Account(db.Model):
    """A user's account."""
    email = db.EmailProperty(required=True)
    first_name = db.StringProperty()
    last_name = db.StringProperty()
    oauth_token = db.StringProperty()

    @property
    def name(self):
        return u'%s %s' % (self.first_name, self.last_name)

    def __unicode__(self):
       return self.name


class Team(db.Model):
    """A real life sports team, with a place and a name. The key name for a
    team should be its slug, the short identifier used to identify the team in
    score feeds (e.g., 'dal' for Dallas, 'mia' for Miami)."""
    place = db.StringProperty(required=True)
    name = db.StringProperty(required=True)

    @property
    def slug(self):
        return self.key().name()

    @classmethod
    def all_teams(cls):
        teams = uncachemodel('teams', namespace='teams')
        if not teams:
            teams = cls.all().fetch(32)
            cachemodel('teams', teams, namespace='teams')
        return teams

    def __unicode__(self):
        return u'%s %s' % (self.place, self.name)

    def __eq__(self, other):
        return isinstance(other, Team) and other.key() == self.key()


class Season(db.Model):
    """A single season.  The key name should be a string containing the start
    year and end year separated by a dash (e.g. '2010-2011')."""
    start_date = db.DateProperty(required=True)

    @property
    def weeks(self):
        return db.Query(Week).ancestor(self).order('end')

    @property
    def pools(self):
        return db.Query(Pool).ancestor(self).order('created_at')

    @property
    def name(self):
        return u'%s Season' % self.key().name()

    @classmethod
    def current(cls):
        if not hasattr(cls, '_current'):
            season = cls.all().order('-start_date').get()
            cls._current = season
        return cls._current

    def __unicode__(self):
        return self.name


class Week(db.Model):
    """A week of games during a given season. Parent should be a Season. Key
    should be the week's ordinal number in that season.
    """
    name = db.StringProperty() # E.g. Week 5
    end = db.DateTimeProperty()

    @property
    def games(self):
        return db.Query(Game).ancestor(self).order('start')

    @property
    def grouped_games(self):
        # Game times are stored as UTC, need to be offset back to EST or the
        # night games overflow into the next day.
        offset = datetime.timedelta(hours=-5)
        grouper = lambda g: (g.start + offset).date()
        return groupby(self.games.fetch(25), grouper)

    @property
    def closed(self):
        return datetime.datetime.now() > self.start

    def find_game_for(self, team):
        return self.games.filter('teams =', team.key()).get()

    @classmethod
    def next_week(cls):
        if not hasattr(cls, '_next_week'):
            season = Season.current()
            if season:
                now = datetime.datetime.now()
                weeks = season.weeks\
                    .filter('end >=', now)\
                    .order('end')\
                    .fetch(1, offset=1)
                week = weeks[0] if weeks else None
                cls._next_week = week
            else:
                cls._next_week = None
        return cls._next_week

    @classmethod
    def current_week(cls):
        if not hasattr(cls, '_current_week'):
            season = Season.current()
            now = datetime.datetime.now()
            week = season.weeks.filter('end >=', now).order('end').get()
            cls._current_week = week
        return cls._current_week

    def __unicode__(self):
        return self.name


class Game(db.Model):
    """A single game in a week in a season, between a home Team and an away
    Team, with a point spread.

    Constraints:

     - Parent: Week
     - Key:    '{away_team.slug}@{home_team.slug}'
    """
    home_team = db.ReferenceProperty(Team, collection_name='home_games')
    away_team = db.ReferenceProperty(Team, collection_name='away_games')

    # Also store the teams' keys in a list, so we can query for which game in
    # a week features a given team.
    teams = db.ListProperty(db.Key)

    home_score = db.IntegerProperty(default=0)
    away_score = db.IntegerProperty(default=0)

    # Spread will always be according to the home team
    spread = db.FloatProperty(default=0.0)

    start = db.DateTimeProperty()
    final = db.BooleanProperty(default=False)

    updated_at = db.DateTimeProperty(auto_now=True)

    def is_winner(self, team, against_spread):
        """Returns True if the given team won or tied the game. Takes the
        point spread into account if against_spread is True. NOTE: Assumes
        that the game is over."""
        winner = self.get_winner(against_spread)
        return winner in (team, None)

    def get_winner(self, against_spread):
        """Determines the winner of the game, taking the point spread into
        account if against_spread is True. Returns the winning team, or None
        in the case of a tie. NOTE: Assumes that the game is over."""
        diff = self.home_score - self.away_score
        if against_spread:
            diff += self.spread
        if diff > 0:
            return self.home_team
        elif diff < 0:
            return self.away_team
        else:
            return None

    def __unicode__(self):
        return '%s at %s' % (self.away_team, self.home_team)


class Pool(db.Model):
    """A pick 'em pool, with a manager and a set of players and entries."""
    manager = db.ReferenceProperty(
        Account, required=True, collection_name='pools')
    name = db.StringProperty(required=True)
    description = db.TextProperty()

    # When does this pool start?
    start_week = db.ReferenceProperty(Week, collection_name='starting_pools')

    # Is this pool invite only?
    invite_only = db.BooleanProperty(default=True)

    # How much does an entry cost?
    entry_fee = db.FloatProperty(default=0.0)

    # Are games picked against the spread
    against_spread = db.BooleanProperty(default=False)

    # Which team are late picks stuck with?
    default_team = db.ReferenceProperty(Team, collection_name='default_pools')

    # Send updates to the manager?
    email_updates = db.BooleanProperty(default=True)

    created_at = db.DateTimeProperty(auto_now_add=True)
    updated_at = db.DateTimeProperty(auto_now=True)

    @property
    def entries(self):
        return db.Query(Entry).ancestor(self)

    @property
    def active_entries(self):
        return self.entries.filter('active =', True)

    @property
    def inactive_entries(self):
        return self.entries.filter('active =', False)

    @property
    def paid_entries(self):
        return self.entries.filter('paid =', True)

    @property
    def unpaid_entries(self):
        return self.entries.filter('paid =', False)

    @property
    def pot(self):
        return self.entry_fee * self.paid_entries.count()

    @property
    def potential_pot(self):
        return self.entry_fee * self.entries.count()

    @property
    def open(self):
        return not self.week.closed

    @property
    def invite_code(self):
        if self.invite_only:
            s = '%s:%s' % (self.key(), self.created_at)
            return hashlib.sha1(s).hexdigest()
        else:
            return 'public'

    def check_invite_code(self, code):
        from lib.webapp import time_independent_equals
        return time_independent_equals(self.invite_code, code)

    def find_entry_for(self, account):
        """Find an entry in this pool for the given account, if there is
        one."""
        return self.entries.filter('account =', account).get()

    def is_member(self, account):
        """Does the given account have an entry in this pool?"""
        return self.find_entry_for(account) is not None

    def add_entry(self, account):
        """Adds an entry for the given account, if one does not already exist.
        Returns a boolean indicated whether a new entry was created."""
        def txn():
            entry = self.entries.filter('account =', account).get()
            if not entry:
                entry = Entry(account=account, parent=self)
                entry.put()
                created = True
            else:
                created = False
            return entry, created
        return db.run_in_transaction(txn)

    def __unicode__(self):
        return self.name


class Entry(db.Model):
    """A single user's entry into a given Pool."""
    account = db.ReferenceProperty(Account, collection_name='entries')

    # Is this entry still active (ie, has not lost)?
    active = db.BooleanProperty(default=True)

    # Has it been paid up?
    paid = db.BooleanProperty(default=False)

    @property
    def picks(self):
        return db.Query(Pick).ancestor(self)

    def find_pick_for(self, week):
        """Find this entry's pick for the given week."""
        return self.picks.filter('week =', week).get()

    def has_picked(self, week):
        """Has a pick been made for the given week?"""
        return self.find_pick_for(week) is not None

    def __unicode__(self):
        return unicode(self.account)


class Pick(db.Model):
    """A single user's pick for a specific game. Should have an entry as its
    parent."""
    week = db.ReferenceProperty(Week, collection_name='picks')
    game = db.ReferenceProperty(Game, collection_name='picks')
    team = db.ReferenceProperty(Team, collection_name='picks')
    correct = db.BooleanProperty()

    def evaluate(self, commit=True):
        """Evaluates this pick to determine if it's correct.  Returns True if
        so, False if not, or None if the game has not finished."""
        if self.game.final:
            self.correct = self.game.is_winner(self.team)
            if commit:
                self.put()
            return self.correct
        else:
            return None

    def __unicode__(self):
        return unicode(self.team)
