
// Zombie constructor.
//
// map is the google.maps.Map on which this player will be drawn
// location is a google.maps.LatLng
function Zombie(map, location) {
  this._map = map;
  this._location = location;
    
  var markerimage = new google.maps.MarkerImage(
      "res/zombie_meandering.png",
      new google.maps.Size(14, 30));
  this._marker = new google.maps.Marker({
      position:location,
      map:map,
      title:"Zombie",
      icon:markerimage,
      // TODO: shadow image.
    });
}

Zombie.prototype.locationChanged = function(position) {
  this._location = latLngFromPosition(position);
  this._marker.set_position(this._location);
}