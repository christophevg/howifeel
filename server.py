import os
from flask import Flask, render_template

template_dir = os.path.abspath("src/pages")
app = Flask(__name__, template_folder=template_dir)

@app.route("/")
def hello():
  return render_template('index.html')
