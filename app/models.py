from __future__ import absolute_import
import six
import os
# https://github.com/googleapis/python-ndb/issues/249#issuecomment-560957294
six.moves.reload_module(six)

from google.cloud import datastore


datastore_client = datastore.Client(project=os.environ['PROJECT_ID'])
