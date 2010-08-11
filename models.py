from google.appengine.ext import db


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
    home_team = db.ReferenceProperty(Team)
    away_team = db.ReferenceProperty(Team)

    home_score = db.IntegerProperty(default=0)
    away_score = db.IntegerProperty(default=0)

    # Spread will always be according to the home team
    spread = db.FloatProperty(default=0.0)

    kickoff = db.DateTimeProperty()
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
    name = db.StringProperty()
    description = db.StringProperty()

    # Are games picked against the spread
    with_spread = db.BooleanProperty(default=False)

    # Is there a hard deadline for picking games?
    hard_deadline = db.BooleanProperty(default=False)

    # What players are participating in this pool?  A list of account keys.
    players = db.ListProperty(db.Key)

    @property
    def entries(self):
        return db.Query(Entry).ancestor(self).filter('active =', True)

    @property
    def active_players(self):
        pass


class Account(db.Model):
    """A user's account."""
    email = db.EmailProperty(required=True)
    oauth_token = db.StringProperty(required=True)
    first_name = db.StringProperty()
    last_name = db.StringProperty()


class Entry(db.Model):
    """A single user's entry into a given Pool."""
    account = db.ReferenceProperty(Account, collection_name='entries')

    # Is this entry still active (ie, has not lost)?
    active = db.BooleanProperty(default=True)

    # Has it been paid up?
    paid = db.BooleanProperty(default=True)


class Pick(db.Model):
    """A single user's pick for a specific game."""
    game = db.ReferenceProperty(Game)
    team = db.ReferenceProperty(Team)
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
