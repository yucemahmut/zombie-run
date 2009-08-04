
// Player constructor.
//
// map is the google.maps.Map on which this player will be drawn
// location is a google.maps.LatLng
function Player(map, location) {
  this._map = map;
  this._location = location;

  var markerimage = new google.maps.MarkerImage(
      "res/icon.png",
      new google.maps.Size(48, 48));
  this._marker = new google.maps.Marker({
      position:location,
      map:map,
      title:"You",
      icon:markerimage,
      // TODO: shadow image.
    });
}

Player.prototype.locationChanged = function(position) {
  this._location = latLngFromPosition(position);
  this._marker.set_position(this._location);
}