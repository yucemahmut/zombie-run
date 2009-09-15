var Game = Class.create({
  initialize: function(map, num_zombies) {
    this.map = map;
    this.num_zombies = num_zombies;
    this.first_location_fixed = false;
    this.zombies = new Array;
    this.players = new Array;
  },
  
  // start the game -- initialize location services.
  start: function() {
    console.log("start");
    this.locationProvider = new LocationProvider();
    this.locationProvider.addListener(this);
    return;
    
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
  
  locationUpdate: function(location) {
    console.log("first location: " + location);
    this.locationProvider.removeListener(this);

    if (this.first_location_fixed) {
      throw "Invalid state -- Game should receive only one location update, then remove itself.";
    }    
    this.first_location_fixed = true;
  
    this.player = new Player(this.map, location);
    this.locationProvider.addListener(this.player);
    this.players.push(this.player);
  
    this.map.set_center(location);
    this.map.set_zoom(15);
    
    this.destinationPickClickListener =
        google.maps.event.addListener(this.map, "click", this.locationSelected.bind(this));
  },
  
  locationSelected: function(mouseEvent) {
    var latLng = mouseEvent.latLng;
    console.log("locationSelected: " + latLng);
    if (this.destination) {
      this.destination.locationUpdate(latLng);
    } else {
      this.destination = new Destination(this.map, latLng);
    }
    // TODO: do a better confirmation dialog.
    if (confirm("Right destination?")) {
      google.maps.event.removeListener(this.destinationPickClickListener);
      this.destinationConfirmed();
    }
  },
  
  destinationConfirmed: function() {
    var pLoc = this.player.getLocation();
    var dLoc = this.destination.getLocation();
    var dst = distance(pLoc, dLoc);
    var centerLoc = latLngTowardTarget(pLoc, dLoc, dst / 2);
    console.log("center: " + centerLoc);
    
    for (i = 0; i < this.num_zombies; i++) {
      var zombieLoc = randomLatLngNearLocation(centerLoc, Math.random() * dst * 2);
      var zombie = new Zombie(this.map, zombieLoc, this.players, 0.5, 100);
      this.zombies.push(zombie);
    }
  },
});
