import datetime
import logging
import math
import random
import time

from django.utils import simplejson as json
from google.appengine.api import users
from google.appengine.ext import db

RADIUS_OF_EARTH_METERS = 6378100
TRIGGER_DISTANCE_METERS = 15
ZOMBIE_VISION_DISTANCE_METERS = 200
MAX_TIME_INTERVAL_SECS = 60 * 10  # 10 minutes

ZOMBIE_SPEED_VARIANCE = 0.2
MIN_NUM_ZOMBIES = 20
MIN_ZOMBIE_DISTANCE_FROM_PLAYER = 20
MAX_ZOMBIE_CLUSTER_SIZE = 4
MAX_ZOMBIE_CLUSTER_RADIUS = 30

DEFAULT_ZOMBIE_SPEED = 3 * 0.447  # x miles per hour in meters per second
DEFAULT_ZOMBIE_DENSITY = 20.0  # zombies per square kilometer

INFECTED_PLAYER_TRANSITION_SECONDS = 120

class Error(Exception):
  """Base error class for all model errors."""

class ModelStateError(Error):
  """A model was in an invalid state."""

class InvalidLocationError(Error):
  """A latitude or longitude was invalid."""


class Entity():
  """An Entity is the base class of every entity in the game.
  
  Entities have a location and a last location update timestamp.
  """
  def __init__(self, game, encoded=None):
    self.game = game
    self.location = (None, None)
    if encoded:
      self.FromString(encoded)
  
  def DictForJson(self):
    return {"lat": self.Lat(), "lon": self.Lon()}
  
  def ToString(self):
    return json.dumps(self.DictForJson())
  
  def FromString(self, encoded):
    obj = json.loads(encoded)
    if obj["lat"] and obj["lon"]:
      self.SetLocation(obj["lat"], obj["lon"])
    return obj
  
  def Invalidate(self, timedelta):
    """Called to invalidate the current state, after some amount of time has
    passed.
    
    Args:
      timedelta: The amount of time that has passed since Invalidate was last
          called.  A datetime.timedelta object.
    """
  
  def Lat(self):
    return self.location[0]
  
  def Lon(self):
    return self.location[1]

  def SetLocation(self, lat, lon):
    if lat is None or lon is None:
      raise InvalidLocationError("Lat and Lon must not be None.")
    if lat > 90 or lat < -90:
      raise InvalidLocationError("Invalid latitude: %s" % lat)
    if lon > 180 or lon < -180:
      raise InvalidLocationError("Invalid longitude: %s" % lon)
    
    self.location = (lat, lon)
  
  def DistanceFrom(self, other):
    """Compute the distance to another Entity."""
    return self.DistanceFromLatLon(other.Lat(), other.Lon())
  
  def DistanceFromLatLon(self, lat, lon):
    dlon = lon - self.Lon()
    dlat = lat - self.Lat()
    a = math.sin(math.radians(dlat/2)) ** 2 + \
        math.cos(math.radians(self.Lat())) * \
        math.cos(math.radians(lat)) * \
        math.sin(math.radians(dlon / 2)) ** 2
    greatCircleDistance = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    distance = RADIUS_OF_EARTH_METERS * greatCircleDistance
    return distance
  

class Player(Entity):
  """A player is a player of the game, obviously I hope."""

  def __init__(self, game, encoded=None, user=None):
    self.infected = False
    self.is_zombie = False
    self.reached_destination = False
    Entity.__init__(self, game, encoded)
    if user:
      self.email = user.email()
  
  def DictForJson(self):
    if self.email is None:
      raise ModelStateError("User must be set before the Player is encoded.")
    dict = Entity.DictForJson(self)
    dict["email"] = self.email
    dict["infected"] = self.infected
    if self.infected:
      dict["infected_time"] = self.infected_time
    dict["is_zombie"] = self.is_zombie
    dict["reached_destination"] = self.reached_destination
    return dict

  def FromString(self, encoded):
    obj = Entity.FromString(self, encoded)
    self.email = obj["email"]
    self.infected = obj["infected"]
    if self.infected:
      self.infected_time = obj["infected_time"]
    self.is_zombie = obj["is_zombie"]
    self.reached_destination = obj["reached_destination"]
  
  def Email(self):
    return self.email
  
  def Invalidate(self, timedelta):
    """Determines whether or not the player has transitioned from infected to
    zombie."""
    if self.infected and \
       time.time() - self.infected_time > \
           INFECTED_PLAYER_TRANSITION_SECONDS:
      self.is_zombie = True
      
  def Infect(self):
    """Call to trigger this Player getting infected by a zombie."""
    self.infected = True
    self.infected_time = time.time()
    
  def ReachedDestination(self):
    """Call to indicate that this player has reached the game's destination."""
    logging.info("Player reached destination.")
    self.reached_destination = True
  
  def HasReachedDestination(self):
    return self.reached_destination
  
  def IsInfected(self):
    return self.infected


class Trigger(Entity):
  """A trigger is an element that can trigger some game action, when reached.
  
  For example: a destination is an entity in the game that triggers the 'win
    game' state.  A Zombie is an entity in the game that triggers the 'lose
    game' state.
  
  Triggers should implement the Process interface method, which gives it
  a hook to modify the game state at each elapsed interval.
  """
  
  def Trigger(self, player):
    """Process any state changes that should occur in the game when this
    trigger interacts with the specified Player."""
    # By default, no action.
    pass   


class Zombie(Trigger):
  
  def __init__(self, game, encoded=None, speed=None, chasing=None):
    Entity.__init__(self, game, encoded)
    
    if speed:
      self.speed = speed
      
    # Chasing is the player object that the zombie is chasing
    self.chasing = chasing
  
  def Advance(self, seconds, player_iter):
    """Meander some distance.
    
    Args:
      timedelta: a datetime.timedelta object indicating how much time has
          elapsed since the last time we've advanced the game.
      player_iter: An iterator that will walk over the players in the game.
    """
    # Advance in 1-second increments
    players = [player for player in player_iter]
    while seconds > 0:
      distance_to_move = seconds * self.speed
      self.ComputeChasing(players)
      if self.chasing:
        distance = self.DistanceFrom(self.chasing)
        self.MoveTowardsLatLon(self.chasing.Lat(),
                               self.chasing.Lon(),
                               min(distance, distance_to_move))
      else:
        random_lat = self.Lat() + random.random() - 0.5
        random_lon = self.Lon() + random.random() - 0.5
        self.MoveTowardsLatLon(random_lat, random_lon, distance_to_move)
      seconds = seconds - 1
      
  def MoveTowardsLatLon(self, lat, lon, distance):
    dstToLatLon = self.DistanceFromLatLon(lat, lon)
    magnitude = 0
    if dstToLatLon > 0:
      magnitude = distance / dstToLatLon
    dLat = (lat - self.Lat()) * magnitude
    dLon = (lon - self.Lon()) * magnitude
    self.SetLocation(self.Lat() + dLat, self.Lon() + dLon)
  
  def ComputeChasing(self, player_iter):
    min_distance = None
    min_player = None
    for player in player_iter:
      distance = self.DistanceFrom(player)
      if min_distance is None or distance < min_distance:
        min_distance = distance
        min_player = player
    
    if min_distance < ZOMBIE_VISION_DISTANCE_METERS:
      self.chasing = player
    else:
      self.chasing = None

  def Trigger(self, player):
    player.Infect()
  
  def DictForJson(self):
    dict = Entity.DictForJson(self)
    dict["speed"] = self.speed
    if self.chasing:
      dict["chasing"] = self.chasing.Email()
    return dict
  
  def FromString(self, encoded):
    obj = Entity.FromString(self, encoded)
    self.speed = float(obj["speed"])
    if obj.has_key("chasing"):
      self.chasing = obj["chasing"]


class Destination(Trigger):
  
  def Trigger(self, player):
    player.ReachedDestination()


class Game(db.Model):
  """A Game contains all the information about a ZombieRun game."""
  
  owner = db.UserProperty(auto_current_user_add=True)
  
  # The list of player emails, for querying.
  player_emails = db.StringListProperty()
  
  # The actual encoded player data.
  players = db.StringListProperty()
  zombies = db.StringListProperty()
  destination = db.StringProperty()
  
  # Meters per Second
  average_zombie_speed = db.FloatProperty(default=DEFAULT_ZOMBIE_SPEED)
  
  # Zombies / km^2
  zombie_density = db.FloatProperty(default=DEFAULT_ZOMBIE_DENSITY)
  
  started = db.BooleanProperty(default=False)
  done = db.BooleanProperty(default=False)
  humans_won = db.BooleanProperty(default=False)
  
  game_creation_time = db.DateTimeProperty(auto_now_add=True)
  last_update_time = db.DateTimeProperty(auto_now=True)
  
  def Id(self):
    # Drop the "g" at the beginning of the game key name.
    return int(self.key().name()[1:])
  
  def Players(self):
    for encoded in self.players:
      yield Player(self, encoded)
  
  def PlayersInPlay(self):
    """Iterate over the Players in the Game which have locations set, have not
    reacahed the destination, and are not infected.
    
    Returns:
        Iterable of (player_index, player) tuples.
    """
    for i, player in enumerate(self.Players()):
      if (player.Lat() and 
          player.Lon() and 
          not player.HasReachedDestination() and
          not player.IsInfected()):
        yield i, player
  
  def AddPlayer(self, player):
    self.players.append(player.ToString())
    self.player_emails.append(player.Email())
  
  def SetPlayer(self, index, player):
    if index > len(self.players) - 1:
      raise ModelStateError("Trying to set a player that doesn't exist.")
    self.players[index] = player.ToString()
    self.player_emails[index] = player.Email()
  
  def Zombies(self):
    for encoded in self.zombies:
      yield Zombie(self, encoded)
  
  def AddZombie(self, zombie):
    self.zombies.append(zombie.ToString())
    
  def SetZombie(self, index, zombie):
    if index > len(self.zombies) - 1:
      raise ModelStateError("Trying to set a zombie that doesn't exist.")
    self.zombies[index] = zombie.ToString()
  
  def Destination(self):
    return Destination(self, self.destination)
  
  def SetDestination(self, destination):
    self.destination = destination.ToString()
  
  def Entities(self):
    """Iterate over all Entities in the game."""
    for zombie in self.Zombies():
      yield zombie
    for player in self.Players():
      yield player
    yield self.Destination()
  
  def Start(self):
    self.started = True
    
  def Started(self):
    return self.started
  
  def IsDone(self):
    return self.done
  
  def HaveHumansWon(self):
    return self.done and self.humans_won

  def Advance(self):
    if not self.started:
      return
    
    timedelta = datetime.datetime.now() - self.last_update_time
    seconds = timedelta.seconds + timedelta.microseconds / float(1e6)
    seconds_to_move = min(seconds, MAX_TIME_INTERVAL_SECS)
    
    for entity in self.Entities():
      entity.Invalidate(timedelta)
    
    for i, zombie in enumerate(self.Zombies()):
      zombie.Advance(seconds_to_move,
                     [player for i, player in self.PlayersInPlay()])
      self.SetZombie(i, zombie)
      
    # Perform triggers
    for i, player in self.PlayersInPlay():
      # Trigger destination first, so that when a player has reached the
      # destination at the same time they were caught by a zombie, we give them
      # the benefit of the doubt.
      destination = self.Destination()
      if player.DistanceFrom(destination) < TRIGGER_DISTANCE_METERS:
        destination.Trigger(player)

      for zombie in self.Zombies():
        if player.HasReachedDestination():
          # This player is out of the game, they succeeded.
          continue

        if player.DistanceFrom(zombie) < TRIGGER_DISTANCE_METERS:
          zombie.Trigger(player)
      self.SetPlayer(i, player)
    
    # Is the game over?
    uninfected_player_who_hasnt_reached_destination = False
    player_who_is_not_infected = True
    for player in self.Players():
      if player.IsInfected():
        player_who_is_not_infected = False
      elif not player.HasReachedDestination():
        uninfected_player_who_hasnt_reached_destination = True

    if not player_who_is_not_infected:
      # All players have been infected.
      self.done = True
      self.humans_won = False
    elif not uninfected_player_who_hasnt_reached_destination:
      # There are players how aren't infected, and they have all reached the
      # destination
      self.done = True
      self.humans_won = True