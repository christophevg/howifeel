import os
from flask import Flask, render_template, request, abort

template_dir = os.path.abspath("src/pages")
static_dir   = os.path.abspath("src/static")
app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
app.config["TEMPLATES_AUTO_RELOAD"] = True

import flask_restful
from flask_restful import Resource

api = flask_restful.Api(app)

from pymongo import MongoClient

DB       = os.environ.get("MONGODB_URI", "mongodb://localhost:27017/howifeel")
mongo    = MongoClient(DB)
database = DB.split("/")[-1]
if "?" in database: database = database.split("?")[0]
db       = mongo[database]

class User(object):
  def __init__(self, user, mood=None, followers=None):
    self.user       = user
    self._mood      = mood
    self._followers = [] if followers is None else followers
  
  @property
  def mood(self):
    return self._mood
  
  @mood.setter
  def mood(self, value):
    db.mood.update_one(
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
    db.mood.update_one(
      { "user"  : self.user },
      { "$push" : { "followers" : follower} },
      upsert=True
    )
    self._followers.append(follower)
    return follower

  def break_link(self, link):
    db.mood.update_one(
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
      return clazz(**info)
    return None

  @classmethod
  def followed_with_link(clazz, db, link):
    info = db.mood.find_one({ "followers.link" : link }, {"_id" : False})
    if info:
      return clazz(**info)
    return None

# TODO replace with logged on user

USER = User.find(db, "xtof")
if not USER:
  USER = User("xtof")

# UI Routes

@app.route("/")
def hello():
  return render_template("index.html")

@app.route("/mood")
def show_mood_management_page():
  return render_template("manage_mood.html", show_navigation=True)

@app.route("/followers")
def show_followers_management_page():
  return render_template("manage_followers.html", show_navigation=True)

@app.route("/mood/<link>")
def show_mood_view_page(link):
  user = User.followed_with_link(db, link)
  if user:
    return render_template("view_mood.html", user=user)
  return render_template("unknown_follower.html")

# API Resources

class Mood(Resource):
  def get(self):
    return USER.mood

  def post(self):
    USER.mood = request.get_json()["mood"]

api.add_resource(Mood, "/api/mood")

class Followers(Resource):
  def get(self):
    return USER.followers

  def post(self):
    if not USER.add_follower(**request.get_json()):
      abort(400, description="Invalid follower information")

api.add_resource(Followers, "/api/followers")

class Link(Resource):
  def delete(self, link):
    USER.break_link(link)

api.add_resource(Link, "/api/link/<link>")
