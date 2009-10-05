import logging
import wsgiref.handlers

from controllers import api
from google.appengine.api import users
from google.appengine.ext import webapp


URL_BINDINGS = [ 
                 ('/', api.CreateHandler),
                 ('/rpc/get', api.GetHandler),
                 ('/rpc/join', api.JoinHandler),
                 ('/rpc/put', api.PutHandler),
                 ('/rpc/start', api.StartHandler),
                 ('/rpc/addFriend', api.AddFriendHandler),
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
