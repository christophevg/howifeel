__version__ = "0.0.1"

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
app.config["SECRET_KEY"] = os.urandom(12)

import flask_restful

api = flask_restful.Api(app)

import howifeel.auth
import howifeel.ui
import howifeel.api
