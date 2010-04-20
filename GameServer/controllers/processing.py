import datetime
import logging

from models import game

from google.appengine.ext import webapp
from google.appengine.api.labs import taskqueue


MAX_DATASTORE_ENTITY_AGE = datetime.timedelta(7, 0, 0)


class BaseCleanupHandler(webapp.RequestHandler):
  
  def get(self):
    self.post()
  
  def post(self):
    deleted = False
    for tile in self._GetQuery().fetch(1000):
      deleted = True
      tile.delete()
      # logging.info("Deleted tile " % tile.Id())
    if deleted:
      task = taskqueue.Task(url=self._GetTaskUrl())
      task.add(queue_name="cleanup")
  
  def _GetTaskUrl(self):
    raise Exception("Must implement.")

  def _GetQuery(self):
    raise Exception("Must implement.")


class CleanupTileHandler(BaseCleanupHandler):

  def _GetTaskUrl(self):
    return "/tasks/cleanup/tiles"

  def _GetQuery(self):
    query = game.GameTile.all()
    query.filter("last_update_time < ", 
                 datetime.datetime.now() - MAX_DATASTORE_ENTITY_AGE)
    return query
  


class CleanupGameHandler(webapp.RequestHandler):
  
  def _GetTaskUrl(self):
    return "/tasks/cleanup/games"

  def _GetQuery(self):
    query = game.Game.all()
    query.filter("last_update_time < ",
                 datetime.datetime.now() - MAX_DATASTORE_ENTITY_AGE)
    return query
