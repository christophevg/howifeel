import logging
logger = logging.getLogger(__name__)

from urllib.parse import urlparse, urljoin

def is_safe_url(target):
  ref_url = urlparse(request.host_url)
  test_url = urlparse(urljoin(request.host_url, target))
  return test_url.scheme in ('http', 'https') and \
       ref_url.netloc == test_url.netloc

from flask import request, render_template, redirect, url_for, abort

from flask_login import login_required, login_user, logout_user

from howifeel      import app
from howifeel.user import User

@app.route("/")
def index():
  return render_template("index.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
  if request.method == "GET":
    return render_template("signup.html", hide_header=True)
  else:
    username  = request.form.get("username")
    password  = request.form.get("password")
    password2 = request.form.get("password2")
    if username and password == password2:
      user = User(username)
      user.change_password(None, password)
      login_user(user)
      next = request.args.get("next")
      if not is_safe_url(next):
        return abort(400)
      return redirect(next or url_for("show_mood_management_page"))
    return render_template(
      "signup.html",
      hide_header=True,
      feedback="Invalid username and/or passwords do not match."
    )
    
@app.route("/login", methods=["GET", "POST"])
def show_login_page():
  if request.method == "GET":
    return render_template("login.html", hide_header=True)
  else:
    user = User.find(request.form.get("username"))
    password = str.encode(request.form.get("password"))
    if user and user.validates(password):
      login_user(user)
      next = request.args.get("next")
      if not is_safe_url(next):
        return abort(400)
      return redirect(next or url_for("show_mood_management_page"))
    return render_template(
      "login.html",
      hide_header=True,
      feedback="Incorrect username and/or password."
    )

@app.get("/logout")
@login_required
def logout():
  logout_user()
  return redirect(url_for("index"))

@app.route("/mood")
@login_required
def show_mood_management_page():
  return render_template("manage_mood.html")

@app.route("/followers")
@login_required
def show_followers_management_page():
  return render_template("manage_followers.html")

@app.route("/mood/<link>")
def show_mood_view_page(link):
  user = User.followed_with_link(link)
  if user:
    return render_template("view_mood.html", user=user)
  logger.warn(f"unknown link requested: {link}")
  return render_template("unknown_follower.html")
