import webapp2
from google.appengine.ext import db
import json
import urllib


def getschemename(path_url, prefix_url):
    """helper function to strip a scheme name off of a url"""
    scheme = path_url[len(prefix_url):]
    if scheme:
        if scheme[0] == '/':
            scheme = scheme[1:]
        else:
            raise Exception("Invalid URL")
    return scheme


# ApplicationSettings record class. This is what is saved on the google server
class RhinoSettings(db.Model):
    name = db.StringProperty(required=True)  # the "scheme" name
    settings = db.TextProperty()             # JSON style string of settings

    @staticmethod
    def get_from_db(scheme):
        settings = db.GqlQuery('SELECT * FROM RhinoSettings WHERE name = :1', scheme)
        item = settings.get()
        return item
    @staticmethod
    def get_all_names():
        settings = db.GqlQuery('SELECT * FROM RhinoSettings')
        return [setting.name for setting in settings]


# called with BASEURL/api/appsettings*
#   http://rhinosettings.appspot.com/api/appsettings*
#   http://localhost:8080/api/appsettings*
class AppSettingsHandler(webapp2.RequestHandler):
    prefix_url = "/api/appsettings"

    def get(self):
        scheme = getschemename(self.request.path, AppSettingsHandler.prefix_url)
        if scheme:
            scheme = urllib.unquote(scheme)
            item = RhinoSettings.get_from_db(scheme)
            if item:
                self.response.out.write(item.settings)
            else:
                self.error(404)  #not found
        else:
            schemes = RhinoSettings.get_all_names()
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
            item = RhinoSettings.get_from_db(_name) #just grab the first one and update it
            if item:
                item.settings = _settings
                item.put()
            else:
                saved = RhinoSettings(name=_name, settings=_settings)
                saved.put()


# Start the appengine handlers
handlers = [(AppSettingsHandler.prefix_url + '.*', AppSettingsHandler)]
application = webapp2.WSGIApplication(handlers, debug=True)
