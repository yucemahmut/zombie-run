package net.peterd.zombierun.activity;

import java.util.concurrent.atomic.AtomicReference;

import com.google.android.maps.GeoPoint;
import com.google.android.maps.MapView;
import com.google.android.maps.Overlay;

import net.peterd.zombierun.R;
import net.peterd.zombierun.constants.Constants;
import net.peterd.zombierun.constants.Constants.GAME_MENU_OPTION;
import net.peterd.zombierun.entity.Destination;
import net.peterd.zombierun.overlay.DestinationOverlay;
import net.peterd.zombierun.service.HardwareManager;
import net.peterd.zombierun.util.FloatingPointGeoPoint;
import android.app.Activity;
import android.app.AlertDialog;
import android.content.DialogInterface;
import android.content.Intent;
import android.graphics.Canvas;
import android.graphics.drawable.Drawable;
import android.location.Location;
import android.location.LocationListener;
import android.os.Bundle;
import net.peterd.zombierun.util.Log;
import android.view.KeyEvent;
import android.widget.TextView;

public class StartGame extends Activity {

  /**
   * Simply route to the first sub-activity.  This is defined here only so that we can have a
   * consistent entry-point to the start-game set of activities.
   */
  public void onCreate(Bundle state) {
    super.onCreate(state);
    Intent intent = new Intent(this, WaitingForFirstFixActivity.class);
    intent.putExtras(getIntent().getExtras());
    startActivity(intent);
  }
  
  public static class BaseStartGameActivity extends GameMapActivity implements LocationListener {
    protected final AtomicReference<Destination> destinationReference =
        new AtomicReference<Destination>();
    protected Drawable destinationDrawable;
    protected Location currentLocation;

    public BaseStartGameActivity() {
      menuOptions.add(GAME_MENU_OPTION.MAP_VIEW);
      menuOptions.add(GAME_MENU_OPTION.MY_LOCATION);
      menuOptions.add(GAME_MENU_OPTION.SATELLITE_VIEW);
      menuOptions.add(GAME_MENU_OPTION.STOP);
    }

    @Override
    public void onCreate(Bundle state) {
      super.onCreate(state);
      
      service.getHardwareManager().registerLocationListener(this);

      destinationDrawable = getResources().getDrawable(R.drawable.flag);
      Drawable destinationDrawable = this.destinationDrawable;
      destinationDrawable.setBounds(0, 0,
          destinationDrawable.getIntrinsicHeight(),
          destinationDrawable.getIntrinsicHeight());
      
      if (state != null) {
        onRestoreInstanceState(state);
      }

      Intent intent = getIntent();
      if (intent != null) {
        Bundle extras = intent.getExtras();
        if (extras != null) {
          Log.i("ZombieRun.BaseStartGameActivity", "Setting Destination from intent extras.");
          destinationReference.set(Destination.fromBundle(extras));
        }
      }
      
      mapView.getOverlays().add(
          new DestinationOverlay(destinationReference, this.destinationDrawable));
    }
    
    @Override
    public boolean onKeyDown(int keyCode, KeyEvent event) {
      if (keyCode == KeyEvent.KEYCODE_BACK) {
        startActivity(new Intent(this, Main.class));
        return true;
      }
      return false;
    }
    
    @Override
    public void onSaveInstanceState(Bundle state) {
      super.onSaveInstanceState(state);
      Destination destination = destinationReference.get();
      if (destination != null) {
        Log.i("ZombieRun.BaseStartGameActivity", "Putting Destination to activity bundle.");
        destination.toBundle(state);
      }
    }

    @Override
    public void onRestoreInstanceState(Bundle state) {
      super.onSaveInstanceState(state);
      Log.i("ZombieRun.BaseStartGameActivity", "Getting Destination from activity bundle.");
      destinationReference.set(Destination.fromBundle(state));
    }
    
    @Override
    public void startActivity(Intent intent) {
      Destination destination = destinationReference.get();
      Bundle bundle = new Bundle();
      if (destination != null) {
        Log.i("ZombieRun.BaseStartGameActivity", "Putting Destination to intent extras.");
        destination.toBundle(bundle);
      }
      gameSettings.toBundle(bundle);
      intent.putExtras(bundle);
      service.shutDown();
      super.startActivity(intent);
    }
    
    @Override
    public void onStop() {
      super.onStop();
    }
    
    public void onLocationChanged(Location location) {
      currentLocation = location;
    }

    public void onProviderDisabled(String provider) { }
    public void onProviderEnabled(String provider) { }
    public void onStatusChanged(String provider, int status, Bundle extras) { }
  }

  public static class WaitingForFirstFixActivity extends BaseStartGameActivity {
    
    @Override
    public void onCreate(Bundle state) {
      super.onCreate(state);

      // The Intent that will take us back to the main screen.
      final Intent cancelIntent = new Intent(this, Main.class);
      WaitingForLocationDialogView waitingForLocationDialogView =
          new WaitingForLocationDialogView(this, service.getHardwareManager());
      new AlertDialog.Builder(this)
          .setView(waitingForLocationDialogView)
          .setNegativeButton("Cancel", new DialogInterface.OnClickListener() {
                public void onClick(DialogInterface dialog, int which) {
                  startActivity(cancelIntent); 
                }
              })
          .setOnCancelListener(new DialogInterface.OnCancelListener() {
                public void onCancel(DialogInterface dialog) {
                  startActivity(cancelIntent); 
                }
              })
          .show();
    }
    
    @Override
    public void onLocationChanged(Location location) {
      super.onLocationChanged(location);
      startActivity(new Intent(this, ShowingPickDestinationMessageActivity.class));
    }
  }
  
  public static class ShowingPickDestinationMessageActivity extends BaseStartGameActivity {
    @Override
    public void onCreate(Bundle state) {
      super.onCreate(state);
      
      mapView.getController().animateTo(
          service.getHardwareManager().getLastKnownLocation().getGeoPoint());
      mapView.getController().setZoom(15);
      
      final Intent beginPickingDestinationIntent =
          new Intent(this, PickingDestinationActivity.class);
      new AlertDialog.Builder(this)
          .setMessage(R.string.message_pick_destination)
          .setPositiveButton("OK", new DialogInterface.OnClickListener() {
                public void onClick(DialogInterface dialog, int which) {
                  startActivity(beginPickingDestinationIntent);
                }
              })
          .show();
    }
  }
  
  public static class PickingDestinationActivity extends BaseStartGameActivity {

    @Override
    public void onCreate(Bundle state) {
      super.onCreate(state);
      mapView.getOverlays().add(new DestinationPickingOverlay(this));
    }
    
    protected void destinationChosen(Destination destination) {
      destinationReference.set(destination);
      
      final Intent startGameIntent;
      if (gameSettings.getIsMultiplayerGame()) {
        startGameIntent = new Intent(this, OwnedMultiPlayerGame.class);
      } else {
        startGameIntent = new Intent(this, SinglePlayerGame.class);
      }
      
      new AlertDialog.Builder(this)
          .setMessage(R.string.message_confirm_destination)
          .setPositiveButton("Yes", new DialogInterface.OnClickListener() {
                public void onClick(DialogInterface dialog, int which) {
                  startActivity(startGameIntent);
                }
              })
          .setNegativeButton("No", new DialogInterface.OnClickListener() {
                public void onClick(DialogInterface dialog, int which) {
                  // Do nothing, just let another destination be chosen.
                }
              })
          .show();
    }
    
    private static class DestinationPickingOverlay extends Overlay {
      
      private final PickingDestinationActivity activity;
      
      public DestinationPickingOverlay(PickingDestinationActivity activity) {
        this.activity = activity;
      }
      
      @Override
      public boolean onTap(GeoPoint point, MapView map) {
        super.onTap(point, map);
        activity.destinationChosen(new Destination(new FloatingPointGeoPoint(point)));
        return true;
      }
    }
  }
  
  private static class WaitingForLocationDialogView extends TextView implements LocationListener {
    
    private final Activity activity;
    private final HardwareManager hardwareManager;
    private Location location;
    
    public WaitingForLocationDialogView(Activity activity,
        HardwareManager hardwareManager) {
      super(activity);
      this.activity = activity;
      this.hardwareManager = hardwareManager;
    }
    
    @Override
    public void onDraw(Canvas canvas) {
      String message = activity.getString(R.string.waiting_for_location);
      if (location != null) {
        message += "  Current location is accurate to " + location.getAccuracy() + " meters.";
      }
      message += "  Waiting for a location accurate to " + Constants.minDeviceAccuracyMeters +
          " meters.";
      setText(message);
      setPadding(5, 5, 5, 5);
      super.onDraw(canvas);
    }

    @Override
    protected void onAttachedToWindow() {
      hardwareManager.registerLocationListener(this);
    };
    
    @Override
    protected void onDetachedFromWindow() {
      hardwareManager.removeLocationListener(this);
    }
    
    public void onLocationChanged(Location location) {
      this.location = location;
      this.postInvalidate();
    }
    public void onProviderDisabled(String provider) { }
    public void onProviderEnabled(String provider) { }
    public void onStatusChanged(String provider, int status, Bundle extras) { }
  }
}
