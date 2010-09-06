from ext.webapp2 import Route
import views

urls = [
    Route(r'/', views.pools.IndexHandler, 'index'),

    Route(r'/pools', views.pools.PoolsHandler, 'pools'),
    Route(r'/pools/<:\d+>', views.pools.PoolHandler, 'pool'),
    Route(r'/pools/<:\d+>/join/<:\w+>', views.pools.JoinHandler, 'join-pool'),
    Route(r'/pools/<:\d+>/entries', views.pools.EntriesHandler, 'entries'),
    Route(r'/pools/<:\d+>/entries/<:\d+>', views.pools.EntryHandler, 'entry'),
    Route(r'/pools/<:\d+>/entries/<:\d+>/picks',
          views.pools.PicksHandler,
          'picks'),
    Route(r'/pools/<:\d+>/entries/<:\d+>/picks/<:\d+>',
          views.pools.PickHandler,
          'pick'),

    Route(r'/pools/<:\d+>/manage',
          views.pools.ManagePoolHandler,
          'manage-pool'),

    Route(r'/accounts/logout', views.accounts.LogoutHandler, 'logout'),
    Route(r'/accounts/login', views.accounts.LoginHandler, 'login'),
    Route(r'/accounts/login/facebook',
          views.accounts.FacebookLoginHandler,
          'facebook-login'),

    Route(r'/account', views.accounts.AccountHandler, 'account'),
    Route(r'/accounts/<:\d+>', views.accounts.ProfileHandler, 'profile'),

    Route(r'/seasons/<:\d+-\d+>', views.seasons.SeasonHandler, 'season'),
    Route(r'/seasons/<:\d+-\d+>/weeks/<:\d+>',
          views.seasons.WeekHandler,
          'week'),

    Route(r'/teams/', views.teams.TeamsHandler, 'teams'),
    Route(r'/teams/<:\w+>', views.teams.TeamHandler, 'team'),
    ]
