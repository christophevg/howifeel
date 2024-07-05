import bcrypt
import hashlib

from flask_login import UserMixin

from howifeel.data import db

class User(UserMixin):
  def __init__(self, user, mood=None, followers=None, following=None, password=None, profile=None):
    self.user       = user
    self._profile   = {} if profile is None else profile
    self._mood      = mood
    self._password  = password
    self._followers = [] if followers is None else followers
    self._following = [] if following is None else following
  
  def __str__(self):
    return self.user

  def __repr__(self):
    return self.__str__()

  @classmethod
  def find(clazz, user):
    info = db.users.find_one({"user" : user}, { "_id" : False })
    if info:
      return clazz(**info)
    return None
  
  def get_id(self):
    return self.user
  
  def validates(self, password):
    if not type(password) is bytes:
      password = str.encode(password)
    return bcrypt.checkpw(password, self._password) 

  def change_password(self, old_password, new_password):
    if self._password:
      assert self.validates(old_password)
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(str.encode(new_password), salt)
    db.users.update_one(
      { "user"   : self.user },
      { "$set"   : { "password" : hashed }},
      upsert=True
    )
    self._password = hashed

  @property
  def profile(self):
    return self._profile

  def update(self, update=None):
    if not update: return
    self._profile.update(update)
    db.users.update_one(
      { "user"   : self.user },
      { "$set"   : { "profile" : self._profile }},
      upsert=True
    )

  @property
  def gravatar(self):
    try:
      return hashlib.md5(str.encode(self._profile["email"].lower())).hexdigest()
    except KeyError:
      return ""

  @property
  def mood(self):
    return self._mood
  
  @mood.setter
  def mood(self, value):
    db.users.update_one(
      { "user"   : self.user },
      { "$set"   : { "mood" : value }},
      upsert=True
    )
    self._mood = value

  @property
  def followers(self):
    return list(self._followers)

  def add_follower(self, name, link):
    if not name or not link: return None
    follower = { "name" : name, "link" : link }
    db.users.update_one(
      { "user"  : self.user },
      { "$push" : { "followers" : follower} },
      upsert=True
    )
    self._followers.append(follower)
    return follower

  def break_link(self, link):
    db.users.update_one(
      { "user"  : self.user },
      { "$pull" : { "followers" : { "link" : link }} }
    )
    self._followers = [
      follower for follower in self._followers if follower["link"] != link
    ]

  @classmethod
  def followed_with_link(clazz, link):
    info = db.users.find_one({ "followers.link" : link }, {"_id" : False})
    if info:
      return clazz(**info)
    return None

  @property
  def invitations(self):
    return list(db.invitations.find({"from" : self.user }, {"_id" : False}))

  @property
  def following(self):
    return [ User(**user) for user in db.users.find(
      { "user" : { "$in" : self._following } },
      { "_id" : False, "password" : False }
    )]

  def follow(self, username):
    db.users.update_one(
      { "user" : self.user },
      { "$push" : { "following" : username} },
      upsert=True
    )
    self._following.append(username)

  def follows(self, user):
    return user.user in self._following

  def unfollow(self, username):
    db.users.update_one(
      { "user"  : self.user },
      { "$pull" : { "following" : username } }
    )
    self._following = [
      followed for followed in self._following if followed != username
    ]

  def to_json(self):
    return {
      "user"      : self.user,
      "profile"   : self._profile,
      "mood"      : self._mood,
      "gravatar"  : self.gravatar,
      "following" : self._following, # avoid nested user objects (recursion)
      "followers" : self._followers
    }
