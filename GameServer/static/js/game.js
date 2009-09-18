var Game = Class.create({
  initialize: function(map) {
    this.map = map;
    this.location = false;
    this.game_data = new Object;
    this.zombies = new Array;
    this.players = new Array;
    this.updating = false;
    
    this.game_id = false;
    this.num_zombies = false;
    this.average_zombie_speed = false;
    this.created = false;
    this.joined = false;
  },
  
  joinGame: function(game_id) {
    this.joined = true;
    this.game_id = game_id;
  },
  
  createGame: function(num_zombies, average_zombie_speed) {
    this.created = true;
    this.game_id = false;
    this.num_zombies = num_zombies;
    this.average_zombie_speed = average_zombie_speed;
  },
  
  // start the game -- initialize location services.
  start: function() {
    this.locationProvider = new LocationProvider();
    if (!this.locationProvider.addListener(this)) {
      return false;
    }
    
    request_options = {
        method: 'get',
        onSuccess: this.gameUpdate.bind(this)
      };
    
    if (this.created) {
      // Create game.
      new Ajax.Request('/rpc/create', request_options);
    } else {
      // Join game.
      request_options.parameters = { gid: this.game_id };
      new Ajax.Request('/rpc/join', request_options);
    }
    
    setInterval(this.update.bind(this), 5000);
    return true;
  },
  
  gameUpdate: function(transport) {
    var json = eval('(' + transport.responseText + ')');
    if (json) {
      this.game_data = json;
      this.game_id = this.game_data.game_id;
    }
    this.updating = false;
    this.draw();
  },
  
  failedGameUpdate: function() {
    this.updating = false;
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
  
  request: function(url, parameters) {
    new Ajax.Request(url,
      {
        method: 'get',
        parameters: parameters,
        onSuccess: this.gameUpdate.bind(this),
        onFailure: this.failedGameUpdate.bind(this),
      });
  },
  
  draw: function() {
    for (i = 0; i < this.game_data.zombies.length; ++i) {
      zombie = this.game_data.zombies[i];
      latLng = new google.maps.LatLng(zombie.lat, zombie.lon);
      isNoticingPlayer = zombie.chasing != null;
      if (i < this.zombies.length) {
        this.zombies[i].locationUpdate(latLng);
        this.zombies[i].setIsNoticingPlayer(isNoticingPlayer);
      } else {
        this.zombies[this.zombies.length] = new Zombie(this.map, latLng, isNoticingPlayer);
      }
    }
    
    for (i = 0; i < this.game_data.players.length; ++i) {
      player = this.game_data.players[i];
      latLng = new google.maps.LatLng(player.lat, player.lon);
      if (i < this.players.length) {
        this.players[i].locationUpdate(latLng);
      } else {
        this.players[this.players.length] = new Player(this.map, latLng);
      }
    }
    
    var destination_latlng = new google.maps.LatLng(
        this.game_data.destination.lat,
        this.game_data.destination.lon);
    if (this.destination) {
      this.destination.locationUpdate(destination_latlng);
      console.log("Updated existing Destination marker to " + destination_latlng);
    } else {
      this.destination = new Destination(this.map, destination_latlng);
      console.log("Set new Destination marker.");
    }
  },
  
  locationUpdate: function(location) {
    if (!this.location) {
      if (this.created) {
        this.destinationPickClickListener =
        google.maps.event.addListener(this.map,
            "click",
            this.locationSelected.bind(this));
      }
      this.map.set_center(location);
      this.map.set_zoom(15);
    }

    this.location = location;

    // Put location to the server.
    this.update();
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
            "num_zombies": this.num_zombies,
            "average_zombie_speed": "1"
          });
    }
  },
});
