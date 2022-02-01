import logging
logger = logging.getLogger(__name__)

from flask import request, abort

from flask_restful import Resource

from howifeel       import api
from howifeel.user  import current_user

# resource to get/set the mood of the currently logged on user

class Mood(Resource):
  def get(self):
    return current_user().mood

  def post(self):
    mood = request.get_json()["mood"]
    current_user().mood = mood
    logger.debug(f"set mood to {mood} for {current_user().user}")

api.add_resource(Mood, "/api/mood")

# resource to get followers or add a new one

class Followers(Resource):
  def get(self):
    return current_user().followers

  def post(self):
    follower = current_user().add_follower(**request.get_json())
    if not follower:
      abort(400, description="Invalid follower information")
    logger.debug(f"added follower {follower['name']} for {current_user().user}")

api.add_resource(Followers, "/api/followers")

# resource to break a link to follower

class Link(Resource):
  def delete(self, link):
    current_user().break_link(link)
    logger.debug(f"removed link: {link}")

api.add_resource(Link, "/api/link/<link>")
