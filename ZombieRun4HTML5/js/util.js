var kRadiusOfEarthMeters = 6378100;

// Takes the position object from the navigator's location services,
// returns a google.maps.LatLng
function latLngFromPosition(position) {
  return new google.maps.LatLng(position.coords.latitude,
                                position.coords.longitude);
}

// Convert degrees to radians.
function toRadians(degrees) {
  return degrees * Math.PI / 180;
}

// Distance, in meters, between points a and b
//
// a and b are both google.maps.LatLng
function distance(a, b) {
  // Haversine formula, from http://mathforum.org/library/drmath/view/51879.html
  dLat = a.lat() - b.lat();
  dLon = a.lng() - b.lng();
  var x = Math.pow(Math.sin(toRadians(dLat / 2)), 2) +
      Math.cos(toRadians(a.lat())) *
        Math.cos(toRadians(b.lat())) *
          Math.pow(Math.sin(toRadians(dLon / 2)), 2);
  var greatCircleDistance = 2 * Math.atan2(Math.sqrt(x), Math.sqrt(1-x));
  return kRadiusOfEarthMeters * greatCircleDistance;
}

// origin and target are google.maps.LatLng, distanceMeters is numeric
function latLngTowardTarget(origin, target, distanceMeters) {
  dLat = target.lat() - origin.lat();
  dLon = target.lng() - origin.lng();
  
  dist = distance(origin, target);
  offsetLat = dLat * distanceMeters / dist;
  offsetLng = dLon * distanceMeters / dist;
  return new google.maps.LatLng(origin.lat() + offsetLat, origin.lng() + offsetLng);
}