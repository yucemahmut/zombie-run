import logging
import os

import main

from models import game
from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template


class Error(Exception):
  """Base error."""


class IndexPageHandler(webapp.RequestHandler):
  
  def get(self):
    """ foo """
    user = users.get_current_user()
    template_values = {}
    if user:
      query = game.Game.all()
      query.order("-last_update_time")
      query.filter("owner =", user)
      
      games = []
      for db_game in query:
        if db_game.started:
          games.append(db_game)
    
      template_values["games"] = games
      template_values["logout"] = users.create_logout_url(
          main.REVERSE_URL_BINDINGS[IndexPageHandler]) 
    else:
      template_values["login"] = users.create_login_url(
          main.REVERSE_URL_BINDINGS[IndexPageHandler])
    
    path = os.path.join(os.path.dirname(__file__), 'templates/index.html')
    self.response.out.write(template.render(path, template_values))