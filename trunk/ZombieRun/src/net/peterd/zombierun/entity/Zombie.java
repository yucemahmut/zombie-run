package net.peterd.zombierun.entity;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.TimeUnit;

import net.peterd.zombierun.constants.Constants;
import net.peterd.zombierun.game.GameEvent;
import net.peterd.zombierun.service.GameEventBroadcaster;
import net.peterd.zombierun.service.GameEventListener;
import net.peterd.zombierun.util.FloatingPointGeoPoint;
import net.peterd.zombierun.util.GeoPointUtil;

import net.peterd.zombierun.util.Log;

import com.google.android.maps.GeoPoint;

public class Zombie implements GameEventListener {

  private final int id;
  private final List<Player> players;
  private final Map<Player, Double> distancesToPlayers = new HashMap<Player, Double>();
  private final double zombieSpeedMetersPerSecond;
  private final GameEventBroadcaster gameEventBroadcaster;
  private FloatingPointGeoPoint location;
  private boolean isNoticingPlayer = false;
  private boolean isNearPlayer = false;
  private Player playerZombieIsChasing;
  
  public Zombie(int id,
      FloatingPointGeoPoint startingLocation,
      List<Player> players,
      Player playerZombieIsChasing,
      double zombieSpeedMetersPerSecond,
      GameEventBroadcaster gameEventBroadcaster) {
    this.id = id;
    location = startingLocation;
    this.players = players;
    this.playerZombieIsChasing = playerZombieIsChasing;
    this.zombieSpeedMetersPerSecond = zombieSpeedMetersPerSecond;
    this.gameEventBroadcaster = gameEventBroadcaster;
  }
  
  public Zombie(int id,
      FloatingPointGeoPoint startingLocation,
      List<Player> players,
      double zombieSpeedMetersPerSecond,
      GameEventBroadcaster gameEventBroadcaster) {
    this(id, startingLocation, players, null, zombieSpeedMetersPerSecond, gameEventBroadcaster);
  }

  public GeoPoint getLocation() {
    return location.getGeoPoint();
  }

  public boolean isNoticingPlayer() {
    return isNoticingPlayer;
  }
  
  public void advance(long time, TimeUnit timeUnit) {
    computeDistancesToPlayers();
    
    // If we get an interval that's too long, it'll screw up the distance that the zombies move,
    // which can make them completely overshoot or something.
    long intervalMs = Math.min(timeUnit.toMillis(time), Constants.gameUpdateDelayMs);
    
    double movementDistanceMeters = zombieSpeedMetersPerSecond * (((float) intervalMs) / 1000);

    // hasNoticedPlayer sets playerZombieIsChasing and distanceToPlayerZombieIsChasing.
    if (hasNoticedPlayer()) {
      Player playerZombieIsChasing = this.playerZombieIsChasing;
      movementDistanceMeters =
          Math.min(movementDistanceMeters,
              distancesToPlayers.get(playerZombieIsChasing));
      moveTowardPlayer(playerZombieIsChasing, movementDistanceMeters);

      // Setting isNoticingPlayer to true must happen after conditionallyVibrateOnPlayerNoticed, as
      // that method checks to see if it's being called while isNoticingPlayer is false to determine
      // whether or not this is the point at which the zombie switches from 'not noticed player' to
      // 'noticed player.'
      conditionallyVibrateOnPlayerNoticed();
      isNoticingPlayer = true;
    } else {
      meander(movementDistanceMeters);
      isNoticingPlayer = false;
    }
    
    conditionallyWarnZombieNearPlayer();
    
    Player playerZombieIsChasing = this.playerZombieIsChasing;
    if (playerZombieIsChasing != null && hasCaughtPlayer(playerZombieIsChasing)) {
      gameEventBroadcaster.broadcastEvent(GameEvent.ZOMBIE_CATCH_PLAYER);
    }
  }

  private void computeDistancesToPlayers() {
    for (Player player : players) {
      FloatingPointGeoPoint playerLocation = player.getLocation();
      if (playerLocation != null) {
        double distance = GeoPointUtil.distanceMeters(playerLocation, location);
        distancesToPlayers.put(player, distance);
      }
    }
  }

  private void conditionallyWarnZombieNearPlayer() {
    Player playerZombieIsChasing = this.playerZombieIsChasing;
    if (playerZombieIsChasing != null && isNearPlayer(playerZombieIsChasing)) {
      if (!isNearPlayer) {
        gameEventBroadcaster.broadcastEvent(GameEvent.ZOMBIE_NEAR_PLAYER);
      }
      isNearPlayer = true;
    } else {
      isNearPlayer = false;
    }
  }
  
  private void conditionallyVibrateOnPlayerNoticed() {
    if (!isNoticingPlayer) {
      gameEventBroadcaster.broadcastEvent(GameEvent.ZOMBIE_NOTICE_PLAYER);
    }
  }
  
  /**
   * Precondition: {@link #playerZombieIsChasing} must not be null.
   * @return
   */
  private boolean hasCaughtPlayer(Player playerZombieIsChasing) {
    return distancesToPlayers.get(playerZombieIsChasing) <
        Constants.zombieCatchPlayerDistanceMeters;
  }
  
  /**
   * Determines whether or not the zombie has noticed a player, and sets
   * {@link #playerZombieIsChasing} and {@link #distanceToPlayerZombieIsChasing} appropriately (or
   * null if the zombie is not noticing a player.
   * 
   * @return True if the zombie has noticed a player.  The player the zombie has noticed and the
   *    distance to that player will be stored in {@link #playerZombieIsChasing} and
   *    {@link #distanceToPlayerZombieIsChasing}.
   */
  private boolean hasNoticedPlayer() {
    if (distancesToPlayers.isEmpty()) {
      return false;
    }
    
    // If this zombie is already chasing a player, then it should continue chasing that player until
    // it is no longer interested.
    if (playerZombieIsChasing != null) {
      if (distancesToPlayers.get(playerZombieIsChasing) <
          Constants.zombieNoticePlayerDistanceMeters) {
        return true;
      }
    }
    
    Double minDistanceToPlayer = null;
    Player playerWithMinimumDistance = null;
    for (Map.Entry<Player, Double> entry : distancesToPlayers.entrySet()) {
      if (minDistanceToPlayer == null || entry.getValue() < minDistanceToPlayer) {
        minDistanceToPlayer = entry.getValue();
        playerWithMinimumDistance = entry.getKey();
      }
    }
    
    if (minDistanceToPlayer < Constants.zombieNoticePlayerDistanceMeters) {
      playerZombieIsChasing = playerWithMinimumDistance;
      return true;
    } else {
      playerZombieIsChasing = null;
      return false;
    }
  }
  
  private boolean isNearPlayer(Player player) {
    return distancesToPlayers.get(player) < Constants.zombieNearPlayerDistanceMeters;
  }
  
  private void meander(double movementDistanceMeters) {
    // TODO: Give them a primary direction, not just random movements.
    // TODO: Make zombies cluster a little bit
    location = GeoPointUtil.getGeoPointNear(location, movementDistanceMeters);
  }
  
  private void moveTowardPlayer(Player player, double movementDistanceMeters) {
    Log.d("ZombieRun.Zombie", "Moving towards player " + player.toString());
    location = GeoPointUtil.geoPointTowardsTarget(location,
        player.getLocation(),
        movementDistanceMeters);
  }
  
  public String toString() {
    int indexOfPlayerZombieIsChasing = -1;
    if (playerZombieIsChasing != null) {
      indexOfPlayerZombieIsChasing = players.indexOf(playerZombieIsChasing);
    }
    return id + ":" +
        Integer.toString(indexOfPlayerZombieIsChasing) + ":" +
        location.toString() + ":" +
        zombieSpeedMetersPerSecond;
  }
  
  public static Zombie fromString(String stringEncodedZombie,
      List<Player> players,
      GameEventBroadcaster gameEventBroadcaster) {
    String[] parts = stringEncodedZombie.split(":", 4);
    if (parts.length != 4) {
      Log.e("ZombieRun.Zombie", "Did not find 3 parts, which should have been the zombie id, " +
      		"index of the player the zombie is chasing (-1 for none), and a string-encoded " +
          "FloatingPointGeoPoint, in '" + stringEncodedZombie + "'.");
      return null;
    }
    
    String zombieIdStr = parts[0];
    int zombieId;
    try {
      zombieId = Integer.parseInt(zombieIdStr);
    } catch (NumberFormatException e) {
      Log.e("Zombie", "Could not parse integer zombie id from '" + zombieIdStr + "'.", e);
      return null;
    }
    
    String indexOfPlayerZombieIsChasingStr = parts[1];
    Player playerZombieIsChasing = null;
    try {
      int indexOfPlayerZombieIsChasing = Integer.parseInt(indexOfPlayerZombieIsChasingStr);
      if (indexOfPlayerZombieIsChasing >= 0 && indexOfPlayerZombieIsChasing < players.size()) {
        playerZombieIsChasing = players.get(indexOfPlayerZombieIsChasing);
      }
    } catch (NumberFormatException e) {
      Log.e("Zombie", "Could not parse integer player index from '" + 
          indexOfPlayerZombieIsChasingStr + "' to determine which player this zombie is " +
          "chasing.", e);
      return null;
    }
    
    String fpgpString = parts[2];
    FloatingPointGeoPoint fpgp = FloatingPointGeoPoint.fromString(fpgpString);
    if (fpgp == null) {
      Log.e("Zombie", "Could not parse zombie position FloatingPointGeoPoint from encoded " +
          "string '" + fpgpString + "'.");
      return null;
    }
    
    String zombieSpeedMetersPerSecondString = parts[3];
    double zombieSpeedMetersPerSecond = 0;
    try {
      zombieSpeedMetersPerSecond = Double.parseDouble(zombieSpeedMetersPerSecondString);
    } catch (NumberFormatException e) {
      Log.e("ZombieRun.Zombie", "Could not parse zombie speed from string '" +
          zombieSpeedMetersPerSecondString + "'.");
      return null;
    }
    
    Zombie zombie =
        new Zombie(zombieId,
            fpgp,
            players,
            playerZombieIsChasing,
            zombieSpeedMetersPerSecond,
            gameEventBroadcaster);
    return zombie;
  }
  
  public static class ZombieListSerializer {
    
    public static String toString(List<Zombie> zombies) {
      StringBuilder builder = new StringBuilder();
      for (Zombie zombie : zombies) {
        builder.append(zombie.toString());
        builder.append("\n");
      }
      return builder.toString();
    }

    public static List<Zombie> fromString(
        String encodedString,
        List<Player> players,
        GameEventBroadcaster gameEventBroadcaster) {
      List<Zombie> zombies = new ArrayList<Zombie>();
      String[] lines = encodedString.split("\n");
      for (int i = 0; i < lines.length; ++i) {
        Zombie zombie =
            Zombie.fromString(lines[i],
                players,
                gameEventBroadcaster);
        if (zombie != null) {
          zombies.add(zombie);
        }
      }
      return zombies;
    }
  }

  public void receiveEvent(GameEvent event) {
    
  }
}
