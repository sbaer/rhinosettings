import webapp2


class MainHandler(webapp2.RequestHandler):
    def get(self):
        self.response.out.write('Hello world!')


application = webapp2.WSGIApplication([('/', MainHandler)], debug=True)
