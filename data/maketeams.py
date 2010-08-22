import simplejson as json
import env

from google.appengine.ext import db
import models

teamsData = json.load(open('data/teams.json'))

teams = []
for team in teamsData:
    key = db.Key.from_path('Team', team['slug'])
    teams.append(models.Team(key=key, name=team['name'], place=team['place']))
    print unicode(team)

keys = db.put(teams)
print keys
    