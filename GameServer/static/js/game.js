/**
 * The Game handles drawing, updating, and fetching the game state from the
 * game server.
 */
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
    
    this.failed_requests = 0;
  },
  
  // start the game -- initialize location services.
  start: function() {
    $("message").style.display = "block";
  
    this.locationProvider = new LocationProvider();
    if (!this.locationProvider.addListener(this)) {
      return false;
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
      // Compute messages that should be shown.
      var messages = [];
      for (var i = 0; i < Game.all_messages.length; ++i) {
        message = Game.all_messages[i];
        if (message.shouldShow(this.game_data, json)) {
          messages.push(message);
        }
      }
      
      // If there were any messages to show, then show them.
      if (messages.length > 0) {
        this.showMessages(messages, json);
      }
      
      // Update our game state.
      this.game_data = json;
      this.game_id = this.game_data.game_id;
    }

    // Note that we got a successful request through.
    this.failed_requests = 0;
    
    // This is our attempt at synchronization, because I don't understand those
    // issues in JavaScript.
    this.updating = false;

    this.is_owner = this.game_data.owner == this.game_data.player;

    // Draw the fucker.
    this.draw();
  },
  
  /**
   * Show an array of Messages.
   * 
   * @param messages: an array of AbstractMessage objects.
   * @param new_gamestate: The new game state, to be compared with
   *     this.game_data.  Will be used to calculate the message representation.
   */
  showMessages: function(messages, new_gamestate) {
    for (var i = 0; i < messages.length; ++i) {
      this.showMessage(messages[i], new_gamestate);
    }
  },
  
  /**
   * Show a single Message.
   * 
   * @param message: a single AbstractMessage object.
   * @param new_gamestate: The new game state, to be compared with
   *     this.game_data.  Will be used to calculate the message representation.
   */
  showMessage: function(message, new_gamestate) {
    var str = message.getMessage(this.game_data, new_gamestate);
    console.log("Game message: " + str);
    alert(str);
  },
  
  failedGameUpdate: function() {
    console.log("Failed request.");
    this.failed_requests += 1;
    
    if (this.failed_requests > 10) {
      showMessage(new TooManyFailedRequestsMessage(), null);
    }
      
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
    while (this.players &&
           this.players.length > 0 &&
           this.players.length > this.game_data.players.length - 1) {
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
      this.location = location;
      this.moveToCurrentLocation();
    } else {
      this.location = location;
    }

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
  
  moveToCurrentLocation: function() {
    this.map.setCenter(this.location);
    this.map.setZoom(15);
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
      
      // TODO: on request failure, re-issue this RPC.
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

Object.extend(Game, {
  all_messages: [],
});


/*
 * Game Messages
 */

var AbstractMessage = Class.create({
  /**
   * Determine whether or not this Message should be shown for this transition
   * between game states.
   * 
   * Return: true or false.
   */
  shouldShow: function(old_gamestate, new_gamestate) {
    return false;
  },
  
  /**
   * Get the string that this message should display.  Will only be called if
   * shouldShow(old_gamestate, new_gamestate) returns True.
   * 
   * Return: a string.
   */
  getMessage: function(old_gamestate, new_gamestate) {
    return "";  
  },
});

var TooManyFailedRequestsMessage = Class.create(AbstractMessage, {
  shouldShow: function(old_gamestate, new_gamestate) {
    return false;
  },
  
  getMessage: function(old_gamestate, new_gamestate) {
    return "There's been a problem connecting to central intelligence.  " +
        "Reinitializing systems.";
  },
});

var HumanInfectedMessage = Class.create(AbstractMessage, {
  shouldShow: function($super, ogs, ngs) {
    var ogs_num_infected = 0;
    if (!ogs.players) {
      return false;
    }
    
    for (var i = 0; i < ogs.players.length; ++i) {
      if (ogs.players[i].infected) {
        ogs_num_infected += 1;
      }
    }
    
    var ngs_num_infected = 0;
    for (var i = 0; i < ngs.players.length; ++i) {
      if (ngs.players[i].infected) {
        ngs_num_infected += 1;
      }
    }
    
    return ogs_num_infected < ngs_num_infected;
  },
  
  getMessage: function(ogs, ngs) {
    var newly_infected_players = [];
    for (var i = 0; i < ogs.players.length; ++i) {
      if (!ogs.players[i].infected && ngs.players[i].infected) {
        newly_infected_players.push(ngs.players[i].email);
      }
    }
    if (newly_infected_players.length == 1) {
      if (newly_infected_players[0] == ngs.player) {
    	return "You were just infected by a zombie!";
      } else {
        return newly_infected_players[0] + " was just infected by a zombie!";
      }
    } else {
      return newly_infected_players.join(", ") +
          " were just infected by zombies!";
    }
  }
});
Game.all_messages.push(new HumanInfectedMessage());

var PlayerJoinedGameMessage = Class.create(AbstractMessage, {
  shouldShow: function($super, ogs, ngs) {
	return ogs.started && this.getOtherNewPlayerNames(ogs, ngs).length > 0;
  },
  
  getMessage: function(ogs, ngs) {
	var new_players = this.getOtherNewPlayerNames(ogs, ngs);
    if (new_players.length == 1) {
      return new_players[0] + " just joined the game.";
    } else {
      return new_players.join(", ") + " have just joined the game.";
    }
  },
  
  /**
   * Get the names of the players that have joined the game since the last game
   * update, excluding the current player.
   */
  getOtherNewPlayerNames: function(ogs, ngs) {
    var new_players = [];
    var i = 0;
    if (ogs.players) {
      i = ogs.players.length;
    }
    for (; i < ngs.players.length; ++i) {
      if (ngs.players[i].email != ngs.player) {
        new_players.push(ngs.players[i].email);
      }
    }
    return new_players;
  },
});
Game.all_messages.push(new PlayerJoinedGameMessage());

/**
 * Base Message for all messages that relate to the end of the game.
 */
var AbstractGameOverMessage = Class.create(AbstractMessage, {
  shouldShow: function($super, old_gamestate, new_gamestate) {
    return old_gamestate.started &&
           !old_gamestate.done &&
           new_gamestate.done;
  }
});

var AllHumansSurviveMessage = Class.create(AbstractGameOverMessage, {
  shouldShow: function($super, old_gamestate, new_gamestate) {
    var super_true = $super(old_gamestate, new_gamestate);
    if (!super_true) {
      return false;
    }
    for (var i = 0; i < new_gamestate.players.length; i++) {
      if (new_gamestate.players[i].infected) {
        // At least one player was infected.
        return false;
      }
    }
    // No players were infected!
    return true;
  },
  getMessage: function(old_gamestate, new_gamestate) {
    return "All humans survived!";
  }
});
Game.all_messages.push(new AllHumansSurviveMessage());

var AllHumansInfectedMessage = Class.create(AbstractGameOverMessage, {
  shouldShow: function($super, old_gamestate, new_gamestate) {
    var super_true = $super(old_gamestate, new_gamestate);
    if (!super_true) {
      return false;
    }
    for (var i = 0; i < new_gamestate.players.length; i++) {
      if (!new_gamestate.players[i].infected) {
        // At least one player was not infected.
        return false;
      }
    }
    // All players were infected!
    return true;
  },
  
  getMessage: function(old_gamestate, new_gamestate) {
    return "All humans infected!";
  }
});
Game.all_messages.push(new AllHumansInfectedMessage());