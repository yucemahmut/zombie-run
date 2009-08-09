var Zombie = Class.create({
  initialize: function(map, location) {
    this.map = map;
    this.location = location;
    
    var markerimage = new google.maps.MarkerImage(
        "res/zombie_meandering.png",
        new google.maps.Size(14, 30));
    this.marker = new google.maps.Marker({
        position:this.location,
        map:this.map,
        title:"Zombie",
        icon:markerimage,
        // TODO: shadow image.
      });
  },
  
  locationChanged: function(latLng) {
    this.location = latLng;
    this.marger.set_position(this.location);
  }
});