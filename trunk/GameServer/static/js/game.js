var Game = Class.create({
  initialize: function(map, game_id) {
    this.map = map;
    this.location = false;
    this.game_data = new Object;
    this.zombies = new Array;
    this.players = new Array;
    this.updating = false;
    this.game_id = game_id;
    this.is_owner = false;
  },
  
  // start the game -- initialize location services.
  start: function() {
    this.locationProvider = new LocationProvider();
    if (!this.locationProvider.addListener(this)) {
      return false;
    }
    
    if (this.game_id) {
      this.request("/rpc/join", {"gid": this.game_id});
    }
    
    this.update();    
    setInterval(this.update.bind(this), 5000);
    return true;
  },
  
  update: function() {
    if (this.updating) {
      return;
    }
  
    this.updating = true;
    parameters = { 'gid': this.game_id };
    
    if (this.location) {
      parameters["lat"] = this.location.lat();
      parameters["lon"] = this.location.lng();
      this.request("/rpc/put", parameters);
    } else {
      this.request("/rpc/get", parameters);
    }
  },
  
  gameUpdate: function(transport) {
    var json = eval('(' + transport.responseText + ')');
    if (json) {
      this.game_data = json;
      this.game_id = this.game_data.game_id;
    }
    this.updating = false;

    this.is_owner = this.game_data.owner == this.game_data.player;
    this.draw();
  },
  
  failedGameUpdate: function() {
    this.updating = false;
  },
  
  request: function(url, parameters) {
    // Requests should try to include the bounds of the current viewport, so
    // that the server can include a restricted set of the data in its
    // response, to minimize network traffic.
    var bounds = null;
    if (this.map) {
      bounds = this.map.getBounds();
    }
    if (bounds) {
      parameters["swLat"] = bounds.getSouthWest().lat();
      parameters["swLon"] = bounds.getSouthWest().lng();
      parameters["neLat"] = bounds.getNorthEast().lat();
      parameters["neLon"] = bounds.getNorthEast().lng();
    }
     
    new Ajax.Request(url,
      {
        method: 'get',
        parameters: parameters,
        onSuccess: this.gameUpdate.bind(this),
        onFailure: this.failedGameUpdate.bind(this),
      });
  },
  
  draw: function() {
    // Update the location of all the Zombie icons
    if (!this.game_data.zombies) {
      this.game_data.zombies = [];
    } 
    while (this.zombies.length > this.game_data.zombies.length) {
      this.zombies.pop().remove();
    }
    for (i = 0; i < this.game_data.zombies.length; ++i) {
      zombie = this.game_data.zombies[i];
      latLng = new google.maps.LatLng(zombie.lat, zombie.lon);
      isNoticingPlayer = zombie.chasing != null;
      if (i < this.zombies.length) {
        this.zombies[i].locationUpdate(latLng);
        this.zombies[i].setIsNoticingPlayer(isNoticingPlayer);
      } else {
        this.zombies[this.zombies.length] =
            new Zombie(this.map, latLng, isNoticingPlayer);
      }
    }
    
    // Update the location of all the player icons
    if (!this.game_data.players) {
      this.game_data.players = [];
    }
    while (this.players.length > this.game_data.players.length - 1) {
      // game_data.players.length - 1 because we don't want to draw the current
      // user.
      this.players.pop().remove();
    }
    for (i = 0; i < this.game_data.players.length; ++i) {
      player = this.game_data.players[i];
      if (player.email == this.game_data.player) {
        // Don't draw the current user.  We show the current user's location
        // with a blue dot.
        continue;
      }
      
      latLng = new google.maps.LatLng(player.lat, player.lon);
      if (i < this.players.length) {
        this.players[i].locationUpdate(latLng);
      } else {
        this.players[this.players.length] = new Player(this.map, latLng);
      }
    }
    
    if (this.game_data.destination) {
      var destination_latlng = new google.maps.LatLng(
          this.game_data.destination.lat,
          this.game_data.destination.lon);
      if (this.destination) {
        this.destination.locationUpdate(destination_latlng);
      } else {
        this.destination = new Destination(this.map, destination_latlng);
      }
    }
  },
  
  locationUpdate: function(location) {
    if (!this.location) {
      this.map.set_center(location);
      this.map.set_zoom(15);
    }

    this.location = location;
    
    if (!this.locationMarker) {
      this.locationMarker = new MyLocation(this.map, this.location);
    } else {
      this.locationMarker.locationUpdate(this.location);
    }

    // Put location to the server.
    this.update();
    
    if (this.game_data &&
        !this.game_data.destination &&
        this.is_owner &&
        !this.destinationPickClickListener) {
      this.destinationPickClickListener =
          google.maps.event.addListener(this.map,
              "click",
              this.locationSelected.bind(this));
    }
  },
  
  locationSelected: function(mouseEvent) {
    var latLng = mouseEvent.latLng;
    if (this.destination) {
      this.destination.remove();
    }
    this.destination = new Destination(this.map, latLng);
    
    // TODO: do a better confirmation dialog.
    if (confirm("Right destination?")) {
      google.maps.event.removeListener(this.destinationPickClickListener);
      
      // TODO: on request failure, re-issue the RPC.
      this.request("/rpc/start",
          { 
            "gid": this.game_id,
            "lat": latLng.lat(),
            "lon": latLng.lng(),
          });
    }
  },
  
  addFriend: function() {
    var email = prompt("What is your friend's email?");
    new Ajax.Request("/rpc/addFriend",
      {
        method: 'get',
        parameters: { "gid": this.game_id,
                      "email": email },
        onSuccess: this.addFriendSuccess.bind(this),
        onFailure: this.addFriendFailed.bind(this),
      });
  },
  
  addFriendSuccess: function(transport) {
    alert("We've invited your friend!  Tell them to check their email soon.");
  },
  
  addFriendFailed: function() {
    alert("Failed to send an invitation to your friend.  Please try again.");
  },
});
