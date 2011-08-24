#!/usr/bin/env python

from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.ext import db
# appengine still uses python 2.5, when it upgrades we can use the built-in json module
from django.utils import simplejson as json
import urllib


def getapi_schemename(path_url, prefix_url):
    "helper function to strip a scheme name off of a url"
    scheme = path_url[len(prefix_url):]
    if scheme:
        if scheme[0]=='/': scheme = scheme[1:]
        else: raise Exception("Invalid URL")
    return scheme


# ApplicationSettings record class. Other things we may want to save in this data structure are
#   user information, version number.  Store everything but DisplayModeSettings
class RhinoAppSettings(db.Model):
    name = db.StringProperty(required=True)  # the "scheme" name
    settings = db.TextProperty()             # JSON style string of settings

    @staticmethod
    def get_from_db(scheme):
        settings = db.GqlQuery('SELECT * FROM RhinoAppSettings WHERE name = :1', scheme)
        item = settings.get()
        return item
    @staticmethod
    def get_all_names():
        settings = db.GqlQuery('SELECT * FROM RhinoAppSettings')
        return [setting.name for setting in settings]


# called with BASEURL/api/appsettings*
#   http://rhinosettings.appspot.com/api/appsettings*
#   http://localhost:8080/api/appsettings*
class AppSettingsHandler(webapp.RequestHandler):
    prefix_url = "/api/appsettings"
    def get(self):
        scheme = getapi_schemename(self.request.path, AppSettingsHandler.prefix_url)
        if scheme:
            scheme = urllib.unquote(scheme)
            item = RhinoAppSettings.get_from_db(scheme)
            if item: self.response.out.write(item.settings)
            else: self.error(404) #not found
        else:
            schemes = RhinoAppSettings.get_all_names()
            d = {"schemes":schemes}
            output = json.dumps(d)
            self.response.out.write(output)

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




#########################################################################################
# Let's work on the DisplayMode settings later, the following database and requesthandler
# subclasses could be used to store a bunch of named DisplayModes on appengine that users
# can browse and install.
#########################################################################################
class DisplayModeSettings(db.Model):
    name = db.StringProperty(required=True)     # the "scheme" name
    description = db.StringProperty()
    settings = db.TextProperty(required=True)   # JSON style string of settings
    preview = db.BlobProperty()


# called with BASEURL/api/displaymodes*
#   http://rhinosettings.appspot.com/api/displaymodes*
#   http://localhost:8080/api/displaymodes*
class DisplayModesHandler(webapp.RequestHandler):
    prefix_url = "/api/displaymodes"
    def get(self):
        mode_name = getapi_schemename(self.request.path, DisplayModesHandler.prefix_url)
        if mode_name:
            self.response.out.write("Named DisplayMode = " + mode_name)
        else:
            self.response.out.write("DisplayModes (all...)")



#########################################################################################
# Start the appengine handlers
#########################################################################################
def main():
    handlers = []
    handlers.append( (AppSettingsHandler.prefix_url + '.*', AppSettingsHandler) )
    handlers.append( (DisplayModesHandler.prefix_url + '.*', DisplayModesHandler) )
    application = webapp.WSGIApplication( handlers, debug=True)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
