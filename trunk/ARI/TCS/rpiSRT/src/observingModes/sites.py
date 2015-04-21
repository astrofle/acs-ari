import ephem
import math
import ephem.stars
print "loading site parameters and source list (small)"
print "call find_sources(source_list, site) for a list of observable objects"

sites = {
		'calama':{'lat': '-22.5', 'lon':'-68.9', 'elevation':2277},
		'San Joaquin':{'lat': '-33.499991', 'lon':'-70.611403', 'elevation':400},
		'Santa Martina':{'lat': '-33.268726', 'lon':'-70.531504', 'elevation':1400},
}


planet_list = {
	'Moon':ephem.Moon(),
	'Sun':ephem.Sun(),
	'Mercury':ephem.Mercury(),
	'Venus':ephem.Venus(),
	'Mars':ephem.Mars(),
	'Jupiter':ephem.Jupiter(),
	'Saturn':ephem.Saturn(),
	'Uranus':ephem.Uranus(),
	'Neptune':ephem.Neptune(),
	'Pluto':ephem.Pluto()
	}

SRT_sources_list = {
	'Crab':{'ra':'05:31:30', 'dec':'21:58:00'},
	'Orion':{'ra':'05:32:48','dec':'-5:27:00'},
	'S8':{'ra':'05:42:00','dec':'-1:00:00'},
	'Cass':{'ra':'23:21:12','dec':'58:44:00'},
	'SgrA':{'ra':'17:42:54', 'dec':'-28:50:00'},
	'Rosett':{'ra':'06:29:12', 'dec':'04:57:00'},
	'M17':{'ra':'18:17:30', 'dec':'-16:18:00'},
	'CygEMN':{'ra':'20:27:00', 'dec':'41:00:00'},
	'G90':{'ra':'21:12:00', 'dec':'48:00:00'},
	'G180':{'ra':'05:40:00', 'dec':'29:00:00'},
	'GNpole':{'ra':'12:48:00', 'dec':'28:00:00'},
	'Androm':{'ra':'00:39:00', 'dec':'40:30:00'},
	'AC1':{'ra':'05:14:12', 'dec':'18:44:00'},
	'PULSAR':{'ra':'03:29:00','dec':'54:00:00'},
	'PS':{'ra':'08:30:00', 'dec':'-45:00:00'},
	'3c218':{'ra':'09:15:41', 'dec':'-11:53:05'}
	}

#Pending galactic coordinate

star_list = []
for star in ephem.stars.db.split("\n"):
	star_list.append(star.split(",")[0])	
star_list.remove('')

def find_planets(planets, site):
	sources = {}
	for planet in planets:
		[az, el] = source_azel(planets[planet], site)
		#print planet, az, el
		if el > 15.0:
			sources[planet] = planets[planet]
	return sources

def find_stars(stars, site):
	sources = {}
	for star in stars:
		[az, el] = source_azel(ephem.star(star), site)
		#print star, az, el
		if el > 15.0:
			sources[star] = ephem.star(star)
	return sources
	
def find_SRTsources(SRTsources, site):
	sources = {}
	for source in SRTsources:
		[az, el] = radec2azel(SRTsources[source]['ra'], SRTsources[source]['dec'], site)
		#print source, az, el
		if el> 15.0:
			sources[source] = SRTsources[source]
	return sources

def source_azel(object, site):
	site.date = ephem.now()
	object.compute(site)
	az = 180*object.az/math.pi
	az = round(az,2)
	el = 180*object.alt/math.pi
	el = round(el,2)
	return [az, el]

def radec2azel(ra, dec, site):
	star = ephem.FixedBody()
	star._ra = ephem.hours(ra)
	star._dec = ephem.degrees(dec)
	[az, el] = source_azel(star, site)
	azd = int(az)
	azm = abs(60*(az-azd))
	azs = 60*(azm-int(azm))
	eld = int(el)
	elm = abs(60*(el-eld))
	els = 60*(elm-int(elm))
	return [az, el]
	
# Local coordinates
place = 'Santa Martina'
lat = sites[place]['lat']
lon = sites[place]['lon']
elevation = sites[place]['elevation']
site = ephem.Observer()
site.lon = lon
site.lat = lat
site.elevation = elevation


# Find observable planets
planets = find_planets(planet_list, site)
# Find observable stars
stars = find_stars(star_list, site)
# Find observable SRT sources
SRTsources = find_SRTsources(SRT_sources_list, site)
