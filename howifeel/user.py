import logging
logger = logging.getLogger(__name__)

class User(object):
  def __init__(self, user, db, mood=None, followers=None):
    self.user       = user
    self.db         = db
    self._mood      = mood
    self._followers = [] if followers is None else followers
  
  @property
  def mood(self):
    return self._mood
  
  @mood.setter
  def mood(self, value):
    self.db.mood.update_one(
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
    self.db.mood.update_one(
      { "user"  : self.user },
      { "$push" : { "followers" : follower} },
      upsert=True
    )
    self._followers.append(follower)
    return follower

  def break_link(self, link):
    self.db.mood.update_one(
      { "user"  : self.user },
      { "$pull" : { "followers" : { "link" : link }} }
    )
    self._followers = [
      follower for follower in self._followers if follower["link"] != link
    ]

  @classmethod
  def find(clazz, db, user):
    info = db.mood.find_one({"user" : user}, { "_id" : False })
    if info:
      return clazz(**info, db=db)
    return None

  @classmethod
  def followed_with_link(clazz, db, link):
    info = db.mood.find_one({ "followers.link" : link }, {"_id" : False})
    if info:
      return clazz(**info, db=db)
    return None

# TODO replace with logged on user

from howifeel.data import db

USER = User.find(db, "xtof")
if not USER:
  USER = User("xtof")

def current_user():
  return USER
