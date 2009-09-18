import logging
import random
import wsgiref.handlers
import yaml
from django.utils import simplejson as json
from models.game import Destination
from models.game import Game
from models.game import Player
from models.game import Zombie
from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext import webapp


GAME_ID_PARAMETER = "gid"
LATITUDE_PARAMETER = "lat"
LONGITUDE_PARAMETER = "lon"
NUMBER_OF_ZOMBIES_PARAMETER = "num_zombies"
AVERAGE_SPEED_OF_ZOMBIES_PARAMETER = "average_zombie_speed"
ZOMBIE_SPEED_VARIANCE = 0.2


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

    game = Game.get_by_key_name(self.GetGameKeyName(game_id))
    if game is None:
      raise GameNotFoundError()

    if authorize:
      self.Authorize(game)
    
    self.game = game
    return game

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
    game.put()
    
    return game


class CreateHandler(JoinHandler):
  """Handles creating a new game state."""
  
  def get(self):
    """Task: find an unused game id, create the state, and return the id.
    
    Expects no parameters to be present in the request.  Creates a random game
    id, tests whether or not that game id exists in the datastore.  If yes,
    repeat.  If no, write a Game entry to the datastore with that game id
    and return that id in the response content.
    """
    user = users.get_current_user()
    if user:
      game = self.CreateGame()
      self.AddPlayerToGame(game, user)
      game.put()
      self.OutputGame(game)
    else:
      raise AuthorizationError("Cannot join a game if you aren't a logged-in "
                               "user.")  
  def CreateGame(self):
    def CreateNewGameIfAbsent(game_id):
      game_key = self.GetGameKeyName(game_id)
      if Game.get_by_key_name(game_key) is None:
        game = Game(key_name=game_key)
        game.put()
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
        game.put()
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
      game.put()
      
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
    
    # Populate the zombies.
    # TODO: allow one ot change the number of zombies in the request
    num_zombies = 0
    average_zombie_speed = 0
    try:
      num_zombies = int(self.request.get(NUMBER_OF_ZOMBIES_PARAMETER))
      average_zombie_speed = \
          float(self.request.get(AVERAGE_SPEED_OF_ZOMBIES_PARAMETER))
    except ValueError, e:
      raise MalformedRequestError("Start game must include the zombie count "
                                  "and average speed parameters, both numeric.")
    
    logging.info(game.zombies);
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
          
        game.put()
        return game
      
      game = db.RunInTransaction(Put)
      self.OutputGame(game)
    else:
      self.redirect(users.create_login_url(self.request.uri))