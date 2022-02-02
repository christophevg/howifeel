import logging
logger = logging.getLogger(__name__)

import uuid

from flask_login import current_user

from howifeel.data import db

def invite(who):
  invitation = {
    "invitation" : str(uuid.uuid4()),
    "invited"    : who, 
    "from"       : current_user.user
  }
  db.invitations.insert_one(invitation)
  del invitation["_id"]
  return invitation

def is_valid(invitation):
  return bool(db.invitations.find_one({"invitation" : invitation }))

def revoke(invitation):
  db.invitations.delete_one({"invitation" : invitation })
