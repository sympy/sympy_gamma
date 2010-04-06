from google.appengine.ext import db

class Account(db.Model):

    user = db.UserProperty(auto_current_user_add=True, required=True)
    email = db.EmailProperty(required=True)
    nickname = db.StringProperty(required=True)

    created = db.DateTimeProperty(auto_now_add=True)
    modified = db.DateTimeProperty(auto_now=True)

    # Current user's Account. Updated by middleware.AddUserToRequestMiddleware.
    current_user_account = None

    show_prompts = db.BooleanProperty(default=False)
    join_nonempty_fields = db.BooleanProperty(default=True)

    @classmethod
    def get_account_for_user(cls, user):
        """Get the Account for a user, creating a default one if needed."""
        email = user.email()
        assert email
        id = user.user_id()
        assert id
        # the names must begging with a letter, so we add "K" at the beginning:
        key = "K" + str(id)
        account = cls.get_by_key_name(key)
        if account is not None:
            return account
        nickname = cls.create_nickname_for_user(user)
        return cls.get_or_insert(key, user=user, email=email,
                nickname=nickname, fresh=True)

    @classmethod
    def create_nickname_for_user(cls, user):
        """Returns a unique nickname for a user."""
        name = nickname = user.email().split('@', 1)[0]
        next_char = chr(ord(nickname[0].lower())+1)
        existing_nicks = [account.lower_nickname
                      for account in cls.gql(('WHERE lower_nickname >= :1 AND '
                                              'lower_nickname < :2'),
                                             nickname.lower(), next_char)]
        suffix = 0
        while nickname.lower() in existing_nicks:
            suffix += 1
            nickname = '%s%d' % (name, suffix)
        return nickname

class Worksheet(db.Model):

    session_token = db.StringProperty(required=True)

    @property
    def cells(self):
        return Cell.all().filter("worksheet =", self)

    def print_worksheet(self):
        s = "Worksheet: token=%s\n" % self.session_token
        for cell in self.cells:
            s += cell.print_cell() + "-"*40 + "\n"
        return s

    def get_cell_ids(self):
        ids = []
        for cell in self.cells:
            ids.append(cell.id)
        return ids

    def max_id(self):
        ids = self.get_cell_ids()
        if len(ids) == 0:
            return 0
        else:
            return max(ids)

class Cell(db.Model):

    worksheet = db.ReferenceProperty(Worksheet, required=True)
    id = db.IntegerProperty(required=True)
    input = db.StringProperty()
    output = db.StringProperty()

    def print_cell(self):
        return "Cell: id=%d\ninput: %s\noutput: %s\n" % (self.id,
                self.input, self.output)
