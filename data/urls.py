from ext.webapp2 import Route
import views

urls = [
    Route(r'/data/odds', views.OddsHandler, 'odds'),
    ]
