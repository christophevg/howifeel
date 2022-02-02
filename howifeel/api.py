import logging
logger = logging.getLogger(__name__)

from functools import wraps

from flask import request, abort

from flask_login import current_user

from flask_restful import Resource

from howifeel import app, api
from howifeel.invitations import invite, revoke

# decorator to check if current_user is logged in

def authenticate(func):
  @wraps(func)
  def wrapper(*args, **kwargs):
    if not current_user.is_anonymous:
      return func(*args, **kwargs)
    abort(401)
  return wrapper

# resource to get/set the mood of the currently logged on user

class Mood(Resource):
  method_decorators = [authenticate]
  def get(self):
    return current_user.mood

  def post(self):
    mood = request.get_json()["mood"]
    current_user.mood = mood
    logger.debug(f"set mood to {mood} for {current_user.user}")

api.add_resource(Mood, "/api/mood")

# resource to get followers or add a new one

class Followers(Resource):
  method_decorators = [authenticate]
  def get(self):
    return current_user.followers

  def post(self):
    follower = current_user.add_follower(**request.get_json())
    if not follower:
      abort(400, description="Invalid follower information")
    logger.debug(f"added follower {follower['name']} for {current_user.user}")

api.add_resource(Followers, "/api/followers")

# resource to break a link to follower

class Link(Resource):
  method_decorators = [authenticate]
  def delete(self, link):
    current_user.break_link(link)
    logger.debug(f"removed link: {link}")

api.add_resource(Link, "/api/link/<link>")

# resource to get followers or add a new one

class Invitations(Resource):
  method_decorators = [authenticate]
  def get(self):
    return current_user.invitations

  def post(self):
    invited = request.get_json()["invited"]
    invitation = invite(invited)
    logger.debug(f"invited {invited} for {current_user.user}")
    return invitation

api.add_resource(Invitations, "/api/invitations")

# resource to break a link to follower

class Invitation(Resource):
  method_decorators = [authenticate]
  def delete(self, invitation):
    revoke(invitation)
    logger.debug(f"revoked invitation: {invitation}")

api.add_resource(Invitation, "/api/invitation/<invitation>")
