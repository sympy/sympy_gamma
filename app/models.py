from google.appengine.ext import ndb

class Query(ndb.Model):
    text = ndb.StringProperty()
    date = ndb.DateTimeProperty(auto_now_add = True)
    user_id = ndb.StringProperty()

# this class can be used to store result in the databases.
# but that costs money. so i am avoiding it.:)

class Notebook(ndb.Model):
    result_json = ndb.JsonProperty(indexed = False)
    timestamp = ndb.DateTimeProperty(auto_now_add = True, indexed = True)
