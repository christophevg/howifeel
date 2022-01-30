import os
from flask import Flask, render_template

template_dir = os.path.abspath("src/pages")
static_dir   = os.path.abspath("src/static")
app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)

@app.route("/")
def hello():
  return render_template('index.html')

@app.route("/mood")
def mood():
  return render_template('mood.html')
