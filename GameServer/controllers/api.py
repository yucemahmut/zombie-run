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
from models.game import Entity
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
MAX_ZOMBIE_CLUSTER_SIZE = 4
MAX_ZOMBIE_CLUSTER_RADIUS = 30

DEFAULT_ZOMBIE_SPEED = 1.34  # 3 miles per hour in meters per second
DEFAULT_ZOMBIE_DENSITY = 50.0  # 50 zombies per square kilometer


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
  """The GameHandler is really a base RequestHandler for the other
  RequestHandlers in the API.  It's not capable of handling anything on its own,
  but rather provides a series of methods that are useful to the rest of the
  handlers."""
  
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
    
    dictionary["player"] = users.get_current_user().email()
    
    dictionary["players"] = []
    for player_str in game.players:
      player_dict = json.loads(player_str)
      dictionary["players"].append(player_dict)

    # TODO: only output the zombies that are near enough to the current user
    # to be of any interest.  Possibility: compute line-of-sight from the
    # current user based on the nearby terrain, to encourage players to travel
    # to the top of nearby hills to get a better view.
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
    
  def RedirectToLogin(self):
    self.redirect(users.create_login_url(self.request.uri))
  
  def RedirectToGame(self, game):
    self.redirect("/game?gid=%d" % game.Id())


class JoinHandler(GameHandler):
  """Handles players joining an ongoing game."""
  
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


class CreateHandler(JoinHandler):
  """Handles creating a new game."""
  
  def get(self):
    """Task: find an unused game id, create the state, and return the id.
    
    Expects no parameters to be present in the request.  Creates a random game
    id, tests whether or not that game id exists in the datastore.  If yes,
    repeat.  If no, write a Game entry to the datastore with that game id
    and return that id in the response content.
    """
    user = users.get_current_user()
    if not user:
      self.RedirectToLogin()
    else:
      game = self.CreateGame(user)
      self.RedirectToGame(game)
        
  def CreateGame(self, user):
    def CreateNewGameIfAbsent(game_id):
      game_key = self.GetGameKeyName(game_id)
      if Game.get_by_key_name(game_key) is None:
        game = Game(key_name=game_key,
                    owner=user,
                    average_zombie_speed=DEFAULT_ZOMBIE_SPEED,
                    zombie_density=DEFAULT_ZOMBIE_DENSITY)
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
    
    epicenter_lat, epicenter_lon = self.GetZombieEpicenter(game, owner)
    
    # not / 2 because we want to cover more than the area just between the
    # player and the destination
    radius_m = owner.DistanceFrom(game.Destination())  
    radius_km = radius_m / 1000
    area_kmsq = math.pi * radius_km * radius_km
    logging.info("Computing zombie count for an area of %f square km" %
                 area_kmsq)
    
    # Populate the zombies.
    num_zombies = max(game.zombie_density * area_kmsq, MIN_NUM_ZOMBIES)
    
    # TODO: Implement keeping the zombies at least some distance away from each
    # of the players.
    while len(game.zombies) < num_zombies:
      max_zombie_cluster_size = min(MAX_ZOMBIE_CLUSTER_SIZE,
                                    num_zombies - len(game.zombies))
      zombie_cluster_size = random.randint(1, max_zombie_cluster_size)
      self.AddZombieCluster(game,
                            epicenter_lat,
                            epicenter_lon,
                            radius_m,
                            zombie_cluster_size)
      
  def AddZombieCluster(self,
                       game,
                       epicenter_lat, 
                       epicenter_lon, 
                       max_radius, 
                       num_zombies):
    cluster_distance_from_epicenter = random.random() * max_radius
    cluster_lat, cluster_lon = \
        self.RandomPointNear(epicenter_lat,
                             epicenter_lon,
                             cluster_distance_from_epicenter)
    for i in xrange(num_zombies):
      self.AddZombie(game,
                     cluster_lat,
                     cluster_lon)
  
  def AddZombie(self, game, center_lat, center_lon):
    speed = game.average_zombie_speed * \
        ((random.random() - 0.5) * ZOMBIE_SPEED_VARIANCE + 1)

    distance_from_center = random.random() * MAX_ZOMBIE_CLUSTER_RADIUS

    lat, lon = self.RandomPointNear(center_lat, 
                                    center_lon, 
                                    distance_from_center)
    
    zombie = Zombie(speed=speed)
    zombie.SetLocation(lat, lon)
    game.AddZombie(zombie)

  def RandomPointNear(self, lat, lon, distance):
    radians = math.pi * 2 * random.random()
    to_lat = lat + math.sin(radians)
    to_lon = lon + math.cos(radians)
    
    base = Entity()
    base.SetLocation(lat, lon)

    to = Entity()
    to.SetLocation(to_lat, to_lon)

    base_to_distance = base.DistanceFrom(to)
    magnitude = distance / base_to_distance
    
    dLat = (to_lat - lat) * magnitude
    dLon = (to_lon - lon) * magnitude
    
    return (lat + dLat, lon + dLon) 
  
  def GetZombieEpicenter(self, game, owner):
    # Figure out the midpoint of the owner and the destination
    destination = game.Destination()
    dLat = destination.Lat() - owner.Lat()
    dLon = destination.Lon() - owner.Lon()
    mid_lat = owner.Lat() + dLat / 2
    mid_lon = owner.Lon() + dLon / 2
    return (mid_lat, mid_lon)


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
  
        # TODO: compute the zombie density in an area around each player, and if
        # the zombie density drops below a certain level, add more zombies at
        # the edge of that area.  This should ensure that players can travel
        # long distances without running away from the original zombie
        # population.
        if game.started:
          game.Advance()
          
        self.PutGame(game, False)
        return game
      
      game = db.RunInTransaction(Put)
      self.OutputGame(game)
    else:
      self.RedirectToLogin()