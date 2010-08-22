from ext.webapp2 import Route
import views

urls = [
    Route(r'/', views.pools.IndexHandler, 'index'),

    Route(r'/pools', views.pools.PoolsHandler, 'pools'),
    Route(r'/pools/<:\d+>', views.pools.PoolHandler, 'pool'),
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

    Route(r'/accounts/login', views.accounts.LoginHandler, 'login'),
    Route(r'/account', views.accounts.AccountHandler, 'account'),
    Route(r'/accounts/<:\d+>', views.accounts.ProfileHandler, 'profile'),
    ]
