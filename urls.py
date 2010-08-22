import views

urls = [
    (r'/', views.Index),

    (r'/pools', views.Pools),
    (r'/pools/(\d+)', views.Pool),
    (r'/pools/(\d+)/entries', views.Entries),
    (r'/pools/(\d+)/entries/(\d+)', views.Entry),
    (r'/pools/(\d+)/entries/(\d+)/picks', views.Picks),
    (r'/pools/(\d+)/entries/(\d+)/picks/(\d+)', views.Pick),
    (r'/pools/(\d+)/manage', views.ManagePool),

    (r'/accounts/login', views.Login),
    (r'/accounts/(\d+)', views.Account),
    ]
