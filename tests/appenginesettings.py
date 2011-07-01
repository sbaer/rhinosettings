#rhinosettings google app to store/retrieve application settings in the 'cloud'
import sys, json, urllib, urllib2, inspect
import rhinoscriptsyntax as rs
import System, Rhino

appengine_url = "http://rhinosettings.appspot.com/"
# for local testing
#appengine_url = "http://localhost:8080/"

def cloudrestore(id):
    """Retrieve settings from database and update the
    the current application settings by these values
    Parameters:
      id: name of the settings scheme in the database
    """
    f = urllib.urlopen(appengine_url + id)
    received_data = f.read()
    f.close()
    if not received_data: return
    data = json.loads(received_data)

    states = {}
    states["AppearanceSettings"] = Rhino.ApplicationSettings.AppearanceSettings.GetDefaultState()
    states["EdgeAnalysisSettings"] = Rhino.ApplicationSettings.EdgeAnalysisSettings.GetDefaultState()
    states["ModelAidSettings"] = Rhino.ApplicationSettings.ModelAidSettings.GetDefaultState()
    states["ViewSettings"] = Rhino.ApplicationSettings.ViewSettings.GetDefaultState()
    states["SmartTrackSettings"] = Rhino.ApplicationSettings.SmartTrackSettings.GetDefaultState()
    aliases = Rhino.ApplicationSettings.CommandAliasList.GetDefaults()
    
    def restoresetting(state, name, setting):
        try:
            s = "state." + name
            if name.endswith("Color"):
                s += "=System.Drawing.ColorTranslator.FromHtml(\"" + setting + "\")"
            else:
                if type(setting) is str: s += "='" + setting + "'"
                else: s+= "=" + str(setting)
            exec(s)
        except:
            print sys.exc_info()
    for setting, val in data.items():
        if type(val) is dict:
            if states.has_key(setting):
                state = states[setting]
                for k,v in val.items(): restoresetting(state, k, v)
            if setting=="CommandAliasList":
                aliases.Clear()
                for k,v in val.items(): aliases.Add(k,v)
    Rhino.ApplicationSettings.CommandAliasList.Clear()
    for kv in aliases:
        Rhino.ApplicationSettings.CommandAliasList.Add(kv.Key,kv.Value)
    Rhino.ApplicationSettings.AppearanceSettings.UpdateFromState( states["AppearanceSettings"] )
    Rhino.ApplicationSettings.EdgeAnalysisSettings.UpdateFromState( states["EdgeAnalysisSettings"] )
    Rhino.ApplicationSettings.ModelAidSettings.UpdateFromState( states["ModelAidSettings"] )
    Rhino.ApplicationSettings.ViewSettings.UpdateFromState( states["ViewSettings"] )
    Rhino.ApplicationSettings.SmartTrackSettings.UpdateFromState( states["SmartTrackSettings"] )
    rs.Redraw()

	
def cloudsave(id):
    """Save settings to the cloud.
    parameters:
      id: Name of scheme to save in database (always converted to lower case)
    """
    def getnondefaults(section, defaults):
        dict = {}
        members = inspect.getmembers(defaults, (lambda x: not inspect.isbuiltin(x)) )
        for name, val in members:
            if name.startswith('_'): continue
            s = "Rhino.ApplicationSettings."+section+"." + name
            sameasdefault = eval( "defaults."+name+"=="+s )
            if not sameasdefault:
                print "   saving:  ", s
                item = eval(s)
                if type(item) is System.Drawing.Color:
                    item = System.Drawing.ColorTranslator.ToHtml(item)
                dict[name] = item
        return dict

    data = {}

    defaults = Rhino.ApplicationSettings.AppearanceSettings.GetDefaultState()
    subdict = getnondefaults("AppearanceSettings", defaults)
    if subdict: data["AppearanceSettings"] = subdict

    defaults = Rhino.ApplicationSettings.EdgeAnalysisSettings.GetDefaultState()
    subdict = getnondefaults("EdgeAnalysisSettings", defaults)
    if subdict: data["EdgeAnalysisSettings"] = subdict

    defaults = Rhino.ApplicationSettings.ModelAidSettings.GetDefaultState()
    subdict = getnondefaults("ModelAidSettings", defaults)
    if subdict: data["ModelAidSettings"] = subdict
    
    defaults = Rhino.ApplicationSettings.ViewSettings.GetDefaultState()
    subdict = getnondefaults("ViewSettings", defaults)
    if subdict: data["ViewSettings"] = subdict
    
    defaults = Rhino.ApplicationSettings.SmartTrackSettings.GetDefaultState()
    subdict = getnondefaults("SmartTrackSettings", defaults)
    if subdict: data["SmartTrackSettings"] = subdict

    if not Rhino.ApplicationSettings.CommandAliasList.IsDefault():
        print "   saving:   Rhino.ApplicationSettings.CommandAliasList"
        subdict = {}
        aliases = Rhino.ApplicationSettings.CommandAliasList.ToDictionary()
        for kv in aliases: subdict[kv.Key] = kv.Value
        data["CommandAliasList"] = subdict
    
    if data:
        jsondata = {"name":id, "settings":data}
        j = json.dumps(jsondata)
        req = urllib2.Request(appengine_url, j, {"content-type":"application/json"})
        stream = urllib2.urlopen(req)
        response = stream.read()
        stream.close()
        return response


def getinput():
    gs = Rhino.Input.Custom.GetString()
    gs.SetCommandPrompt("Scheme Name")
    direction = Rhino.Input.Custom.OptionToggle(True, "Save", "Restore")
    gs.AddOptionToggle("Direction", direction)
    op_list = gs.AddOption("List")
    while( True ):
        if gs.Get()==Rhino.Input.GetResult.Option:
            if gs.OptionIndex() == op_list:
                f = urllib.urlopen(appengine_url)
                received_data = f.read()
                f.close()
                if received_data:
                    schemes = json.loads(received_data)["schemes"]
                    for scheme in schemes: print scheme
            continue
        break
    if gs.CommandResult()!=Rhino.Commands.Result.Success:
        return
    restore = direction.CurrentValue
    name = gs.StringResult()
    return restore, name

if __name__ == "__main__":
    print "Rhino Appearance Settings"
    input = getinput()
    if input:
        restore, name = input
        if restore:
            print "- Restoring settings saved in cloud"
            cloudrestore(name)
        else:
            print "- Saving non-default settings to cloud"
            cloudsave(name)
