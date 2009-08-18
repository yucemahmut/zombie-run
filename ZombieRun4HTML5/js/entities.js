// Note: the markers do not show up in Android.
var Entity = Class.create({
  initialize: function(map, location) {
    this.map = map;
    this.location = location;
    this.marker = this.getMarker(this.map, this.location);
  },
  
  getMarker: function(map, latLng) {
    alert("please override me.");
  },
  
  locationUpdate: function(location) {
    console.log(this + ".locationUpdate(" + location + ")");
    this.location = location;
    this.marker.set_position(this.location);
  },
  
  getLocation: function() {
    return this.location;
  },
});

// Note: for some reason the Player marker seems to disappear on Firefox 3.5 when it receives
// a locationUpdate.
var Player = Class.create(Entity, {
  getMarker: function(map, latLng) {
    var markerimage = new google.maps.MarkerImage(
        "res/icon.png",
        new google.maps.Size(48, 48));
    return new google.maps.Marker({
        position:latLng,
        map:map,
        title:"You",
        icon:markerimage,
        // TODO: shadow image.
      });
  },
});

var Zombie = Class.create(Entity, {
  initialize: function($super, map, location, players, speed, visionDistance) {
    $super(map, location);
    console.log("Zombie! (" + location + ")");
    this.players = players;  // the players in the game.
    this.speed = speed;  // meters per second
    this.visionDistance = visionDistance;  // the distance this zombie can see, in meters.
  },
  
  getMarker: function(map, latLng) {
    var markerimage = new google.maps.MarkerImage(
        "res/zombie_meandering.png",
        new google.maps.Size(14, 30));
    return new google.maps.Marker({
        position:latLng,
        map:map,
        title:"Zombie",
        icon:markerimage,
        // TODO: shadow image.
      });
  },
  
  advance: function(timeElapsed) {
    console.log("advance(" + timeElapsed + ") with " + this.players.length + " players.");
    
    // Yeah, this isn't what we actually want to do.
    if (this.players.length > 0) {
      this.moveTowardPlayer(this.players[0]);
    }
  },
  
  isNoticingPlayer: function(player) {
    return distance(this.location, player.getLocation()) < this.visionDistance;
  },
  
  meander: function(timeElapsed) {
    // move in some random direction
    // todo: move in packs, in a more defined direction.
    var distanceMoved = timeElapsed * this.speed;
  },
  
  moveTowardPlayer: function(player, timeElapsed) {
    var distanceToPlayer = distance(this.location, player.getLocation());
    var distanceMoved = Math.min(timeElapsed * this.speed, distanceToPlayer);
    this.locationUpdate(latLngTowardTarget(this.location, player.getLocation(), distanceMoved));
  },
});

var Destination = Class.create(Entity, {
  getMarker: function(map, latLng) {
    var markerimage = new google.maps.MarkerImage(
        "res/flag.png",
        new google.maps.Size(62, 35));
    return new google.maps.Marker({
        position:latLng,
        map:map,
        title:"Destination",
        icon:markerimage,
        // TODO: shadow image.
      });
  },
});