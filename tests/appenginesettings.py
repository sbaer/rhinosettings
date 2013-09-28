#rhinosettings google app to store/retrieve application settings in the 'cloud'
import sys, json, urllib, urllib2
import rhinoscriptsyntax as rs
import System, Rhino

#appengine_url = "http://rhinosettings.appspot.com/api/appsettings"
# for local testing
appengine_url = "http://localhost:8080/api/appsettings"

def cloudrestore(id):
    """Retrieve settings from database and update the
    the current application settings by these values
    Parameters:
      id: name of the settings scheme in the database
    """
    f = urllib.urlopen(appengine_url + '/' + id)
    received_data = f.read()
    f.close()
    if not received_data:
        return
    data = json.loads(received_data)

    color = data["ViewportBackgroundColor"]
    color = System.Drawing.ColorTranslator.FromHtml(color)
    Rhino.ApplicationSettings.AppearanceSettings.ViewportBackgroundColor = color
    rs.Redraw()


def cloudsave(id):
    """Save settings to the cloud.
    parameters:
      id: Name of scheme to save in database (always converted to lower case)
    """
    color = Rhino.ApplicationSettings.AppearanceSettings.ViewportBackgroundColor
    color = System.Drawing.ColorTranslator.ToHtml(color)
    data = {"ViewportBackgroundColor": color}
    if data:
        jsondata = {"name":id, "settings":data}
        j = json.dumps(jsondata)
        req = urllib2.Request(appengine_url, j, {"content-type":"application/json"})
        stream = urllib2.urlopen(req)
        response = stream.read()
        stream.close()
        return response

def GetOptions():
    restore = rs.GetBoolean("Rhino Appearance Settings", [("Option", "Save", "Restore")],[False])
    if restore is None: return
    restore = restore[0]
    name = rs.GetString("Scheme Name")
    if name: return name, restore

if __name__ == "__main__":
    rc = GetOptions()
    if rc:
        name, restore = rc
        if restore:
            print "- Restoring settings saved in cloud"
            cloudrestore(name)
        else:
            print "- Saving settings to cloud"
            cloudsave(name)
