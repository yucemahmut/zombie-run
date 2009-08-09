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

// A LocationProvider, when created, requests periodic location updates continuously and provides
// them to all registered listeners.
//
// A listener should implement:
//   function locationUpdate(location);
// where location is of the type google.maps.LatLng
var LocationProvider = Class.create({
  initialize: function() {
    this.listeners = new Array;

    if (navigator.geolocation) {
      this.initializeW3CLocationUpdates();
    } else if (window.google && google.gears) {
      this.initializeGoogleGearsLocationUpdates();
    } else {
      // TODO: create a more unified notification and error system.
      alert("No location API.");
    }
  },

  addListener: function(listener) {
    this.listeners.push(listener);
  },

  // TODO: provide a removeListener method
  
  updateListeners: function(latLng) {
    this.listeners.each(function(listener) {
        listener.locationUpdate(latLng);
      });
  },
  
  
  //
  // W3C Location Handling
  //
  initializeW3CLocationUpdates: function() {
    console.log("Getting location updates from the W3C location API.");

    // Get our intial position, and initialize the map at that point.
    navigator.geolocation.getCurrentPosition(
        this.w3CLocationChanged.bind(this),
        this.w3CLocationError.bind(this),
        { enableHighAccuracy:true, maximumAge:0, timeout:0 });
  
    // Get updates of the user's location at least every 10 seconds.
    navigator.geolocation.watchPosition(
        this.w3CLocationChanged.bind(this),
        this.w3CLocationError.bind(this),
        { enableHighAccuracy:true, maximumAge: 10 * 1000, timeout:0 });
  },
  
  // position is the object returned to the method from the navigator.geoLocation.getCurrentPosition
  w3CLocationChanged: function(position) {
    var latLng = latLngFromPosition(position);
    console.log("w3CLocationChanged: " + latLng);
    this.updateListeners(latLng);
  },
  
  w3CLocationError: function(error) {
    console.log("locationError: " + error.message);
  },
  

  //
  // Google Gears Location Handling
  //
  initializeGoogleGearsLocationUpdates: function() {
    var geo = google.gears.factory.create('beta.geolocation');
    var options = { enableHighAccuracy: true };
    try {
      geo.getCurrentPosition(this.googleGearsLocationChanged.bind(this),
                             this.googleGearsLocationError.bind(this),
                             options);
      geo.watchPosition(this.googleGearsLocationChanged.bind(this),
                        this.googleGearsLocationError.bind(this),
                        options);
    } catch (e) {
      alert(e);
      return;
    }
  },
  
  googleGearsLocationChanged: function(position) {
    var latLng = new google.maps.LatLng(position.latitude, position.longitude);
    console.log("googleGearsLocationChanged: " + latLng);
    this.updateListeners(latLng);
  },
  
  googleGearsLocationError: function(error) {
    console.log("locationError: " + error.message);
  },
});