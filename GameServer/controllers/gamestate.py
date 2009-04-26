import random
import wsgiref.handlers
import yaml
from models.game import Game
from google.appengine.ext import db
from google.appengine.ext import webapp


GAME_ID_PARAMETER = "gid"
PLAYER_ID_PARAMETER = "pid"
PLAYER_DATA_PARAMETER = "pd"
DESTINATION_PARAMETER = "d"
ZOMBIES_PARAMETER = "z"
SECRET_KEY_PARAMETER = "s"
OWNER_PLAYER_ID = 0

class Error(Exception):
  """Base error."""

class MalformedRequestError(Error):
  """The incoming request was missing some required field or referenced data
  that does not exist."""

class GameNotFoundError(Error):
  """The game was not found."""

class AuthorizationError(Error):
  """The attempted operation was not authorized."""

class SecretKeyMismatchError(AuthorizationError):
  """The provided secret key did not match the stored key for the game id."""

class GameStartedError(Error):
  """The game has already started, precluding the attempted operation."""


class GameHandler(webapp.RequestHandler):

  _secret_key_upper_bound = 2**128

  def get(self):
    self.response.set_status(403, 'All requests must be POSTed.')

  def CreateNewSecretKey(self):
    """Generate a 128-bit hex-encoded secret key."""
    game_id_int = random.randint(0, self._secret_key_upper_bound)
    game_id_hex = hex(game_id_int)
    # Cut off the first two characters of the hex-encoded game id, which is
    # always "0x"
    return game_id_hex[2:]
  
  def GetGameKeyName(self, game_id):
    """For a given game id, get a string representing the game's key name.
    
    Args:
      game_id: The integer game id.
    
    Returns:
      A string with which one can create a db.Key for the game.
    """
    return "g%d" % game_id
  
  def GetGame(self, game_id=None, validate_secret_key=True):
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
      SecretKeyMismatchError: If the provided secret key does not match that in
          the datastore.
    """
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

    game_data = Game.get_by_key_name(self.GetGameKeyName(game_id))
    if game_data is None:
      raise GameNotFoundError()
    
    if validate_secret_key:
      secret_key = self.request.get(SECRET_KEY_PARAMETER, None)
      if secret_key is None:
        raise MalformedRequestError("Secret key not present in request.")

      player_id = self.request.get(PLAYER_ID_PARAMETER, None)
      try:
        player_id_int = int(player_id)
      except ValueError, e:
        raise MalformedRequestError("Player ID not an integer.")
      except TypeError, e:
        raise MalformedRequestError("Player ID not an integer.")
      if player_id is None:
        raise MalformedRequestError("Player ID not present in request.")
      
      recorded_secret_key = None
      if len(game_data.secret_keys) < player_id_int:
        raise MalformedRequestError("Player ID not valid, must be < %d" %
                                    len(game_data.players))
      recorded_secret_key = game_data.secret_keys[player_id_int]
      if recorded_secret_key != secret_key:
        raise SecretKeyMismatchError()
    
    return game_data
  
  def Output(self, dictionary):
    """Write the provided dictionary of key-value pairs to output."""
    self.response.headers["Content-Type"] = "text/plain; charset=utf-8"
    lines = []
    for key in dictionary:
      value = dictionary[key]
      if value is None or value == "None":
        continue
      elif hasattr(value, "__iter__"):
        for v in value:
          lines.append("%s[]:%s" % (key, str(v)))
      else:
        lines.append("%s:%s" % (key, str(value)))
    self.response.out.write("\n".join(lines))


class JoinHandler(GameHandler):
  """Handles players joining an unstarted game."""
  
  def get(self):
    self.post()
    
  def post(self):
    """Adds a player to the game.
    
    GAME_ID_PARAMETER must be present in the request and in the datastore.
    
    Adds the player to the game with a blank initial entry, returning the
    player's id and the game's secret key.
    """
    game = db.run_in_transaction(self.AddPlayerToGame)
    player_id = len(game.players) - 1
    self.Output({"player_id": player_id,
                 "secret": str(game.secret_keys[player_id]),
                 "destination": str(game.destination)})

  def AddPlayerToGame(self, game_id=None):
    """Retreive the game with the provided id and add a player.
    
    Returns:
      The modified and saved game object, with a new player appended to the
      end of the list of players.  The new player's id will be
      len(game.players) - 1 (the array index of the newest player.
    """
    game = self.GetGame(game_id=game_id, validate_secret_key=False)
    if game.started:
      raise GameStartedError("Cannot join game already in progress.")
    game.players.append(db.Text())
    game.secret_keys.append(db.Text(self.CreateNewSecretKey()))
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
    def CreateNewGameIfAbsent(game_id, destination):
      game_key = self.GetGameKeyName(game_id)
      if Game.get_by_key_name(game_key) is None:
        Game(key_name=game_key,
             started=False,
             destination=destination).put()
        return True
      return False
     
    magnitude = 9999
    game_id = None
    destination = self.request.get(DESTINATION_PARAMETER, None)
    if destination is None:
      raise MalformedRequestError("A game must have a destination when it's created.");
    
    while True:
      # TODO: Limit this to not blow up the potential size of a game id to an
      # arbitrarily large number.
      game_id = random.randint(0, magnitude)
      if db.run_in_transaction(CreateNewGameIfAbsent,
                               game_id,
                               destination):
        break
      magnitude = magnitude * 10 + 9

    game = db.run_in_transaction(self.AddPlayerToGame, game_id)
    self.Output({"game_id": game_id,
                 "player_id": 0,
                 "secret": str(game.secret_keys[0])})
    

class GetHandler(GameHandler):
  """Handles getting the current game state."""
  
  def get(self):
    self.post()
  
  def post(self):
    """Task: encode the game data in the output.
    
    GAME_ID_PARAMETER must be present in the request and in the datastore.
    """
    self.OutputGame(self.GetGame())

  def OutputGame(self, game):
    """Write the game data to the output, serialized as YAML.
    
    Args:
      game: The Game that should be written out.
    """
    key_values = {}
    key_values["players"] = [str(player) for player in game.players]
    key_values["zombies"] = str(game.zombies)
    if game.started:
      key_values["started"] = 1
    else:
      key_values["started"] = 0
    key_values["destination"] = str(game.destination)
    self.Output(key_values)


class StartHandler(GetHandler):
  """Handles starting a game."""
  
  def get(self):
    self.post()
  
  def post(self):
    def StartGame():
      if self.request.get(PLAYER_ID_PARAMETER, None) != str(OWNER_PLAYER_ID):
        raise AuthorizationError("Only the game owner can start the game.")
      game = self.GetGame()
      game.started = True
      game.put()
      return game
    game = db.run_in_transaction(StartGame)
    self.OutputGame(game)


class PutHandler(GetHandler):
  """The PutHandler handles registering updates to the game state.
  
  All update requests return the current game state, to avoid having to make
  two requests to update and get the game state.
  """
  
  def get(self):
    self.post()
  
  def post(self):
    """Task: Parse the input data and update the game state.
    
    Looks for parameters in the POST data to determine which action to take:
    
    Prerequirement: GAME_ID_PARAMETER is present in the request and in the
    datastore.
    
    If PLAYER_ID_PARAMETER and PLAYER_DATA_PARAMETER are found, update the
    location of the appropriate player.
    
    If ZOMBIES_PARAMETER is present, update the state of the zombie horde.
    """
    def UpdateGameData(player_id, player, zombies, secret):
      """Update the game data, returning the game."""
      game = self.GetGame()
      game.players[player_id] = db.Text(player)
      if zombies is not None:
        if player_id != OWNER_PLAYER_ID:
          raise AuthorizationError("Attempt to record position of zombies by "
                                   "a player who is not the game owner.")
        game.zombies = db.Text(zombies)
      game.put()
      return game
    
    player_id = None
    try:
      player_id = int(self.request.get(PLAYER_ID_PARAMETER, None))
    except ValueError, e:
      raise MalformedRequestError("Player id must be included in the request "
                                  "and be an integer.")

    player = self.request.get(PLAYER_DATA_PARAMETER, None)
    if player is None:
      raise MalformedRequestError("Player data not included in request.")
    
    zombies = self.request.get(ZOMBIES_PARAMETER, None)
    secret = self.request.get(SECRET_KEY_PARAMETER, None)
    game = db.run_in_transaction(UpdateGameData,
                                 player_id,
                                 player,
                                 zombies,
                                 secret)
    self.OutputGame(game)
