var Player = Class.create({
  initialize: function(map, location) {
    this.map = map;
    this.location = location;
    
    var markerimage = new google.maps.MarkerImage(
        "res/icon.png",
        new google.maps.Size(48, 48));
    this.marker = new google.maps.Marker({
        position:this.location,
        map:this.map,
        title:"You",
        icon:markerimage,
        // TODO: shadow image.
      });
  },
  
  locationChanged: function(latLng) {
    this.location = latLng;
    this.marger.set_position(this.location);
  }
});