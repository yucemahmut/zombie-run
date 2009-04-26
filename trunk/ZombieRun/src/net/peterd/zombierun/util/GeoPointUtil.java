package net.peterd.zombierun.util;

import net.peterd.zombierun.constants.Constants;

import com.google.android.maps.GeoPoint;

import android.location.Location;

public class GeoPointUtil {

  public static GeoPoint fromLocation(Location location) {
    return new GeoPoint((int) Math.round(location.getLatitude() * 1E6),
        (int) Math.round(location.getLongitude() * 1E6));
  }
  
  public static FloatingPointGeoPoint getGeoPointNear(FloatingPointGeoPoint origin,
      double distanceMeters) {
    FloatingPointGeoPoint directionalGeoPoint =
        new FloatingPointGeoPoint(Math.random() - 0.5 + origin.getLatitude(),
            Math.random() - 0.5 + origin.getLongitude());
    return geoPointTowardsTarget(origin, directionalGeoPoint, distanceMeters);
  }

  public static FloatingPointGeoPoint geoPointTowardsTarget(
      FloatingPointGeoPoint origin,
      FloatingPointGeoPoint target,
      double distanceMeters) {
    double diffLat = target.getLatitude() - origin.getLatitude();
    double diffLon = target.getLongitude() - origin.getLongitude();
    
    double diffMagnitudeMeters = distanceMeters(origin, target);
    double deltaLat = diffLat * (distanceMeters / diffMagnitudeMeters);
    double deltaLon = diffLon * (distanceMeters / diffMagnitudeMeters);
    
    return new FloatingPointGeoPoint(
        origin.getLatitude() + deltaLat,
        origin.getLongitude() + deltaLon);
  }
  
  public static double distanceMeters(GeoPoint gp1, GeoPoint gp2) {
    return distanceMeters(new FloatingPointGeoPoint(gp1), new FloatingPointGeoPoint(gp2));
  }
  
  public static double distanceMeters(FloatingPointGeoPoint gp1, GeoPoint gp2) {
    return distanceMeters(gp1, new FloatingPointGeoPoint(gp2));
  }
  
  public static double distanceMeters(GeoPoint gp1, FloatingPointGeoPoint gp2) {
    return distanceMeters(new FloatingPointGeoPoint(gp1), gp2);
  }
  
  public static double distanceMeters(FloatingPointGeoPoint gp1,
      FloatingPointGeoPoint gp2) {
    // Haversine formula, from http://mathforum.org/library/drmath/view/51879.html
    double dlon = gp2.getLongitude() - gp1.getLongitude();
    double dlat = gp2.getLatitude() - gp1.getLatitude();
    double a = Math.pow(Math.sin(Math.toRadians(dlat/2)), 2) +
        Math.cos(Math.toRadians(gp1.getLatitude())) *
        Math.cos(Math.toRadians(gp2.getLatitude())) *
        Math.pow(Math.sin(Math.toRadians(dlon / 2)), 2);
    double greatCircleDistance = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a)); 
    return Constants.radiusOfEarthMeters * greatCircleDistance;
  }
}
