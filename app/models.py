import six
# https://github.com/googleapis/python-ndb/issues/249#issuecomment-560957294
six.moves.reload_module(six)

from google.cloud import ndb

ndb_client = ndb.Client(project='sympy-live-hrd')


class Query(ndb.Model):
    text = ndb.StringProperty()
    date = ndb.DateTimeProperty(auto_now_add=True)
    user_id = ndb.StringProperty()
