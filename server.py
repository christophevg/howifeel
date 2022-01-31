import os
from flask import Flask, render_template, request

template_dir = os.path.abspath("src/pages")
static_dir   = os.path.abspath("src/static")
app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)

import flask_restful
from flask_restful import Resource

api = flask_restful.Api(app)

from pymongo import MongoClient

DB       = os.environ.get("MONGODB_URI", "mongodb://localhost:27017/howifeel")
mongo    = MongoClient(DB)
database = DB.split("/")[-1]
if "?" in database: database = database.split("?")[0]
db       = mongo[database]

@app.route("/")
def hello():
  return render_template('index.html')

@app.route("/mood")
def show_mood_page():
  return render_template('mood.html')

USER = "xtof"

class Mood(Resource):
  def get(self):
    try:
      return db.mood.find_one({"user" : USER}, { "_id" : False })["mood"]
    except TypeError:
      # no current mood recorded for user
      return None

  def post(self):
    mood = request.get_json()
    db.mood.update_one(
      { "user"   : USER },
      { "$set"   : { "mood" : mood["mood"] }},
      upsert=True
    )

api.add_resource(Mood, "/api/mood")
