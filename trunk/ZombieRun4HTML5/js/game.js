var Game = Class.create({
  initialize: function(map, num_zombies) {
    this.map = map;
    this.num_zombies = num_zombies;
    this.first_location_fixed = false;
    this.zombies = new Array;
  },
  
  // start the game -- initialize location services.
  start: function() {
    console.log("start");
    // Get our intial position, and initialize the map at that point.
    navigator.geolocation.getCurrentPosition(
        this.firstLocation.bind(this),
        this.locationError.bind(this),
        { enableHighAccuracy:true, maximumAge:0, timeout:0 });
  
    // Get updates of the user's location at least every 10 seconds.
    navigator.geolocation.watchPosition(
        this.locationChanged.bind(this),
        this.locationError.bind(this),
        { enableHighAccuracy:true, maximumAge: 10 * 1000, timeout:0 });
  },
  
  // position is the object returned to the method from the navigator.geoLocation.getCurrentPosition
  locationChanged: function(position) {
    console.log("locationChanged: " + latLngFromPosition(position));
    if (!this.first_location_fixed) {
      return;
    }
    this.player.locationChanged(position);
    for (var i; i < this.zombies.length; ++i) {
      this.zombies[i].locationChanged(position);
    }
  },
  
  locationError: function(error) {
    console.log("locationError: " + error.message);
    // TODO: Count errors, if there are enough then show the user an issue.
    alert(error.message);
  },
  
  // position is the object returned to the method from the navigator.geoLocation.getCurrentPosition
  firstLocation: function(position) {
    var location = latLngFromPosition(position);
    console.log("firstLocation: " + location);
  
    this.player = new Player(this.map, location);
  
    this.map.set_center(location);
    this.map.set_zoom(15);
    
    first_location_fixed = true;
    
    google.maps.event.addListener(this.map, "click", this.locationSelected.bind(this));
  },
  
  locationSelected: function(mouseEvent) {
    var latLng = mouseEvent.latLng;
    console.log("locationSelected: " + latLng);
    if (this.destination) {
      this.destination.locationChanged(latLng);
    } else {
      this.destination = new Destination(this.map, latLng);
    }
    // confirm destination.
  },
});
