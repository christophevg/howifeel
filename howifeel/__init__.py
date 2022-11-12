__version__ = "0.0.2"

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

import howifeel.auth
import howifeel.ui
import howifeel.api
