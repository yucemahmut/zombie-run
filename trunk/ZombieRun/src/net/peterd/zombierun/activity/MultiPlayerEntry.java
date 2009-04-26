package net.peterd.zombierun.activity;

import net.peterd.zombierun.R;
import net.peterd.zombierun.game.GameSettings;
import net.peterd.zombierun.util.GeoCalculationUtil;
import android.app.Activity;
import android.content.Context;
import android.content.Intent;
import android.os.Bundle;
import android.view.View;
import android.widget.Button;
import android.widget.Spinner;

public class MultiPlayerEntry extends Activity {
  
  @Override
  public void onCreate(Bundle state) {
    super.onCreate(state);
    setContentView(R.layout.multiplayer_entry);
    
    ((Button) findViewById(R.id.button_start_multiplayer)).setOnClickListener(
        new View.OnClickListener() {
          public void onClick(View v) {
            startNewMultiplayerGame();
          }
        });
    final Context context = this;
    ((Button) findViewById(R.id.button_join_multiplayer)).setOnClickListener(
        new View.OnClickListener() {
          public void onClick(View v) {
            startActivity(new Intent(context, JoinMultiPlayerGame.class));
          }
        });
  }
  
  private void startNewMultiplayerGame() {
    Bundle bundle = new Bundle();
    GameSettings settings = Util.handleGameSettings(this, true);
    settings.toBundle(bundle);
    
    Intent startGameIntent = new Intent(this, StartGame.class);
    startGameIntent.putExtras(bundle);
    startActivity(startGameIntent);
  }
}
