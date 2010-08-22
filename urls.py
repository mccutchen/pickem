import views

urls = [
    (r'/', views.pools.Index),

    (r'/pools', views.pools.Pools),
    (r'/pools/(\d+)', views.pools.Pool),
    (r'/pools/(\d+)/entries', views.pools.Entries),
    (r'/pools/(\d+)/entries/(\d+)', views.pools.Entry),
    (r'/pools/(\d+)/entries/(\d+)/picks', views.pools.Picks),
    (r'/pools/(\d+)/entries/(\d+)/picks/(\d+)', views.pools.Pick),
    (r'/pools/(\d+)/manage', views.pools.ManagePool),

    (r'/accounts/login', views.accounts.Login),
    (r'/accounts/(\d+)', views.accounts.Account),
    ]
