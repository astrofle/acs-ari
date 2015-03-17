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

star_list = []
for star in ephem.stars.db.split("\n"):
	star_list.append(star.split(",")[0])	
star_list.remove('')

def find_planets(planets, site):
	sources = {}
	for planet in planets:
		[az, el] = source_azel(planets[planet], site)
		if el > 8.0:
			sources[planet] = planets[planet]
	return sources

def find_stars(stars, site):
	sources = {}
	for star in stars:
		[az, el] = source_azel(ephem.star(star), site)
		if el > 8.0:
			sources[star] = ephem.star(star)
	return sources

def source_azel(object, site):
	site.date = ephem.now()
	object.compute(site)
	az = 180*object.az/math.pi
	el = 180*object.alt/math.pi
	return [az, el]

def radec2azel(object, site):
	galactic_center = ephem.Galactic(0, 0)	
	eq = ephem.Equatorial(galactic_center)
	body = ephem.FixedBody()
	body._ra = eq.ra
	body._dec = eq.dec
	body._epoch = eq.epoch
	return body
	
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
