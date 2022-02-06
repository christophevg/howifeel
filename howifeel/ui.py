import logging
logger = logging.getLogger(__name__)

from urllib.parse import urlparse, urljoin

def is_safe_url(target):
  ref_url = urlparse(request.host_url)
  test_url = urlparse(urljoin(request.host_url, target))
  return test_url.scheme in ('http', 'https') and \
       ref_url.netloc == test_url.netloc

from flask import request, render_template, redirect, url_for, abort

from flask_login import current_user, login_required, login_user, logout_user

from howifeel             import app
from howifeel.user        import User
from howifeel.invitations import is_valid, revoke

def render(*args, **kwargs):
  return render_template(*args, **kwargs)

@app.errorhandler(404)
def page_not_found(e):
  return render_template("404.html"), 404

@app.route("/")
def index():
  return render("index.html")

@app.route("/signup", methods=["GET", "POST"])
@app.route("/signup/<invitation>", methods=["GET", "POST"])
def signup(invitation=None):
  if not invitation or not is_valid(invitation):
    return redirect(url_for("index"))
  if request.method == "GET":
    return render("signup.html", hide_header=True)
  else:
    username   = request.form.get("username")
    password   = request.form.get("password")
    password2  = request.form.get("password2")
    if username and password == password2:
      user = User(username)
      user.change_password(None, password)
      revoke(invitation)
      login_user(user)
      next = request.args.get("next")
      if not is_safe_url(next):
        return abort(400)
      return redirect(next or url_for("show_mood_management_page"))
    return render(
      "signup.html",
      hide_header=True,
      feedback="Invalid username and/or passwords do not match."
    )
    
@app.route("/login", methods=["GET", "POST"])
def show_login_page():
  if request.method == "GET":
    return render("login.html", hide_header=True)
  else:
    user     = User.find(request.form.get("username"))
    password = request.form.get("password")
    if user and user.validates(password):
      login_user(user)
      next = request.args.get("next")
      if not is_safe_url(next):
        return abort(400)
      return redirect(next or url_for("show_mood_management_page"))
    return render(
      "login.html",
      hide_header=True,
      feedback="Incorrect username and/or password."
    )

@app.get("/logout")
@login_required
def logout():
  logout_user()
  return redirect(url_for("index"))

@app.route("/me", methods=["GET", "POST"])
@login_required
def show_my_page():
  if request.method == "GET":
    return render("me.html")
  else:
    old_password = request.form.get("old_password")
    password     = request.form.get("password")
    password2    = request.form.get("password2")
    if current_user.validates(old_password) and password and password == password2:
      current_user.change_password(old_password, password)
      return render(
        "me.html",
        feedback="Password successfully updated.",
        style="success"
      )
    return render(
      "me.html",
      feedback="Old or new passwords do not match."
    )

@app.route("/mood")
@login_required
def show_mood_management_page():
  return render("manage_mood.html")

@app.route("/followers")
@login_required
def show_followers_management_page():
  return render("manage_followers.html")

@app.route("/following")
@login_required
def show_following_management_page():
  return render("manage_following.html")

@app.route("/mood/<link>")
def show_mood_view_page(link):
  user = User.followed_with_link(link)
  if user:
    return render("view_mood.html", user=user)
  logger.warn(f"unknown link requested: {link}")
  return render("unknown_follower.html")
