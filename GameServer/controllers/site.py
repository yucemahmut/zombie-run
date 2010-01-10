import logging
import os
import random

from controllers import api
from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext.webapp import template
from models.game import Game
from models.game import Player


class HomepageHandler(api.GameHandler):
  
  def get(self):
    user = users.get_current_user()
    if not user:
      # If the user isn't logged in, then we render a frame around the
      # homepage, so that the iPhone won't register that we are opening
      # different urls and break us out of the webapp context that you get when
      # you add an icon to your homescreen.  The frame will render the same
      # homepage url, but with a parameter "wrap=0" indicating that we should
      # not render the frame template again.
      self.RenderLogin()
    else:
      # Look up the game that this player was recently playing.  If there is
      # none, or the game was done, then create a new game and proceed.
      game = self.GetLastGame(user)

      if game is None or game.done:
        logging.info("Creating a new game for player %s." % user.email())
        game = self.CreateGame(user)
      else:
        logging.info("Player %s playing game %d" % (user.email(), game.Id()))
        
      self.OutputTemplate({"game_id": game.Id()},
                           "game.html")
  def GetLastGame(self, user):
    """Get the last game that this player has played, or None if the player
    hasn't been involved in any games yet."""
    query = Game.all()
    query.filter("player_emails =", user.email())
    query.order("-game_creation_time")
    return query.get()
  
  def RenderLogin(self):
    self.OutputTemplate({"login_url": self.LoginUrl()}, "intro.html")
  
  def OutputTemplate(self, dict, template_name):
    path = os.path.join(os.path.dirname(__file__),
                        '../templates', 
                        template_name)
    self.response.out.write(template.render(path, dict))
        
  def CreateGame(self, user):
    def CreateNewGameIfAbsent(game_id):
      game_key = self.GetGameKeyName(game_id)
      if Game.get_by_key_name(game_key) is None:
        game = Game(key_name=game_key, owner=user)
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
  
  def AddPlayerToGame(self, game, user):
    for player in game.Players():
      if player.Email() == user.email():
        return game
    
    player = Player(game, user=user)
    game.AddPlayer(player)
    return game
  

class JoinHandler(HomepageHandler):

  def get(self):
    user = users.get_current_user()
    if not user:
      self.RenderLogin()
    else:
      game = self.GetGame(authorize=False)
      logging.info("Got game with id %d." % game.Id())
      self.AddPlayerToGame(game, user)
      logging.info("Added player to game.")
      self.PutGame(game, True)
      logging.info("Put Game.")
      self.RedirectToGame()


class NewHandler(HomepageHandler):
  
  def get(self):
    user = users.get_current_user()
    if not user:
      self.RenderLogin()
    else:
      self.CreateGame(user)
      self.redirect("/")