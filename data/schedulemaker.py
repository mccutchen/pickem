import datetime
from itertools import groupby
import re

import simplejson as json
from BeautifulSoup import BeautifulSoup


def parse_team(teamData):
    assert teamData.name == 'a'
    abbrev = re.search('/name/([a-z]+)/', teamData['href']).group(1)
    name = teamData.string
    return { abbrev: name }

data = open('schedule.html').read()
soup = BeautifulSoup(data)

# A list of "weeks" dicts
sched = []

for weekData in soup.findAll('table', 'tablehead'):
    week = {}

    nameData = weekData.find('tr', 'stathead')
    week['name'] = nameData.find('td').contents[1].strip()

    week['games'] = []
    for row in nameData.findNextSiblings('tr'):

        if row['class'] == 'colhead':
            date = row.find('td').string
            date = datetime.datetime.strptime(date, '%a, %b %d')
            date = date.replace(year=2010 if date.month > 1 else 2011)

        else:
            try:
                teamsData,  timeData = row.findAll('td', limit=2)
            except ValueError:
                # Bye week
                pass
            else:
                awayData, homeData = teamsData.findAll('a')
                away = parse_team(awayData)
                home = parse_team(homeData)

                time = datetime.datetime.strptime(timeData.string, '%I:%M %p')
                gametime = time.replace(
                    year=date.year, month=date.month, day=date.day)

                game = { 'home': home,
                         'away': away,
                         'datetime': str(gametime) }
                week['games'].append(game)

    week['start'] = week['games'][0]['datetime']
    week['end'] = week['games'][-1]['datetime']
    sched.append(week)

print json.dumps(sched, indent=2)
