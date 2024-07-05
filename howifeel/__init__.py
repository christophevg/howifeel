__version__ = "0.0.4"

# needed explicitly for recursion issue in eventlet+ssl on outgoing pymongo
# and to be able to create single pymongo Database object
# problem only appears on render.com setup
import eventlet
eventlet.monkey_patch()

# load the environment variables for this setup from .env file
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv(usecwd=True))

import howifeel.setup

import pathlib
PATH = pathlib.Path(__file__).parent.resolve()

import os

from flask import Flask

app = Flask(__name__,
  template_folder = PATH / "pages",
  static_folder   = PATH / "static"
)
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["SECRET_KEY"] = os.environ.get("APP_SECRET_KEY", default="local")

import flask_restful

api = flask_restful.Api(app)

# setup a custom json encoder for objects that have a to_json() method
from json import JSONEncoder

class ObjectEncoder(JSONEncoder):
  def default(self, obj):
    if hasattr(obj, "to_json"):
      return obj.to_json()
    return json.JSONEncoder.default(self, obj)

app.config["RESTFUL_JSON"] = { "cls" : ObjectEncoder }

import howifeel.auth
import howifeel.ui
import howifeel.api
