// map is the google.maps.Map on which this game will be drawn
function Game(map) {
  var map = map;
  var first_location_fixed = false;
  var player = false;
  var zombies = false;
  
  this.firstLocation = function(position) {
    var location = latLngFromPosition(position);
  
    player = new Player(map, location);
  
    var zombieLatLng = latLngTowardTarget(location, new google.maps.LatLng(100, 100), 50);
    zombies = new Array();
    zombies[0] = new Zombie(map, zombieLatLng);
    
    map.set_center(location);
    map.set_zoom(15);
    
    first_location_fixed = true;
  }
  
  this.locationChanged = function(position) {
    if (!first_location_fixed) {
      return;
    }
    player.locationChanged(position);
    for (var i; i < zombies.length; ++i) {
      zombies[i].locationChanged(position);
    }
  }
  
  this.locationError = function(error) {
    // TODO: Count errors, if there are enough then show the user an issue.
    alert("location error: " + error.message);
  }
  
  this.initialize = function() {
    // Get our intial position, and initialize the map at that point.
    navigator.geolocation.getCurrentPosition(
        this.firstLocation,
        this.locationError,
        { enableHighAccuracy:true, maximumAge:0, timeout:0 });
  
    // Get updates of the user's location at least every 10 seconds.
    navigator.geolocation.watchPosition(
        this.locationChanged,
        this.locationError,
        { enableHighAccuracy:true, maximumAge: 10 * 1000, timeout:0 });
  }
}
