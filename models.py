import datetime
import logging

from google.appengine.ext import db


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

    def __str__(self):
        return unicode(self).encode('utf8', 'ignore')


class Team(db.Model):
    """A real life sports team, with a place and a name. The key name for a
    team should be its slug, the short identifier used to identify the team in
    score feeds (e.g., 'dal' for Dallas, 'mia' for Miami)."""
    place = db.StringProperty(required=True)
    name = db.StringProperty(required=True)

    def __unicode__(self):
        return u'%s %s' % (self.place, self.name)

    def __str__(self):
        return unicode(self).encode('utf8', 'ignore')


class Season(db.Model):
    """A single season for a given sports league."""
    start_date = db.DateProperty(required=True)
    end_date = db.DateProperty(required=True)

    @property
    def slates(self):
        return db.Query(Slate).ancestor(self).order('start')

    @property
    def name(self):
        return u'%d-%d Season' % (self.start_date.year,
                                  self.end_date.year % 1000)

    @classmethod
    def current(cls):
        if not hasattr(cls, '_current'):
            today = datetime.date.today()
            season = cls.all()\
                .filter('end_date >=', today)\
                .order('end_date')\
                .get()
            cls._current = season
        return cls._current

    def __unicode__(self):
        return self.name

    def __str__(self):
        return unicode(self).encode('utf8', 'ignore')


class Slate(db.Model):
    """A slate of games during a given season.  The games to pick are
    presented by slate.  In the NFL, this would be one week's games."""
    name = db.StringProperty() # E.g. Week 5
    start = db.DateTimeProperty()
    end = db.DateTimeProperty()

    @property
    def started(self):
        return datetime.datetime.now() > self.start

    @classmethod
    def next(cls):
        if not hasattr(cls, '_next'):
            season = Season.current()
            now = datetime.datetime.now()
            slate = season.slates.filter('start >', now).get()
            cls._next = slate
        return cls._next

    def __unicode__(self):
        return self.name

    def __str__(self):
        return unicode(self).encode('utf8', 'ignore')


class Game(db.Model):
    """A single game in a slate in a season, between a home Team and an away
    Team, with a point spread."""
    home_team = db.ReferenceProperty(Team, collection_name='home_games')
    away_team = db.ReferenceProperty(Team, collection_name='away_games')

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

    def __str__(self):
        return unicode(self).encode('utf8', 'ignore')


class Pool(db.Model):
    """A pick 'em pool, with a manager and a set of players and entries."""
    manager = db.ReferenceProperty(
        Account, required=True, collection_name='pools')
    name = db.StringProperty(required=True)
    description = db.StringProperty()

    # Is this pool invite only?
    invite_only = db.BooleanProperty(default=True)

    # How much does an entry cost?
    buy_in = db.FloatProperty(default=0.0)

    # Are games picked against the spread
    against_spread = db.BooleanProperty(default=False)

    # Which team are late picks stuck with?
    default_team = db.ReferenceProperty(Team, collection_name='default_pools')

    # Send updates to the manager?
    email_updates = db.BooleanProperty(default=True)

    @property
    def entries(self):
        return db.Query(Entry).ancestor(self)

    @property
    def active_entries(self):
        return self.entries.filter('active =', True)

    @property
    def paid_entries(self):
        return self.entries.filter('paid =', True)

    @property
    def unpaid_entries(self):
        return self.entries.filter('paid =', False)

    @property
    def pot(self):
        return self.buy_in * self.paid_entries.count()

    @property
    def potential_pot(self):
        return self.buy_in * self.entries.count()

    def is_member(self, account):
        """Does the given account have an entry in this pool?"""
        return self.entries.filter('account =', account).get() is not None

    def add_entry(self, account):
        """Adds an entry for the given account, if one does not already exist.
        Returns a boolean indicated whether a new entry was created."""
        def txn():
            entry = self.entries.filter('account =', account).get()
            if not entry:
                entry = Entry(account=account, parent=self)
                entry.put()
                return True
            else:
                return False
        return db.run_in_transaction(txn)

    def __unicode__(self):
        return self.name

    def __str__(self):
        return unicode(self).encode('utf8', 'ignore')


class Entry(db.Model):
    """A single user's entry into a given Pool."""
    account = db.ReferenceProperty(Account, collection_name='entries')

    # Is this entry still active (ie, has not lost)?
    active = db.BooleanProperty(default=True)

    # Has it been paid up?
    paid = db.BooleanProperty(default=False)

    def has_picked(self, slate):
        """Has a pick been made for the given slate?"""
        return self.picks.filter('slate =', slate).get() is not None

    def __unicode__(self):
        return unicode(self.account)

    def __str__(self):
        return unicode(self).encode('utf8', 'ignore')


class Pick(db.Model):
    """A single user's pick for a specific game."""
    entry = db.ReferenceProperty(Entry, collection_name='picks')
    slate = db.ReferenceProperty(Slate, collection_name='picks')
    game = db.ReferenceProperty(Game, collection_name='picks')
    team = db.ReferenceProperty(Team, collection_name='picks')
    correct = db.BooleanProperty()

    def evaluate(self, commit=True):
        """Evaluates this pick to determine if it's correct.  Returns True if
        so, False if not, or None if the game has not finished."""
        if self.game.finished:
            self.correct = self.game.is_winner(self.team)
            if commit:
                self.put()
            return self.correct
        else:
            return None

    def __unicode__(self):
        return unicode(self.team)

    def __str__(self):
        return unicode(self).encode('utf8', 'ignore')
