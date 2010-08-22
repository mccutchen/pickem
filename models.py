from google.appengine.ext import db


class Account(db.Model):
    """A user's account."""
    email = db.EmailProperty(required=True)
    first_name = db.StringProperty()
    last_name = db.StringProperty()
    oauth_token = db.StringProperty()

    def __unicode__(self):
        return unicode(self.email)


class Team(db.Model):
    """A real life sports team, with a place and a name and a slug (the short
    string used to identify the team in score feeds)."""
    place = db.StringProperty()
    name = db.StringProperty()
    slug = db.StringProperty()


class Season(db.Model):
    """A single season for a given sports league."""
    name = db.StringProperty() # E.g. 2010-11 Season
    start_date = db.DateProperty()
    end_date = db.DateProperty()


class Slate(db.Model):
    """A slate of games during a given season.  The games to pick are
    presented by slate.  In the NFL, this would be one week's games."""
    name = db.StringProperty() # E.g. Week 5
    start = db.DateTimeProperty()
    end = db.DateTimeProperty()


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

    def is_winner(self, team, with_spread):
        """Returns True if the given team won or tied the game. Takes the
        point spread into account if with_spread is True. NOTE: Assumes that
        the game is over."""
        winner = self.get_winner(with_spread)
        return winner in (team, None)

    def get_winner(self, with_spread):
        """Determines the winner of the game, taking the point spread into
        account if with_spread is True. Returns the winning team, or None in
        the case of a tie. NOTE: Assumes that the game is over."""
        diff = self.home_score - self.away_score
        if with_spread:
            diff += self.spread
        if diff > 0:
            return self.home_team
        elif diff < 0:
            return self.away_team
        else:
            return None


class Pool(db.Model):
    """A pick 'em pool, with a manager and a set of players and entries."""
    manager = db.ReferenceProperty(
        Account, required=True, collection_name='pools')
    name = db.StringProperty(required=True)
    description = db.StringProperty()

    # How much does an entry cost?
    buy_in = db.FloatProperty(default=0.0)

    # Are games picked against the spread
    with_spread = db.BooleanProperty(default=False)

    # Is there a hard deadline for picking games?
    hard_deadline = db.BooleanProperty(default=False)

    @property
    def entries(self):
        return db.Query(Entry).ancestor(self)

    @property
    def active_entries(self):
        return self.entries.filter('active =', True)

    @property
    def active_players(self):
        pass

    @property
    def pot(self):
        return self.buy_in * self.entries.count()


class Entry(db.Model):
    """A single user's entry into a given Pool."""
    account = db.ReferenceProperty(Account, collection_name='entries')

    # Is this entry still active (ie, has not lost)?
    active = db.BooleanProperty(default=True)

    # Has it been paid up?
    paid = db.BooleanProperty(default=True)


class Pick(db.Model):
    """A single user's pick for a specific game."""
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
