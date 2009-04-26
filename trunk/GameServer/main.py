import wsgiref.handlers

from controllers import gamestate
from google.appengine.ext import webapp


class MainHandler(webapp.RequestHandler):

  def get(self):
    self.response.out.write('Hello world!')


def GetApplication():
  return webapp.WSGIApplication(
      [ ('/', MainHandler),
        ('/game/create', gamestate.CreateHandler),
        ('/game/get', gamestate.GetHandler),
        ('/game/join', gamestate.JoinHandler),
        ('/game/put', gamestate.PutHandler),
        ('/game/start', gamestate.StartHandler),
        ],
      debug=True)


def main():
  wsgiref.handlers.CGIHandler().run(GetApplication())


if __name__ == '__main__':
  main()
