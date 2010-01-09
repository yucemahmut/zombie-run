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
  
  remove: function() {
    this.marker.setMap(null)
  },
  
  locationUpdate: function(location) {
    this.location = location;
    this.marker.setPosition(this.location);
  },
});

var Player = Class.create(Entity, {
  getMarker: function(map, latLng) {
    var markerimage = new google.maps.MarkerImage(
        "res/player.png",
        new google.maps.Size(16, 40));
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
  initialize: function($super, map, location, isNoticingPlayer) {
    this.meanderingIcon = new google.maps.MarkerImage(
        "res/zombie_meandering.png",
        new google.maps.Size(14, 30))
    this.chasingIcon = new google.maps.MarkerImage(
        "res/zombie_chasing.png",
        new google.maps.Size(14, 30))
    this.isNoticingPlayer = isNoticingPlayer;
    $super(map, location);
  },
  
  setIsNoticingPlayer: function(isNoticingPlayer) {
    this.isNoticingPlayer = isNoticingPlayer;
    if (this.isNoticingPlayer) {
      this.marker.setIcon(this.chasingIcon);
    } else {
      this.marker.setIcon(this.meanderingIcon);
    }
  },
  
  getMarker: function(map, latLng) {
    var markerimage =
        this.isNoticingPlayer ? this.chasingIcon : this.meanderingIcon;
    return new google.maps.Marker({
        position:latLng,
        map:map,
        title:"Zombie",
        icon:markerimage,
        // TODO: shadow image.
      });
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

var MyLocation = Class.create(Entity, {
  getMarker: function(map, latLng) {
    var markerimage = new google.maps.MarkerImage(
        "res/YourLocationDot.png",
        new google.maps.Size(16, 16),
        null,
        new google.maps.Point(8, 8));
    return new google.maps.Marker({
        position:latLng,
        map:map,
        title:"Destination",
        icon:markerimage,
        // TODO: shadow image.
      });
  },
});