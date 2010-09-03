import datetime
from django.utils import simplejson as json

from google.appengine.ext import db
import models

scheduleData = json.load(open('data/schedule.json'))

fmt = '%Y-%m-%d %H:%M:%S'

def parsedate(s):
    d = datetime.datetime.strptime(s, fmt)
    return d + datetime.timedelta(hours=5) # convert to UTC

season_start = parsedate(scheduleData[0]['start']).date()
season_end = parsedate(scheduleData[-1]['end']).date()

season_key = '%s-%s' % (season_start.year, season_end.year)
season = models.Season.get_or_insert(
    season_key, start_date=season_start, end_date=season_end)
print season

weeks = []
games = []
for i, weekData in enumerate(scheduleData):
    week_num = i + 1
    week_key = db.Key.from_path('Week', week_num, parent=season.key())
    week = models.Week.get(week_key)
    if not week:
        week = models.Week(
            key=week_key,
            start=parsedate(weekData['start']),
            end=parsedate(weekData['end']),
            name='Week %i' % week_num)
        week.put()
    print week

    for gamedata in weekData['games']:
        home_key = gamedata['home'].keys()[0]
        away_key = gamedata['away'].keys()[0]
        home_team = models.Team.get_by_key_name(home_key)
        away_team = models.Team.get_by_key_name(away_key)
        assert home_team
        assert away_team
        game = db.Query(models.Game).ancestor(week)\
            .filter('home_team =', home_team)\
            .filter('away_team =', away_team)\
            .get()
        if not game:
            game = models.Game(
                parent=week,
                home_team=home_team,
                away_team=away_team,
                teams=[home_team.key(), away_team.key()],
                start=parsedate(gamedata['datetime']))
        games.append(game)
        print ' -', game

gamekeys = db.put(games)
