package net.peterd.zombierun.activity;

import net.peterd.zombierun.entity.Destination;
import net.peterd.zombierun.service.GameService;

public class OwnedMultiPlayerGame extends Game {

  @Override
  protected void createGame(GameService service, Destination destination) {
    final GameService localService = service;
    final Destination localDestination = destination;
    new Thread(new Runnable() {
        public void run() {
          localService.createMultiPlayerGame(
              localService.getHardwareManager().getLastKnownLocation(),
              localDestination,
              gameSettings);
        }
      }).start();
  }
}
