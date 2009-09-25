import logging
import random

import main

from models import game as models
from controllers import gamestate
from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template


class Error(Exception):
  """Base error."""


class IndexPageHandler(gamestate.GameHandler):
  
  def get(self):
    """ foo """
    user = users.get_current_user()
    template_values = {}
    if user:
      query = models.Game.all()
      query.order("-last_update_time")
      query.filter("owner =", user)
      
      last_game = None
      for db_game in query:
        if db_game.started:
          last_game = db_game
          break
    
      template_values["last_game"] = last_game
      template_values["logout"] = users.create_logout_url(
          main.REVERSE_URL_BINDINGS[IndexPageHandler]) 
      self.OutputTemplate(template_values, 'index.html')
    else:
      template_values["login"] = users.create_login_url(
          main.REVERSE_URL_BINDINGS[IndexPageHandler])
      self.OutputTemplate(template_values, 'intro.html')
    

AVERAGE_ZOMBIE_SPEED_PARAMETER = "average_zombie_speed"
ZOMBIE_DENSITY_PARAMETER = "zombie_density"
START_IMMEDIATELY_PARAMETER = "start_immediately"


class CreateHandler(gamestate.JoinHandler):
  
  def get(self):
    """Task: find an unused game id, create the state, and return the id.
    
    Expects no parameters to be present in the request.  Creates a random game
    id, tests whether or not that game id exists in the datastore.  If yes,
    repeat.  If no, write a Game entry to the datastore with that game id
    and return that id in the response content.
    """
    user = users.get_current_user()
    if not user:
      raise models.AuthorizationError(
          "Cannot create a game if you aren't a logged-in user.")
    
    average_zombie_speed = None
    zombie_density = None
    start_immediately = False
    try:
      average_zombie_speed = \
          float(self.request.get(AVERAGE_ZOMBIE_SPEED_PARAMETER))
      zombie_density = \
          float(self.request.get(ZOMBIE_DENSITY_PARAMETER))
      if self.request.get(START_IMMEDIATELY_PARAMETER):
        start_immediately = True
    except TypeError, e:
      raise models.MalformedRequestError("Average zombie speed or density "
                                         "parameters not present or not "
                                         "numeric.")
    except ValueError, e:
      raise models.MalformedRequestError("Average zombie speed or density "
                                         "parameters not present or not "
                                         "numeric.")

    game = self.CreateGame(user, average_zombie_speed, zombie_density)
    
    if start_immediately:
      self.redirect("/game?gid=%s" % game.Id())
    else:
      self.redirect("/wait?gid=%s" % game.Id())
    
        
  def CreateGame(self, user, average_zombie_speed, zombie_density):
    def CreateNewGameIfAbsent(game_id):
      game_key = self.GetGameKeyName(game_id)
      if models.Game.get_by_key_name(game_key) is None:
        game = models.Game(key_name=game_key,
                           owner=user,
                           average_zombie_speed=average_zombie_speed,
                           zombie_density=zombie_density)
        self.AddPlayerToGame(game, user)
        self.PutGame(game, True)
        return game
      return None

    magnitude = 9999
    game_id = None
    game = None
    while game is None:
      # TODO: Limit this to not blow up the potential size of a game id to an
      # arbitrarily large number.
      game_id = random.randint(0, magnitude)
      game = db.RunInTransaction(CreateNewGameIfAbsent,
                                 game_id)
      magnitude = magnitude * 10 + 9
    return game


class GameHandler(gamestate.GameHandler):
  
  def get(self):
    user = users.get_current_user()
    game = self.GetGame()
    self.OutputTemplate({"game": game, "user": user}, "game.html")


class WaitHandler(gamestate.GameHandler):

  def get(self):
    game = self.GetGame()
    self.OutputTemplate({"game": game}, "wait.html")