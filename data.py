from google.appengine.ext import db

class YahooOauthData(db.Model):

    google_user = db.UserProperty(required=True)
    access_token = db.TextProperty(required=False)
    access_secret = db.TextProperty(required=False)
    session_handle = db.TextProperty(required=False)
    yahoo_consumer_key = db.TextProperty(required=False)
    yahoo_consumer_secret = db.TextProperty(required=False)
    yahoo_oauth_refresh_date = db.DateTimeProperty()
