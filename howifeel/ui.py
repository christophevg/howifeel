import logging
logger = logging.getLogger(__name__)

from flask import render_template

from howifeel      import app
from howifeel.data import db
from howifeel.user import User

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
  logger.warn(f"unknown link requested: {link}")
  return render_template("unknown_follower.html")
