package net.peterd.zombierun.entity;

import java.util.ArrayList;
import java.util.List;

import android.location.Location;
import android.location.LocationListener;
import android.os.Bundle;
import net.peterd.zombierun.util.Log;

import net.peterd.zombierun.constants.Constants;
import net.peterd.zombierun.game.GameEvent;
import net.peterd.zombierun.service.GameEventBroadcaster;
import net.peterd.zombierun.service.GameEventListener;
import net.peterd.zombierun.util.FloatingPointGeoPoint;
import net.peterd.zombierun.util.GeoPointUtil;

public class Player implements LocationListener, GameEventListener {

  private FloatingPointGeoPoint location;
  private final Destination destination;
  private final int playerId;
  private final GameEventBroadcaster gameEventBroadcaster;
  
  /**
   * Construct a player.
   * 
   * @param destination The game's destination.
   * @param playerId The player's id, 0-indexed.
   * @param location The player's location, possibly null.
   * @param onReachDestinationRunnable The {@link Runnable} that should be run when the player
   *    reaches the destination.
   */
  public Player(Destination destination,
      int playerId,
      FloatingPointGeoPoint location,
      GameEventBroadcaster gameEventBroadcaster) {
    this.destination = destination;
    this.playerId = playerId;
    this.location = location;
    this.gameEventBroadcaster = gameEventBroadcaster;
  }
  
  /**
   * Get the player's current location.
   * 
   * @return The player's current location, possibly null.
   */
  public FloatingPointGeoPoint getLocation() {
    return location;
  }
  
  /**
   * Serialize the player to a string.
   */
  @Override
  public String toString() {
    if (location != null) {
      return playerId + ":" + location.toString();
    } else {
      return Integer.toString(playerId);
    }
  }

  /**
   * @throws IllegalArgumentException if there are any parsing errors. 
   */
  public static Player fromString(String serializedPlayer,
      Destination destination,
      GameEventBroadcaster gameEventBroadcaster) {
    String[] splits = serializedPlayer.split(":", 2);
    String playerIdString;
    String locationString;
    if (splits.length == 2) {
      playerIdString = splits[0];
      locationString = splits[1];
    } else if (splits.length == 1) {
      playerIdString = splits[0];
      locationString = null;
    } else {
      throw new IllegalArgumentException(
          "Could not split serialized player into one or two parts.");
    }
    
    int playerId;
    try {
      playerId = Integer.parseInt(playerIdString);
    } catch (NumberFormatException e) {
      throw new IllegalArgumentException(
          "Could not parse player id from string '" + serializedPlayer + "'.", e);
    }
    
    FloatingPointGeoPoint location = null;
    if (locationString != null) {
      // May return null.  That's okay, by the semantics of the Player constructor.
      location = FloatingPointGeoPoint.fromString(locationString);
    }
    
    return new Player(destination, playerId, location, gameEventBroadcaster);
  }

  public void setLocation(FloatingPointGeoPoint location) {
    if (location != null) {
      this.location = location;
      Log.d("ZombieRun.Player", "Player location updated to " + this.location);
      if (GeoPointUtil.distanceMeters(this.location, destination.getLocation()) <
              Constants.reachDestinationTestDistanceMeters) {
        gameEventBroadcaster.broadcastEvent(GameEvent.PLAYER_REACHES_DESTINATION);
      }
    } else {
      Log.w("ZombieRun.Player", "Player location attempted to be set to null.");
    }
  }
  
  public void onLocationChanged(Location location) {
    setLocation(new FloatingPointGeoPoint(GeoPointUtil.fromLocation(location)));
  }

  public void onProviderDisabled(String provider) { }
  public void onProviderEnabled(String provider) { }
  public void onStatusChanged(String provider, int status, Bundle extras) { }

  public void receiveEvent(GameEvent event) {
    // Currently a no-op.
  }
  
  public static class PlayerListSerializer {
    
    public static String toString(List<Player> players) {
      StringBuilder builder = new StringBuilder();
      for (Player player : players) {
        builder.append(player.toString());
        builder.append("\n");
      }
      return builder.toString();
    }

    public static List<Player> fromString(
        String encodedString,
        Destination destinationReference,
        GameEventBroadcaster gameEventBroadcaster) {
      List<Player> players = new ArrayList<Player>();
      String[] lines = encodedString.split("\n");
      for (int i = 0; i < lines.length; ++i) {
        Player player = Player.fromString(lines[i], destinationReference, gameEventBroadcaster);
        if (player != null) {
          players.add(player);
        }
      }
      return players;
    }
  }
}
