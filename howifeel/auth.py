from flask_login import LoginManager

from howifeel import app

login_manager = LoginManager(app)

from howifeel.user import User

@login_manager.user_loader
def load_user(user):
  return User.find(user)

login_manager.login_view = "show_login_page"
