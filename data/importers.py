import csv
import datetime
from itertools import groupby
from operator import itemgetter

from google.appengine.ext import db

from models import Team, Season, Week, Game



def import_schedule(season=None):

    # We want to convert from Eastern Time in the schedule to UTC
    import pytz
    est = pytz.timezone('US/Eastern')

    if not season:
        season = Season.current()

    # Make a map of all the teams. Map by both name and place because the
    # input data uses either one, sort of arbitrarily.
    teams = Team.all().fetch(32)
    team_map = dict((t.name, t) for t in teams)
    team_map.update(
        dict((t.place, t) for t in teams))

    # We'll build up the weeks and games we're importing in these structures.
    week_map = {}
    games = []

    csvlines = open('data/examples/2011-2012-schedule.csv').readlines()[1:]
    reader = csv.reader(csvlines)
    for row in reader:
        # Figure out kickoff
        kickoff = '%s %s' % itemgetter(0,7)(row)
        kickoff = datetime.datetime.strptime(kickoff, '%m/%d/%Y %I:%M %p')
        kickoff = est.localize(kickoff).astimezone(pytz.utc)

        # Look up home and away teams by team name in the team map
        team_names = [_.strip() for _ in row[-2:]]
        home, away = itemgetter(*team_names)(team_map)

        # Figure out what week this game belongs to. The data in the CSV is a
        # string like this:
        # 'NFL Week 8:    Chargers @ Chiefs          [TV: ESPN]'
        info = row[2]
        week_num = int(info.split()[2][:-1])

        if week_num not in week_map:
            key = db.Key.from_path('Week', week_num, parent=season.key())
            week_map[week_num] = Week(
                key=key,
                name = 'Week %s' % week_num)
        week = week_map[week_num]

        key_name = '%s@%s' % (away.slug, home.slug)

        game = dict(
            parent=week,
            key_name=key_name,
            home_team=home,
            away_team=away,
            teams=[home.key(), away.key()],
            start=kickoff)
        games.append(game)

    games.sort(key=itemgetter('parent'))

    # Figure out each week's end date based on the latest kickoff of its games
    for week, week_games in groupby(games, itemgetter('parent')):
        end = max(game['start'] for game in week_games)
        week.end = end + datetime.timedelta(hours=5)

    # Store the weeks, so they have "complete" keys, and can therefore be used
    # as the parents to the games we're about to create.
    week_keys = db.put(week_map.values())

    # Create actual game entities from the kwargs we gathered, and store them.
    games = [Game(**kwargs) for kwargs in games]
    game_keys = db.put(games)

    return week_keys + game_keys

