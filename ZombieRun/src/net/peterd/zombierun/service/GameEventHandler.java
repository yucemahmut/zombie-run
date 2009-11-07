package net.peterd.zombierun.service;

import java.util.HashSet;
import java.util.Set;

import net.peterd.zombierun.game.GameEvent;

import net.peterd.zombierun.util.Log;

public class GameEventHandler implements GameEventBroadcaster {

  private final Set<GameEventListener> listeners = new HashSet<GameEventListener>();

  public boolean addListener(GameEventListener listener) {
    Log.d("ZombieRun.GameEventHandler", "Adding GameEventListener " + listener.toString());
    return listeners.add(listener);
  }
  
  public boolean removeListener(GameEventListener listener) {
    Log.d("ZombieRun.GameEventHandler", "Removing GameEventListener " + listener.toString());
    return listeners.remove(listener);
  }
  
  public void clearListeners() {
    Log.d("ZombieRun.GameEventHandler", "Clearing GameEventListeners.");
    listeners.clear();
  }
  
  public void broadcastEvent(GameEvent event) {
    int severity = android.util.Log.INFO;
    if (event == GameEvent.UPDATED_PLAYER_LOCATIONS ||
        event == GameEvent.UPDATED_ZOMBIE_LOCATIONS) {
      severity = android.util.Log.DEBUG;
    }
    Log.println(severity, "ZombieRun.GameEventHandler", "Broadcasting event " + event.name());
    
    for (GameEventListener listener : listeners) {
      listener.receiveEvent(event);
    }
  }
}
