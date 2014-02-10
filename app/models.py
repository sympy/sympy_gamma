from google.appengine.ext import ndb

class Query(ndb.Model):
    text = ndb.StringProperty()
    date = ndb.DateTimeProperty(auto_now_add=True)
    user_id = ndb.StringProperty()


