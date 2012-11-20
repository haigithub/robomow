#!/usr/bin/python

import gps, os, time


session = gps.gps()
session.poll()
session = gps.gps(host='localhost', port='2947')
session.next()
#session.stream(mode=WATCH_ENABLE|WATCH_NEWSTYLE)

session.stream()


#from gps import *
#session = gps() # assuming gpsd running with default options on port 2947
#session.stream(WATCH_ENABLE|WATCH_NEWSTYLE)
#report = session.next()
#print report

while 1:
	os.system('clear')
	session.next()
	time.sleep(1)
	# a = altitude, d = date/time, m=mode,
	# o=postion/fix, s=status, y=satellites

	print
	print ' GPS reading'
	print '----------------------------------------'
	print 'latitude ' , session.fix.latitude
	print 'longitude ' , session.fix.longitude
	print 'time utc ' , session.utc, session.fix.time
	print 'altitude ' , session.fix.altitude
	print 'epx ' , session.fix.epx
	print 'epv ' , session.fix.epv
	print 'ept ' , session.fix.ept
	print 'speed ' , session.fix.speed
	print 'climb ' , session.fix.climb

	print
	print ' Satellites (total of', len(session.satellites) , ' in view)'
	for i in session.satellites:
		print '\t', i

time.sleep(3)


