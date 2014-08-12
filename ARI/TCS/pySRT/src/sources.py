import ephem

def set_source(name):
    """
    Returns a source with name from the 
    source catalog.
    """

    name = name.lower()
    
    if(name == 'Sun'):
        object = ephem.Sun()
    if(name == 'Mars'):
        object = ephem.Mars()
    if(name == 'Jupiter'):
        object = ephem.Jupiter()
    if (name == 'LMC'):
        object = ephem.readdb("LMC,f|G,5:23:34,-69:45:24,0.9,2000,3.87e4|3.3e4")
    if (name == '3C273'):
        object = ephem.readdb("3C273,f|G,12:29:06.6997,+02:03:08.598,12.8,2000,34.02|25.17")
    if (name == 'sgrA'):
        object = ephem.readdb("sgrA,f|J,17:45:40.036,-29:00:28.17,0,2000")
    if (name == 'G90'):
        object = ephem.readdb("G90,f|J,21:13:44,48:12:27.17,0,2000")
    if (name == 'G180'):
        object = ephem.readdb("G180,f|J,05:43:11,29:1:20,0,2000")
    if (name == 'Orion'):
        object = ephem.readdb("Orion,f|J,05:35:17.3,-05:23:28,0,2000")
    if (name == 'Rosett'):
        object = ephem.readdb("Rosett,f|J,06:31:51,04:54:47,0,2000")
    
    return object