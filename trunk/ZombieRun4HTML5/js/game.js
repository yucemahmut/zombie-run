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
  
  // position is the object returned to the method from the navigator.geoLocation.getCurrentPosition
  locationUpdate: function(location) {
    if (!this.first_location_fixed) {
      console.log("first location: " + location);
      // TODO: this is where removing a location listener would be useful.
      this.first_location_fixed = true;
    
      this.player = new Player(this.map, location);
      this.locationProvider.addListener(this.player);
    
      this.map.set_center(location);
      this.map.set_zoom(15);
      
      google.maps.event.addListener(this.map, "click", this.locationSelected.bind(this));
    }
  },
  
  locationSelected: function(mouseEvent) {
    var latLng = mouseEvent.latLng;
    console.log("locationSelected: " + latLng);
    if (this.destination) {
      this.destination.locationUpdate(latLng);
    } else {
      this.destination = new Destination(this.map, latLng);
    }
    // TODO: confirm destination.
  },
});
