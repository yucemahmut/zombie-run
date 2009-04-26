package net.peterd.zombierun.activity;

import net.peterd.zombierun.R;
import net.peterd.zombierun.game.GameSettings;
import net.peterd.zombierun.util.GeoCalculationUtil;
import android.app.Activity;
import android.widget.Spinner;

public class Util {

  public static GameSettings handleGameSettings(Activity activity,
      boolean startingMultiplayerGame) {
    Spinner zombieSpeedSpinner = (Spinner) activity.findViewById(R.id.spinner_zombie_speed);
    int indexOfSpeed = zombieSpeedSpinner.getSelectedItemPosition();
    double zombieSpeedMph = Double.parseDouble(
        activity.getResources().getStringArray(
            R.array.zombie_speeds_average_speed_mph)[indexOfSpeed]);
    double zombieSpeed = GeoCalculationUtil.milesPerHourToMetersPerSecond(zombieSpeedMph);
    
    Spinner zombieCountSpinner = (Spinner) activity.findViewById(R.id.spinner_zombie_count);
    int indexOfDensity = zombieCountSpinner.getSelectedItemPosition();
    double averageDistanceBetweenZombiesMeters = Double.parseDouble(
        activity.getResources().getStringArray(
            R.array.zombie_counts_average_distance_between_zombie_meters)[indexOfDensity]);
    double zombieDensity =
        GeoCalculationUtil.itemPerDistanceToItemsPerSquareKilometer(
            averageDistanceBetweenZombiesMeters);
    
    return new GameSettings(zombieDensity, zombieSpeed, startingMultiplayerGame);
  }
}
