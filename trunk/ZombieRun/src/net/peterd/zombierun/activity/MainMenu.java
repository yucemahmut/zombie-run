package net.peterd.zombierun.activity;

import net.peterd.zombierun.R;
import net.peterd.zombierun.constants.ApplicationConstants;
import net.peterd.zombierun.io.NetworkDataFetcher;
import net.peterd.zombierun.io.UpdateChecker;
import net.peterd.zombierun.service.HardwareManager;
import android.app.AlertDialog;
import android.content.DialogInterface;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.os.Looper;
import android.provider.Settings;
import android.view.KeyEvent;
import net.peterd.zombierun.util.Log;

public abstract class MainMenu extends BaseActivity {
  
  @Override
  public void onCreate(Bundle state) {
    super.onCreate(state);
    if (state != null) {
      onRestoreInstanceState(state);
    }
    setupMainLayout();
    beginCheckingForUpdate();
    testForHardwareCapabilitiesAndShowAlert();
  }
  
  /**
   * Setup the layout and handle all UI elements.
   */
  protected abstract void setupMainLayout();
  
  protected boolean mayStartGame() {
    return testForHardwareCapabilities();
  }
  
  /**
   * Returns true if all the hardware was properly initialized. 
   */
  protected boolean testForHardwareCapabilitiesAndShowAlert() {
    // TODO: Use the actual error message, so that we can determine which of the hardware is
    // disabled or absent.
    if (!testForHardwareCapabilities()) {
      showEnableGPSAlert();
      return false;
    }
    return true;
  }
  
  /**
   * @return true if all the hardware was properly initialized.
   */
  private boolean testForHardwareCapabilities() {
    // TODO: Use the actual error message, so that we can determine which of the hardware is
    // disabled or absent.
    HardwareManager hardwareManager = new HardwareManager(this);
    Integer errorMessage = hardwareManager.initializeHardware();
    if (errorMessage != null) {
      return false;
    }
    return true;
  }
  
  @Override
  public boolean onKeyDown(int keyCode, KeyEvent event) {
    if (keyCode == KeyEvent.KEYCODE_BACK) {
      Intent mainScreenIntent = new Intent(Intent.ACTION_MAIN);
      mainScreenIntent.addCategory(Intent.CATEGORY_HOME);
      startActivity(mainScreenIntent);
    }
    return false;
  }
  
  private void beginCheckingForUpdate() {
    final UpdateChecker updateChecker =
        new UpdateChecker(
            ApplicationConstants.applicationVersionCheckUrl,
            ApplicationConstants.currentVersionCode,
            new NetworkDataFetcher());
    final Runnable checkForUpdateRunnable = new Runnable() {
        public void run() {
          Looper.prepare();
          try {
            if (updateChecker.checkForUpdate()) {
              if (updateChecker.newVersionIsAvailable()) {
                Log.i("ZombieRun.MainMenu", "New market update found.  Showing update dialog.");
                showNewUpdateAvailableAlert(
                    updateChecker.getField(UpdateChecker.FIELD.APPLICATION_ID));
              } else {
                Log.i("ZombieRun.MainMenu", "No market update available.");
              }
            }
          } catch (Exception e) {
            Log.e("ZombieRun.MainMenu", "Uncaught Exception while checking for new version.", e);
            return;
          }
          Looper.loop();
        }
      };
    Thread checkForUpdateThread = new Thread(checkForUpdateRunnable);
    checkForUpdateThread.start();
  }
  
  private void showNewUpdateAvailableAlert(final String marketApplicationId) {
    new AlertDialog.Builder(this)
        .setMessage(R.string.update_available)
        .setPositiveButton(R.string.do_update,
            new DialogInterface.OnClickListener() {
              public void onClick(DialogInterface dialog, int which) {
                Uri applicationMarketUri = Uri.parse("market://details?id=" + marketApplicationId);
                Intent openMarketIntent = new Intent(Intent.ACTION_VIEW, applicationMarketUri);
                startActivity(openMarketIntent);
              }
            })
        .setNegativeButton(R.string.remind_me_later,
            new DialogInterface.OnClickListener() {
              public void onClick(DialogInterface dialog, int which) { }
            })
        .show();
  }
  
  private void showEnableGPSAlert() {
    new AlertDialog.Builder(this)
        .setMessage(R.string.error_gps_disabled)
        .setPositiveButton(R.string.enable_gps,
            new DialogInterface.OnClickListener() {
              public void onClick(DialogInterface dialog, int which) {
                startActivity(new Intent(Settings.ACTION_LOCATION_SOURCE_SETTINGS));
              }
            })
        .show();
  }
}
