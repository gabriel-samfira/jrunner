from .connection import *
import jrunner.common.utils as util
import json
import crypt
import datetime


class User(object):
    user_index = "jrunner:users:index"
    user_redis = "jrunner:user:%s"

    user_data = {
        'passwd': None,
        'first_name': None,
        'last_name': None,
        'email': None,
        'active': True,
        'admin': False,
    }

    def __init__(self, user):
        self.user = user
        self.user_redis = self.user_redis % str(self.user)

        self.userObj = db.get(self.user_redis)
        if self.userObj is None:
            raise ValueError("No such user")
        try:
            self.userObj = json.loads(self.userObj)
        except:
            raise Exception("Invalid user data")

    def __getattr__(self, name):
        if 'userObj' not in self.__dict__:
            raise AttributeError()
        if name not in self.userObj:
            raise AttributeError()
        return self.userObj[name]

    def __setattr__(self, name, value):
        if 'userObj' not in self.__dict__:
            return dict.__setattr__(self, name, value)
        if name in self.userObj:
            self.userObj[name] = value
        elif name in self.user_data:
            self.userObj[name] = value
        elif name in ('active', 'admin',):
            if value is not True and value is not False:
                raise ValueError("%r is not a boolean value" % value)
        else:
            object.__setattr__(self, name, value)

    @classmethod
    def get(cls, user):
        return cls(user)

    @classmethod
    def create(cls, username, passwd, **kw):
        user = cls.user_redis % username
        if db.get(user):
            raise ValueError("Username already exists")

        if len(passwd) == 0:
            raise ValueError("No zero length passwords allowed")

        salt = util.GenRand()
        enc_passwd = crypt.crypt(passwd, "$6$%s" % salt)
        user_data = cls.user_data
        user_data.update({"passwd": enc_passwd})
        user_data.update(kw)
        db.set(user, json.dumps(user_data))
        db.sadd(cls.user_index, username)
        return cls(username)

    def authenticate(self, passwd):
        is_enabled = self.userObj.get('is_enabled', True)
        if is_enabled is False:
            return False

        enc_passwd = self.userObj.get('passwd')
        if enc_passwd is None:
            raise ValueError("Access denied")
        try:
            salt = '$'.join(enc_passwd.split('$')[0:3])
        except:
            raise ValueError("Invalid password hash")
        passwd_hash = crypt.crypt(passwd, salt)
        if passwd_hash != enc_passwd:
            return False
        return True

    def set_password(self, passwd):
        salt = util.GenRand()
        enc_passwd = crypt.crypt(passwd, "$6$%s" % salt)
        self.userObj['passwd'] = enc_passwd
        self.save()

    def delete(self):
        # Not sure if we should allow user deletion. Just disabling shoudl do
        Token.purge_user_tokens(self)
        db.delete(self.user_redis)
        db.srem(self.user_index, self.user)
        return True

    def save(self):
        db.set(self.user_redis, json.dumps(self.userObj))
        return True


class TokenValidator(object):

    def __init__(self):
        self.required_fields = ('user',)
        self.allowed_fields = {
            'user': User,
            'max_uses': int,
            'expires': datetime.datetime,
        }

    def validate(self, data):
        ret = {}
        for i in self.required_fields:
            if i not in data:
                raise ValueError("Invalid token data")
        for i in data.keys():
            if i not in self.allowed_fields:
                raise ValueError("Invalid token data")
            if (isinstance(data[i], self.allowed_fields[i]) is False and
                    data[i] is not None):
                raise ValueError(
                    "%s must be of type %r" % (i, self.allowed_fields[i]))
            if i == "user":
                ret[i] = data[i].user
            elif i == "expires" and data[i] is not None:
                ret[i] = int(data[i].strftime('%s'))
            else:
                ret[i] = data[i]
        return ret

    def load(self, data):
        for i in data.keys():
            if i == "user":
                data[i] = User.get(data[i])
            if i == "expires" and data[i] is not None:
                data[i] = datetime.datetime.fromtimestamp(float(data[i]))
        return data


class Token(object):

    token_schema = {
        "expires": None,
        "max_uses": None,
        "user": None,
    }

    user_tokens = "jrunner:user:%s:tokens"
    token_name = "jrunner:tokens:%s"
    required = ("user",)

    def __init__(self, user, token):
        self.user = user
        if isinstance(self.user, User) is False:
            raise ValueError("Invalid user object")

        self.token = token
        self.user_tokens = self.user_tokens % self.user.user
        self.token_name = self.token_name % str(token)
        self.has_token = db.sismember(self.user_tokens, self.token)
        if self.has_token is False:
            raise ValueError("This token does not belong to this user")
        self.token_data = self.get_token_data()

    @classmethod
    def purge_user_tokens(cls, user):
        user_tokens = cls.user_tokens % user.user
        for i in db.smembers(user_tokens):
            try:
                db.delete(cls.token_name % i)
            except:
                pass
        db.delete(user_tokens)
        return True

    @classmethod
    def authenticate(cls, token):
        token_name = cls.token_name % token
        tk = db.get(token_name)
        if tk is None:
            raise ValueError("No such token")
        try:
            tk = json.loads(tk)
            token_data = TokenValidator().load(tk)
        except:
            raise Exception("Invalid token")
        token_class = cls(token_data['user'], token)
        if token_class.is_valid() is False:
            raise ValueError("This token is invalid")
        try:
            token_class.use()
        except Exception as err:
            log.exception(err)
        return token_data['user']

    @classmethod
    def list(cls, user):
        if isinstance(user, User) is False:
            raise ValueError("Invalid user")
        user_tokens = cls.user_tokens % user.user
        return [x for x in db.smembers(user_tokens)]

    @classmethod
    def get(cls, user, token):
        if isinstance(user, User) is False:
            raise ValueError("Invalid User object")
        token_name = cls.token_name % token
        tk = db.get(token_name)
        if tk is None:
            raise ValueError("No such token")
        tk = json.loads(tk)
        if tk:
            username = tk['user']
            if str(user.user) != str(username):
                raise ValueError("Token does not belong to user")
            return cls(user, token=token)
        raise ValueError("No such token")

    @classmethod
    def create(cls, **kw):
        """
        Create new token for current user.

          Params:
              expires  - datetime.datetime object. Token is invalid after
              max_uses - number of authentications allowed
        """
        for i in cls.required:
            if i not in kw:
                raise ValueError("Missing required field: %s" % i)

        user = kw['user']
        if isinstance(user, User) is False:
            raise ValueError("Invalid User object")

        validated = TokenValidator().validate(kw)
        cls.token_schema.update(validated)

        user_tokens = cls.user_tokens % user.user
        rand = util.GenRand(62)
        token = rand
        token_name = cls.token_name % rand
        db.sadd(user_tokens, token)
        db.set(token_name, json.dumps(cls.token_schema))
        return cls(user, token=rand)

    def get_token_data(self):
        """
        Get token data. If no token data is found, we return defaults
        """
        token = db.get(self.token_name)
        if token:
            data = json.loads(token)
            return TokenValidator().load(data)
        raise ValueError("Token is invalid")

    def is_valid(self):
        if self.token is None:
            raise ValueError("No token specified")
        token_data = self.get_token_data()
        if token_data['expires'] is not None:
            if token_data['expires'] < datetime.datetime.now():
                return False
        if token_data['max_uses'] is not None:
            if token_data['max_uses'] <= 0:
                return False
        return True

    def save(self):
        data = TokenValidator().validate(self.token_data)
        db.set(self.token_name, json.dumps(data))
        return True

    def use(self):
        if self.is_valid():
            if self.token_data['max_uses'] is not None:
                self.token_data['max_uses'] -= 1
            self.save()
            return True
        raise ValueError("Token is invalid")

    def delete(self):
        db.delete(self.token_name)
        db.srem(self.user_tokens, self.token)
        return True
