#!/usr/bin/env python
# v0.1
# a network link provider for Google Earth that overlays NearMap images onto Google Earth
# bug reports etc to gm@stackunderflow.com
# Calculations may not be accurate, do not use for any critical purpose

import socket,thread, globalmaptiles

screen_width = 1920

def genkml(x,y,z,n,s,e,w):
	resp = """<GroundOverlay>
	<name>Tile at %i,%i</name>
	<Icon>
		<href>http://khm0.nearmap.com/kh/v=57&amp;x=%i&amp;s=&amp;y=%i&amp;z=%i&amp;s=G</href>
		<viewBoundScale>0.75</viewBoundScale>
	</Icon>
	<LatLonBox>
		<north>%f</north>
		<south>%f</south>
		<east>%f</east>
		<west>%f</west>
	</LatLonBox>
</GroundOverlay>
""" % (x,y,x,y,z,n,s,e,w) # req[3],req[1],req[2],req[0]
	return resp

def tileoverlay(tz,gx,gy):
	tb = mercator.TileBounds(gx,gy,tz)
	tblat,tblon = mercator.MetersToLatLon(tb[0],tb[1])
	tblat = 0 - tblat # seems to be the wrong way round
	btlat,btlon = mercator.MetersToLatLon(tb[2],tb[3])
	btlat = 0 - btlat
	#print str((tblat,tblon,btlat,btlon))
	return genkml(gx,gy,tz,btlat,tblat,tblon,btlon)
	

def gettiles(req):
	#print req
	lat = float(req[1])
	lon = float(req[0])
	latmax = float(req[3])
	lonmax = float(req[2])
	
	minx, miny = mercator.LatLonToMeters( lat, lon )		# this is quite similar to globalmaptiles
	maxx, maxy = mercator.LatLonToMeters( latmax, lonmax )
	
	#print mercator.Resolution(tz)
	#print abs(maxx-minx) / mercator.Resolution(tz)
	tz = mercator.ZoomForPixelSize(abs(maxx-minx)/screen_width)
	if (tz > 21):
		tz = 21
	print "using zoom level %i" % tz
	#print "%i,%i" % (abs(maxx-minx), abs(maxy-miny))

	tminx, tminy = mercator.MetersToTile( minx, miny, tz )	
	tmaxx, tmaxy = mercator.MetersToTile( maxx, maxy, tz )
	
	overlays = """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2" xmlns:gx="http://www.google.com/kml/ext/2.2" xmlns:kml="http://www.opengis.net/kml/2.2" xmlns:atom="http://www.w3.org/2005/Atom">
<Folder>
	<name>NearTheEarth</name>
	<open>1</open>
	<ScreenOverlay>
    <name>logo</name>
    <Icon>
      <href>http://www.nearmap.com/img/nearmap_watermark.png</href>
    </Icon>
    <overlayXY x="0" y="0" xunits="fraction" yunits="fraction"/>
    <screenXY x="-25" y="6" xunits="pixel" yunits="pixel"/>
    <rotationXY x="0" y="0" xunits="fraction" yunits="fraction"/>
    <size x="0" y="0" xunits="fraction" yunits="fraction"/>
  </ScreenOverlay>"""
	for ty in range(tminy, tmaxy+1):
		for tx in range(tminx, tmaxx+1):
			gx, gy = mercator.GoogleTile(tx, ty, tz)
			overlays += tileoverlay(tz, gx, gy)
	return overlays + "</Folder></kml>"


def interact(conn):
	req = conn.recv(10000).split("\n")[0].split(" ")[1]
	print req
	req = req.replace("/?BBOX=","")
	req = req.split(",")
	conn.send(gettiles(req))
	conn.close()

serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
serversocket.bind(('0.0.0.0', 8080))
serversocket.listen(50)
mercator = globalmaptiles.GlobalMercator()

while 1:
	conn, addr = serversocket.accept()
	thread.start_new_thread(interact,(conn,))
