package net.peterd.zombierun.activity;

import net.peterd.zombierun.R;
import android.content.Context;
import android.content.Intent;
import android.view.View;
import android.widget.Button;

public class MainMenuWithMultiplayerEnabled extends MainMenu {
  
  /**
   * Set up the actions of the buttons in the main layout.
   */
  @Override
  protected void setupMainLayout() {
    setContentView(R.layout.main_multiplayer_enabled);
    final Context mainMenuActivity = this;
    
    ((Button) findViewById(R.id.button_start_singleplayer)).setOnClickListener(
        new View.OnClickListener() {
          public void onClick(View v) {
            if (testForHardwareCapabilitiesAndShowAlert()) {
              startActivity(new Intent(mainMenuActivity, SinglePlayerEntry.class));
            }
          }
        });
    
    ((Button) findViewById(R.id.button_start_multiplayer)).setOnClickListener(
        new View.OnClickListener() {
          public void onClick(View v) {
            if (testForHardwareCapabilitiesAndShowAlert()) {
              startActivity(new Intent(mainMenuActivity, MultiPlayerEntry.class));
            }
          }
        });
    
    Button helpButton = (Button) findViewById(R.id.button_help);
    final Intent showHelpIntent = new Intent(this, About.class);
    helpButton.setOnClickListener(new View.OnClickListener() {
        public void onClick(View v) {
          startActivity(showHelpIntent);
        }
      });
  }
}
