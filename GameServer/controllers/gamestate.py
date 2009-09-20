import datetime
import logging
import math
import os
import pickle
import random
import wsgiref.handlers
import yaml
from django.utils import simplejson as json
from models.game import Destination
from models.game import Game
from models.game import Player
from models.game import Zombie
from google.appengine.api import memcache
from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template


GAME_ID_PARAMETER = "gid"
LATITUDE_PARAMETER = "lat"
LONGITUDE_PARAMETER = "lon"
NUMBER_OF_ZOMBIES_PARAMETER = "num_zombies"
AVERAGE_SPEED_OF_ZOMBIES_PARAMETER = "average_zombie_speed"
ZOMBIE_SPEED_VARIANCE = 0.2
MIN_NUM_ZOMBIES = 20
MIN_ZOMBIE_DISTANCE_FROM_PLAYER = 20


class Error(Exception):
  """Base error."""

class MalformedRequestError(Error):
  """The incoming request was missing some required field or referenced data
  that does not exist."""

class GameNotFoundError(Error):
  """The game was not found."""

class GameStartedError(Error):
  """The game has already started, precluding the attempted operation."""
  
class GameStateError(Error):
  """There was some error in the game's state."""

class AuthorizationError(Error):
  """The current user was not allowed to execute this action."""


class GameHandler(webapp.RequestHandler):
  
  def __init__(self):
    self.game = None

  def GetGameKeyName(self, game_id):
    """For a given game id, get a string representing the game's key name.
    
    Args:
      game_id: The integer game id.
    
    Returns:
      A string with which one can create a db.Key for the game.
    """
    return "g%d" % game_id
  
  def GetGame(self, game_id=None, authorize=True):
    """Determines the game id and retreives the game data from the db.
    
    Args:
      game_id: If not None, gets the game with this id.  If None, takes the
          game id from the request
      validate_secret_key: If true, checks the request's SECRET_KEY_PARAMETER
          and validates it against the stored secret key in the database.  If
          there is a mismatch, raises SecretKeyMismatchError.
    
    Raises:
      MalformedRequestError: If the game id or secret key is not present in the
          request.
      GameNotFoundError: If the provided game id is not present in the
          datastore.
    """
    if self.game:
      return self.game
    
    if game_id is None:
      try:
        # Try to get and parse an integer from the game id parameter.
        game_id = int(self.request.get(GAME_ID_PARAMETER, None))
      except TypeError, e:
        raise MalformedRequestError("Game id not present in request or not an "
                                    "integer value.")
      except ValueError, e:
        raise MalformedRequestError("Game id not present in request or not an "
                                    "integer value.")
    
    game_key = self.GetGameKeyName(game_id)
    
    if self.LoadFromMemcache(game_key) or self.LoadFromDatastore(game_key):
      if authorize:
        self.Authorize(self.game)
      
      return self.game
    else:
      raise GameNotFoundError()
  
  def LoadFromMemcache(self, key):
    """Try loading the game from memcache.  Sets self.game, returns true if
    self.game was successfully set.  If false, self.game was not set."""
    encoded = memcache.get(key)
    
    if not encoded:
      logging.warn("Memcache miss.")
      return False
    
    try:
      self.game = pickle.loads(encoded)
      return True
    except pickle.UnpicklingError, e:
      logging.warn("UnpicklingError: %s" % e)
      return False
    
  def LoadFromDatastore(self, key):
    """Load the game from the database.  Sets self.game, returns true if
    self.game was successfully set.  If false, self.game was not set."""
    logging.info("Getting game from datastore.")
    game = Game.get_by_key_name(key)
    if game:
      self.game = game
      return True
    else:
      return False
  
  def PutGame(self, game, force_db_put):
    # Put to Datastore once every 30 seconds.
    age = datetime.datetime.now() - game.last_update_time
    game.last_update_time = datetime.datetime.now()
    if age.seconds > 30 or force_db_put:
      logging.info("Putting game to datastore.")
      game.put()

    # Put to Memcache.
    encoded = pickle.dumps(game)
    if not memcache.set(game.key().name(), encoded):
      logging.warn("Game set to Memcache failed.")

  def Authorize(self, game):
    user = users.get_current_user()
    if not user:
      raise AuthorizationError("Request to get a game by a non-logged-in-user.")
    else:
      authorized = False
      for player in game.Players():
        if player.Email() == user.email():
          authorized = True
          break
      if not authorized:
        raise AuthorizationError(
            "Request to get a game by a user who is not part of the game "
            "(unauthorized user: %s)." % user.email())
  
  def OutputGame(self, game):
    """Write the game data to the output, serialized as YAML.
    
    Args:
      game: The Game that should be written out.
    """
    dictionary = {}
    dictionary["game_id"] = game.Id()
    dictionary["owner"] = game.owner.email()
    
    dictionary["players"] = []
    for player_str in game.players:
      player_dict = json.loads(player_str)
      dictionary["players"].append(player_dict)
      
    dictionary["zombies"] = []
    for zombie_str in game.zombies:
      zombie_dict = json.loads(zombie_str)
      dictionary["zombies"].append(zombie_dict)
    
    if game.destination is not None:
      destination_dict = json.loads(game.destination)
      dictionary["destination"] = destination_dict
    
    self.Output(json.dumps(dictionary))
  
  def OutputTemplate(self, dict, template_name):
    path = os.path.join(os.path.dirname(__file__), 'templates', template_name)
    self.response.out.write(template.render(path, dict))
  
  def Output(self, output):
    """Write the game to output."""
    self.response.headers["Content-Type"] = "text/plain; charset=utf-8"
    logging.debug("Response: %s" % output)
    self.response.out.write(output)


class JoinHandler(GameHandler):
  """Handles players joining an unstarted game."""
  
  def get(self):
    """Adds a player to the game.
    
    GAME_ID_PARAMETER must be present in the request and in the datastore.
    
    Adds the player to the game with a blank initial entry, returning the
    player's id and the game's secret key.
    """
    def Join():
      game = self.GetGame(authorize=False)
      user = users.get_current_user()
      
      if user:
        game = self.AddPlayerToGame(game, user)
        self.PutGame(game, True)
      return game

    game = db.RunInTransaction(Join)
    self.OutputGame(game)

  def AddPlayerToGame(self, game, user):
    """Retreive the game with the provided id and add a player.
    
    Returns:
      The modified and saved game object, with a new player appended to the
      end of the list of players.  The new player's id will be
      len(game.players) - 1 (the array index of the newest player.
    """
    for player in game.Players():
      if player.Email() == user.email():
        return game
    
    player = Player(user=user)
    game.AddPlayer(player)
    return game


class GetHandler(GameHandler):
  """Handles getting the current game state."""
  
  def get(self):
    """Task: encode the game data in the output.
    
    GAME_ID_PARAMETER must be present in the request and in the datastore.
    """
    def GetAndAdvance():
      game = self.GetGame()
      if game.started:
        game.Advance()
        self.PutGame(game, False)
      return game
    game = db.RunInTransaction(GetAndAdvance)
    self.OutputGame(game)
    

class StartHandler(GetHandler):
  """Handles starting a game."""
  
  def get(self):
    def Start():
      game = self.GetGame()
      if game.started:
        # raise GameStateError("Cannot start a game twice.")
        pass
      if users.get_current_user() != game.owner:
        raise AuthorizationError("Only the game owner can start the game.")
      
      # Set the destination
      lat = None
      lon = None
      try:
        lat = float(self.request.get(LATITUDE_PARAMETER))
        lon = float(self.request.get(LONGITUDE_PARAMETER))
      except ValueError, e:
        raise MalformedRequestError(e)
      
      destination = Destination()
      destination.SetLocation(lat, lon)
  
      game.started = True
      game.SetDestination(destination)
      self.PopulateZombies(game)
      self.PutGame(game, True)
      
      return game
    
    game = db.RunInTransaction(Start)
    self.OutputGame(game)
    
  def PopulateZombies(self, game):
    # Figure out which player is the owner
    owner = None
    for player in game.Players():
      if player.Email() == game.owner.email():
        owner = player
    
    if not owner.Lat() or not owner.Lon():
      raise GameStateError("Cannot start a game before the game owner's "
                           "location is known.  Game owner: %s" %
                           owner.Email())
    
    # Figure out the midpoint of the owner and the destination
    destination = game.Destination()
    dLat = destination.Lat() - owner.Lat()
    dLon = destination.Lon() - owner.Lon()
    mid_lat = owner.Lat() + dLat / 2
    mid_lon = owner.Lon() + dLon / 2
    
    # Figure out how many zombies we will populate
    radius_km = owner.DistanceFrom(destination) / (2 * 1000)
    area_kmsq = math.pi * radius_km * radius_km
    logging.info("Computing zombie count for an area of %f square km" %
                 area_kmsq)
    
    # Populate the zombies.
    num_zombies = max(game.zombie_density * area_kmsq, MIN_NUM_ZOMBIES)
    average_zombie_speed = game.average_zombie_speed
    
    # TODO: Implement keeping the zombies at least some distance away from each
    # of the players.
    while len(game.zombies) < num_zombies:
      lat = mid_lat + (random.random() - 0.5) * dLat * 2
      lon = mid_lon + (random.random() - 0.5) * dLon * 2
      
      speed = average_zombie_speed * \
          ((random.random() - 0.5) * ZOMBIE_SPEED_VARIANCE + 1)
      
      zombie = Zombie(speed=speed)
      zombie.SetLocation(lat, lon)
      game.AddZombie(zombie)


class PutHandler(GetHandler):
  """The PutHandler handles registering updates to the game state.
  
  All update requests return the current game state, to avoid having to make
  two requests to update and get the game state.
  """
  
  def get(self):
    """Task: Parse the input data and update the game state."""
    user = users.get_current_user()
    if user:
      lat = None
      lon = None
      try:
        lat = float(self.request.get(LATITUDE_PARAMETER))
        lon = float(self.request.get(LONGITUDE_PARAMETER))
      except ValueError, e:
        raise MalformedRequestError(e)
      
      def Put():
        game = self.GetGame()
        for i, player in enumerate(game.Players()):
          if player.Email() == user.email():
            if player.Lat() != lat or player.Lon() != lon:
              player.SetLocation(float(self.request.get(LATITUDE_PARAMETER)),
                                 float(self.request.get(LONGITUDE_PARAMETER)))
              game.SetPlayer(i, player)
            break
  
        if game.started:
          game.Advance()
          
        self.PutGame(game, False)
        return game
      
      game = db.RunInTransaction(Put)
      self.OutputGame(game)
    else:
      self.redirect(users.create_login_url(self.request.uri))