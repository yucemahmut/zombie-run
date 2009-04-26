package net.peterd.zombierun.activity;

import net.peterd.zombierun.constants.ApplicationConstants;
import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;

public class Main extends Activity {
  
  @Override
  public void onCreate(Bundle state) {
    super.onCreate(state);
    if (ApplicationConstants.multiplayerEnabled) {
      startActivity(new Intent(this, MainMenuWithMultiplayerEnabled.class));
    } else {
      startActivity(new Intent(this, MainMenuWithMultiplayerDisabled.class));
    }
  }
}
