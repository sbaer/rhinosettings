#!/usr/bin/env python

from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.ext import db
# appengine still uses python 2.5, when it upgrades we can use the built-in json module
from django.utils import simplejson as json


# Our database record class. Other things we may want to save in this data structure are
#   user information, version number 
class RhinoAppSettings(db.Model):
    name = db.StringProperty(required=True)  # the "scheme" name
    settings = db.TextProperty()             # JSON style string of settings
    


# called with http://rhinosettings.appspot.com/*
class MainHandler(webapp.RequestHandler):
    def get(self):
        scheme = self.request.path[1:]
        if scheme:
            settings = db.GqlQuery('SELECT * FROM RhinoAppSettings WHERE name = :1', scheme)
            item = settings.get()
            if item:
                self.response.out.write(item.settings)
        else:
            settings = db.GqlQuery('SELECT * FROM RhinoAppSettings')
            if settings.count()>0:
                schemes = []
                for setting in settings:
                    schemes.append(setting.name)
                d = {"schemes":schemes}
                output = json.dumps(d)
                self.response.out.write(output)
            else:
                self.response.out.write("no settings")

    def post(self):
        posted_data = self.request.body
        data = json.loads(posted_data)
        # the data needs to have a name string and a settings dictionary
        _name = data['name']
        _settings = data['settings']
        if _settings:
            _settings = json.dumps(_settings) #convert _settings back into json
        if _name and _settings:
            # see if the item is already in the datastore. If we implemented
            # versioning, I would just add a new record with an updated version
            # number
            query_rc = db.GqlQuery("SELECT * FROM RhinoAppSettings WHERE name = :1", _name)
            item = query_rc.get() #just grab the first one and update it
            if item:
                item.settings = _settings
                item.put()
            else:
                saved = RhinoAppSettings(name=_name, settings=_settings)
                saved.put()


def main():
    application = webapp.WSGIApplication([('/.*', MainHandler)], debug=True)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
