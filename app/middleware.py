"""Custom middleware.  Some of this may be generally useful."""

from google.appengine.api import users

import models

class AddUserToRequestMiddleware(object):
  """Add a user object and a user_is_admin flag to each request."""

  def process_request(self, request):
    request.user = users.get_current_user()
    request.user_is_admin = users.is_current_user_admin()

    # Update the cached value of the current user's Account
    account = None
    if request.user is not None:
      account = models.Account.get_account_for_user(request.user)
    models.Account.current_user_account = account
