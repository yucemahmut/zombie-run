package net.peterd.zombierun.activity;

import android.os.Bundle;
import net.peterd.zombierun.constants.BundleConstants;
import net.peterd.zombierun.entity.Destination;
import net.peterd.zombierun.service.GameService;

public class MultiPlayerGame extends Game {

  @Override
  protected void createGame(GameService service, Destination destination) {
    final GameService localService = this.service;
    final Bundle extras = getIntent().getExtras();
    new Thread(new Runnable() {
        public void run() {
          localService.joinMultiPlayerGame(extras.getInt(BundleConstants.GAME_ID));
        }
      }).start();
    
  }
}
