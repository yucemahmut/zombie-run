import logging
import wsgiref.handlers

from controllers import admin
from controllers import gamestate
from google.appengine.api import users
from google.appengine.ext import webapp


URL_BINDINGS = [ 
                 ('/', admin.IndexPageHandler),
                 ('/rpc/create', gamestate.CreateHandler),
                 ('/rpc/get', gamestate.GetHandler),
                 ('/rpc/join', gamestate.JoinHandler),
                 ('/rpc/put', gamestate.PutHandler),
                 ('/rpc/start', gamestate.StartHandler),
               ]
REVERSE_URL_BINDINGS = {}


def GetApplication():
  for (url, clazz) in URL_BINDINGS:
    REVERSE_URL_BINDINGS[clazz] = url
  return webapp.WSGIApplication(
      URL_BINDINGS,
      debug=True)


def main():
  wsgiref.handlers.CGIHandler().run(GetApplication())


if __name__ == '__main__':
  main()
