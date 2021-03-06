#!/usr/bin/python

import sys
sys.path.append( "../lib/" )

from PIL import Image, ImageTk
import time
from datetime import datetime
import socket 
import cv2
import cv
from threading import *
import random
from math import *
import easygui as eg
import sonar_functions as sf
from img_processing_tools import *
from nav_functions import *
from maxsonar_class import *
from robomow_motor_class_arduino import *
from gps_functions import *
from class_android_sensor_tcp import *
from train_terrain import *
#from lidar_class import *

from visual import *
from mobot_nav_class import *

def snap_shot(filename):
	"""grabs a frame from webcam, resizes to 320x240 and returns image"""
	#capture from camera at location 0
	now = time.time()
	global webcam1
	try:
		#have to capture a few frames as it buffers a few frames..
		for i in range (5):
			ret, img = webcam1.read()		 
		#print "time to capture 5 frames:", (time.time()) - now
		cv2.imwrite(filename, img)
		img1 = Image.open(filename)
		img1.thumbnail((320,240))
		img1.save(filename)
		#print (time.time()) - now
	except:
		print "could not grab webcam"
	return 

def send_file(host, cport, mport, filetosend):
	#global file_lock
	file_lock = True
	#print "file_lock", file_lock
	try:       
		cs = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		cs.connect((host, cport))
		cs.send("SEND " + filetosend)
		print "sending file", filetosend
		cs.close()
	except:
		#print "cs failed"
		pass
	time.sleep(0.1)
	try:
		ms = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		ms.connect((host, mport))
		f = open(filetosend, "rb")
		data = f.read()
		f.close()
		ms.send(data)
		ms.close()
	except:
		#print "ms failed"
		pass
	#file_lock = False
	#print "file_lock", file_lock
		
		
'''
def send_data(host="u1204vm.local", cport=9091, mport=9090, datatosend=""):
	try:       
		cs = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		cs.connect((host, cport))
		cs.send("SEND " + filetosend)
		cs.close()
	except:
		pass
	time.sleep(0.05)
	try:
		ms = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		ms.connect((host, mport))
		f = open(filetosend, "rb")
		data = f.read()
		f.close()
		ms.send(data)
		ms.close()
	except:
		pass
'''	
class send_video(Thread):
	def __init__(self, filetosend):   
		self.filetosend = filetosend     
		Thread.__init__(self)

	def run(self):
			#global file_lock, hhh
			print self.filetosend
			while True:
				snap_shot(self.filetosend)	
				send_file(host="u1204vm.local", cport=9090, mport=9091,filetosend=self.filetosend)
				time.sleep(.01)
							
class send_sonar_data(Thread):
	def __init__(self, filetosend): 
		self.sonar = MaxSonar()  
		self.filetosend = filetosend
		self.sonar_data = "" 
		self.max_dist = -1
		self.min_dist = -1   
		self.min_sensor = -1
		self.max_sensor = -1 
		self.right_sensor = -1
		self.left_sensor = -1
		self.forwardl_sensor = -1
		self.fowardr_sensor = -1
		Thread.__init__(self)

	def run(self):
			#global file_lock, hhh
			while True:
				self.sonar_data = ""
				self.max_dist = -1
				self.min_dist = -1 
				self.min_sensor = -1
				self.max_sensor = -1
				self.right_sensor = -1
				self.left_sensor = -1
				self.forwardl_sensor = -1
				self.fowardr_sensor = -1
				#
				#below 2 lines are for test purposes when actual US arent sending data
				#for i in range(1,6):
				#	sonar_data = sonar_data + "s"+str(i)+":"+ str(random.randint(28, 91))

				data = str(self.sonar.distances_cm())
				self.sonar_data = []
				sonar_data_str1 = ""
				try:
					if len(data) > 1:
						self.sonar_data.append(int(data[(data.find('s1:')+3):(data.find('s2:'))]))
						self.sonar_data.append(int(data[(data.find('s2:')+3):(data.find('s3:'))]))
						self.sonar_data.append(int(data[(data.find('s3:')+3):(data.find('s4:'))]))
						self.sonar_data.append(int(data[(data.find('s4:')+3):(data.find('s5:'))]))
						#have to put this before cliff sensor
						self.min_dist = min(self.sonar_data)
						self.min_sensor = self.sonar_data.index(self.min_dist)
						self.sonar_data.append(int(data[(data.find('s5:')+3):(len(data)-1)]))
						self.max_dist = max(self.sonar_data)
						#self.min_dist = min(self.sonar_data)
						#self.min_sensor = self.sonar_data.index(self.min_dist)
						self.max_sensor = self.sonar_data.index(self.max_dist)
						#sonar_data_str1 = "".join(str(x) for x in self.sonar_data)
						self.frontl_sensor = self.sonar_data[0]
						self.frontr_sensor = self.sonar_data[1]
						self.right_sensor = self.sonar_data[2]
						self.left_sensor = self.sonar_data[3]
						self.cliff = self.sonar_data[4]

						#print sonar_data_str1
						#print data
						#
						#f = open("sonar_data.txt", "w")
						#f.write(data)
						#f.close()
						#send_file(host="u1204vm.local", cport=9092, mport=9093,filetosend=self.filetosend)
				except:
					pass
				try:
					time.sleep(.02)
				except:
					pass
			print "out of while in sonar"
	
	def terminate(self):
		self.sonar.terminate()


def safety_check(motor, sonar, threshold, cliff):
	answer = True
	if (sonar.cliff > cliff):
		print "cliff detected", sonar.cliff, cliff
		answer = False
	if (sonar.min_dist < threshold):
		print "object too close", sonar.min_dist, threshold
		answer = False
	return answer

def move_mobot(motor, sonar, threshold, cliff, themove, speed):
	move_time = .6
	print "sonar data:", sonar.sonar_data
	print "moving:", themove, "  speed:", speed
	#####################3
	if themove == "s": motor.forward(0)
	if (themove == "f"):
		#if (safety_check(motor, sonar, threshold, cliff)) == True:
		motor.forward(speed)
		time.sleep(move_time)
		motor.forward(0)
			#print motor.motor1_speed, motor.motor2_speed
		#else:
		#	evasive_maneuver(motor, sonar, threshold, cliff)
	if (themove == "b"):
		motor.left(-1*speed)
		motor.right(-1*(speed*1.2))
		#motor.reverse(speed)
		time.sleep(move_time)
		motor.forward(0)
		#print motor.motor1_speed, motor.motor2_speed
	if (themove == "l"):
		motor.spin_left(speed)
		time.sleep(move_time)
		motor.forward(0)
		#print motor.motor1_speed, motor.motor2_speed
	if (themove == "r"):
		motor.spin_right(speed)
		time.sleep(move_time)
		motor.forward(0)
		#print motor.motor1_speed, motor.motor2_speed
	print "done moving"

def enable_video():
	video1 = send_video("snap_shot.jpg")
	video1.daemon=True
	video1.start()
	#video1.join()
	
def enable_sonar():
	sonar = send_sonar_data("sonar_data.txt")
	sonar.daemon=True
	sonar.start()
	#sonar.join()


def test_gps():
	#print "startup all gps"
	#start_all_gps()
	gpslist = gps_list()
	#print gpslist
	gps2 = mobot_gps()
	gps2.daemon=True
	gps2.start()
	
	current_track = 1000
	max_spd = 0.0
	#gps2.join()
	while True:
		print "# of GPS Units:", len(gpslist)
		#if (gps2.satellites > 0):
		print 'Satellites (total of', gps2.satellites , ' in view)'
		print "Active satellites used:", gps2.active_satellites
		#for i in gps2.satellites:
		#	print '\t', i
		print "lat: ", gps2.latitude
		print "long:", gps2.longitude
		print 'track: ', gps2.track
		print "Current Track: ", current_track
		mph = gps2.speed * 2.23693629
		if mph > max_spd: max_spd = mph
		print 'speed: m/sec', gps2.speed , " MPH:" , mph
		print "max_spd: ", max_spd
		if mph > 2.0:
			current_track = gps2.track
		#time.sleep(random.randint(1, 3))
		time.sleep(.5)	
		#os.system("clear")

class display_sonar(Thread):
	def __init__(self, sonar):
		self.sonar = sonar  
		Thread.__init__(self)

class mobot_display(Thread):
	def __init__(self, camID, sonar):
		self.camID = camID 
		self.sonar = sonar   
		Thread.__init__(self)

	def run(self):
		global frame1
		global frame2
		cv2.namedWindow('Sonar Data', cv.CV_WINDOW_AUTOSIZE)
		cv2.namedWindow('Front Camera', cv.CV_WINDOW_AUTOSIZE)
		cv2.namedWindow('Ground Cam', cv.CV_WINDOW_AUTOSIZE)
		cv.MoveWindow('Front Camera', 373, 24)
		cv.MoveWindow('Ground Cam', 760, 24)
		cv.MoveWindow('Sonar Data', 60, 24)
		camera =  cv.CreateCameraCapture(self.camID)
		camera2 = cv.CreateCameraCapture(1)
		while True:
			#time.sleep(1)
			try:
				#print "raw sonar data", self.sonar.sonar_data
				sonar_img = sf.sonar_graph(self.sonar.sonar_data)
				cv.ShowImage('Sonar Data', PILtoCV(sonar_img, 4))
				cv.WaitKey(10)
				del sonar_img
			except:
				print "sonar display failure"
				pass
			try:
				frame1 = cv.QueryFrame(camera)
				frame1 = resize_img(frame1, 0.60)
				cv.ShowImage('Front Camera', frame1)
				cv.WaitKey(10)
			except:
				print "camera1 display failure"
				pass
			try:
				#frame2 = cv.QueryFrame(camera2)
				#frame2 = resize_img(frame2, 0.60)
				frame2 = frame1
				cv.ShowImage('Ground Cam', frame2)
				cv.WaitKey(10)
			except:
				print "camera2 display failure"
				pass

class sonar_prevent_hit(Thread):
	def __init__(self, motor, sonar, threshold):
		self.sonar = sonar  
		self.motor = motor
		self.threshold = threshold
		Thread.__init__(self)

	def run(self):
		while True:
			#time.sleep(.12)
			try:
				#print "self.sonar.min_dist:", self.sonar.min_dist
				if (self.sonar.min_dist < self.threshold):
					print "auto hit prevent activated: " ,self.sonar.sonar_data
					time.sleep(1)
				evasive_maneuver(self.motor, self.sonar, self.threshold)
			except:
				print "sonar auto hit prevent failure"
				pass

def evasive_maneuver(motor, sonar, threshold, cliff):
	global auto_pilot_on
	#wait to confirm 
	motor.stop()
	time.sleep(.05)
	while (sonar.min_dist < threshold or sonar.cliff > cliff or auto_pilot_on == True):
		print "..........evasive maneuver............."
		print "sonar_data: ", sonar.sonar_data
		motor.stop()
		time.sleep(.05)
		motor.left(-1*24)
		motor.right(-1*(24*1.2))
		time.sleep(1)
		motor.stop()
		#time.sleep(.5)
		if (sonar.right_sensor > sonar.left_sensor):
			#while (sonar.frontl_sensor < threshold and sonar.frontr_sensor < threshold):
			motor.spin_right(24)
			time.sleep(random.randint(120, 260)/100)	
			#time.sleep(0.02)
		else:
			#while (sonar.frontl_sensor < threshold and sonar.frontr_sensor < threshold):
			motor.spin_left(24)
			time.sleep(random.randint(120, 260)/100)
			#time.sleep(0.02)
		#move_mobot(motor, 'f', 25)
		#time.sleep(.2)

def turn_to_bearing(motor, sonar, threshold, compass, heading):
	#wait to confirm 
	motor.forward(0)
	time.sleep(1)
	#while (sonar.min_dist > threshold ):
	print "..........turning to heading: ", heading
	dif = 1000 
	while dif > 10:	
		while compass.heading == None:
			time.sleep(.01)
		dif = abs(heading - compass.heading )
		print "dif:", dif
		print "heading now:", compass.heading
		#motor.spin_right(22)
		motor.right(-24)
		motor.left(22)
		#time.sleep(.3)
		#move_mobot(motor, 's', 0)
		#time.sleep(.3)
	motor.foward(0)
	time.sleep(1)	
	print "heading now:", compass.heading

class auto_move(Thread):
	def __init__(self, motor, sonar, threshold, cliff):
		self.motor = motor
		self.sonar = sonar
		self.threshold = threshold
		self.cliff = cliff
		Thread.__init__(self)

	def run(self):		
		global auto_pilot_on
		while True:
			#print "running autopilot", auto_pilot_on
			while auto_pilot_on == True:
				#for i in range (10):
				print "..........autopilot............."
				print "sonar_data: ", self.sonar.sonar_data
				now =  datetime.now()
				print "min sensor:", self.sonar.min_sensor		
				while  (self.sonar.min_dist <= self.threshold):
					evasive_maneuver(self.motor, self.sonar, self.threshold, self.cliff)
				#time.sleep(.5)
				if (self.sonar.min_dist > self.threshold):
					move_mobot(self.motor, self.sonar, self.threshold, self.cliff, 'f',18)

				#time.sleep(1)
				#move_mobot(self.motor, 's', 0)
				#print "sonar_data: ", sonar.sonar_data
				#print "loop time:",  datetime.now() - now
		

def wallfollow(motor, sonar, threshold):
	rm_spd = 16
	lm_spd = 16

	spd = 14
	while True:
		print "..........wallfollow............."
		print "sonar_data: ", sonar.sonar_data
		print "sonar_right:", sonar.right_sensor, "   sonar_left:", sonar.left_sensor,
		print "RMotor: ", rm_spd, "  LMotor: ", lm_spd
		while (sonar.min_dist < threshold):
			rm_spd = spd
			lm_spd = spd
			evasive_maneuver(motor, sonar, threshold)
		else:
			if sonar.right_sensor < 56:
					lm_spd = spd - 4 #decrease left motor speed
					rm_spd = spd + 1 
			if sonar.right_sensor > 57:
					lm_spd = spd + 2 #increase left motor speed
					rm_spd = spd
					#rm_spd = rm_spd -1
			#if sonar.right_sensor  > 48 and sonar.right_sensor < 52:
			#		rm_spd = spd
			#		lm_spd = spd

		#adjust for max/min
		if lm_spd > 28: lm_spd = 28
		if rm_spd > 28: rm_spd = 28
		if lm_spd < 6: lm_spd = 6
		if rm_spd < 6: rm_spd = 6

		#send cmds to motors
		motor.right(rm_spd)
		motor.left(lm_spd)
		time.sleep(.03)
		#move_mobot(motor, 's', 0)
		
def train_on_terrain():
	global frame2
	img1 = frame2
	video = None
	reply = ""
	while reply != 'Quit':
		#eg.rootWindowPosition = eg.rootWindowPosition
		print 'reply=', reply		

		#if reply == "": reply = "Next Frame"

		if reply == "Mowable":
			classID = "1"
			if img1 != None:
				features = find_features(frame2)
				save_data(features, classID)
			else:
				if video != None: 
					img1 = np.array(grab_frame_from_video(video)[1])
				else:
					img1 = frame2
				img1 = array2image(img1)
				img1 = img1.resize((320,240))
				img1 = image2array(img1)
				cv2.imwrite('temp.png', img1)

		if reply == "Non-Mowable":
			classID = "2"
			if img1 != None:
				features = find_features(img1)
				save_data(features, classID)
			else:
				if video != None: 
					img1 = np.array(grab_frame_from_video(video)[1])
				else:
					img1 = frame2
				img1 = array2image(img1)
				img1 = img1.resize((320,240))
				img1 = image2array(img1)
				cv2.imwrite('temp.png', img1)

		if reply == "Quit":
			print "Quitting Training...."
			#sys.exit(-1)

		if reply == "Predict":
			print "AI predicting"
			if img1 != None:
				predict_class(CV2array(img1))
			else:
				if video != None: 
					img1 = np.array(grab_frame_from_video(video)[1])
				else:
					img1 = frame2
				img1 = array2image(img1)
				img1 = img1.resize((320,240))
				img1 = image2array(img1)
				cv2.imwrite('temp.png', img1)

		if reply == "Subsection":
			img1 = Image.open('temp.png')
			print img1
			xx = subsection_image(img1, 16,True)
			print xx
			#while (xx != 9):
			#	time.sleep(1)

		if reply == "Retrain AI":
			print "Retraining AI"
			train_ai()

		if reply == "Next Frame":
			print "Acquiring new image.."
			if video != None: 
				img1 = np.array(grab_frame_from_video(video)[1])
			else:
				img1 = frame2
			print img1
			#img1 = array2image(img1)
			#img1 = CVtoPIL(img1)
			#img1 = img1.resize((320,240))
			#img1 = PILtoCV(img1,3)
			#img1 = image2array(img1)
			#cv2.imwrite('temp.png', img1)
			cv.SaveImage('temp.png', img1)
			#print type(img1)
			#img1.save()

		if reply == "Fwd 10 Frames":
			print "Forward 10 frames..."
			for i in range(10):
				img1 = np.array(grab_frame_from_video(video)[1])
			img1 = array2image(img1)
			img1 = img1.resize((320,240))
			img1 = image2array(img1)
			cv2.imwrite('temp.png', img1)

		if reply == "Del AI File":
			data_filename = 'robomow_feature_data.csv'
			f_handle = open(data_filename, 'w')
			f_handle.write('')
			f_handle.close()

		if reply == "Test Img":	
			#im = Image.fromarray(image)
			#im.save("new.png")
			img1 = Image.open('temp.png')
			#img1.thumbnail((320,240))
			path = "../../../../mobot_data/images/test_images/"
			filename = str(time.time()) + ".jpg"
			img1.save(path+filename)	
			print "trying"
		#if video != None: 
		#	reply =	eg.buttonbox(msg='Classify Image', title='Robomow GUI', choices=('Mowable', 'Non-Mowable', 'Test Img', 'Next Frame', 'Fwd 10 Frames', 'Predict', 'Subsection', 'Retrain AI' , 'Del AI File', 'Quit'), image='temp.png', root=None)
		#else:
		reply =	eg.buttonbox(msg='Classify Image', title='Robomow GUI', choices=('Mowable', 'Non-Mowable', 'Test Img','Next Frame',  'Predict', 'Retrain AI' , 'Del AI File', 'Quit'), image='temp.png', root=None)




if __name__== "__main__":
	testmode = False
	if len(sys.argv) > 1:
		if sys.argv[1] == 'testmode':
				print 'starting in testing mode'
				testmode= True
	
	auto_pilot_on = False
	sonar = None
	motor = None
	compass = None
	reply =""
	movetime = 0.4
	threshold = 40
	cliff = 48
	frame1 =  None
	frame2 = None

	#while sonar == None or motor == None:# or compass == None:
	#while sonar == None:
	#		try:
	#			sonar = send_sonar_data("sonar_data.txt")
	#		except:
	#			time.sleep(.5)
	#			pass
	#sonar.daemon=True
	#sonar.start()

	#while motor == None:
	#		try:
	#			motor = robomow_motor()
	#			print "motor.isConnected:", motor.isConnected
	#		except:
	#			time.sleep(.5)
	#			pass

		#if compass == None:
		#	compass = android_sensor_tcp(8095)
		#	compass.daemon=True
		#	compass.start()
		
	#while lidar == None:	
	#	print 'trying to connect lidar'
	#	lidar = mobot_lidar("/dev/ttyUSB0", 115200)
	#	#except:
	#	time.sleep(.5)
	#	pass

	#th = thread.start_new_thread(update_view, (lidar,))		
	#time.sleep(2)
	#nav = mobot_nav (lidar)
	#raw_input ('done connecting motor and lidar: press enter')
	

	'''
	#time.sleep(3)
	#while compass.heading == None:
	#	time.sleep(1)

	#turn_to_bearing(motor, sonar, 40, compass, 0)
	
	#test_gps()
	#gpslist = gps_list()
	#print gpslist
	#gps2 = mobot_gps()
	#gps2.daemon=True
	#gps2.start()
	#time.sleep(5)

	while True:
		time.sleep(1)
		#if (mobot_gps.active_satellites > 4):
			#print "position: ", gps2.latitude, gps2.longitude
			#the_map = create_map(10, 10, (gps2.latitude, gps2.longitude))	
			#break
		print; print
		print "READINGS"
		print "--------------------------------"
		print "Number of GPS units: " , len(gpslist)
		print 'latitude ' , mobot_gps.latitude
		print 'longitude ' , mobot_gps.longitude
		#print 'mode:', mobot_gps.fix.mode
		print 'track: ', mobot_gps.track
		#print 'time utc ' , mobot_gps.utc, mobot_gps.fix.time
		print 'altitude ' , mobot_gps.altitude
		#print 'epx ', mobot_gps.fix.epx
		#print 'epv ', mobot_gps.fix.epv
		#print 'ept ', mobot_gps.fix.ept
		#print 'epc ', mobot_gps.fix.epc
		#print 'epd ', mobot_gps.fix.epd
		#print 'eps ', mobot_gps.fix.eps
   	#print "speed ", mobot_gps.fix.speed
   	#print "climb " , mobot_gps.fix.climb
   	#print
   	#print 'Satellites (total of', len(mobot_gps.satellites) , ' in view)'
   	#for i in mobot_gps.satellites:
	 	#	print '\t', i
   	print "Active satellites used: ", mobot_gps.active_satellites
	print the_map

		except (KeyboardInterrupt, SystemExit): #when you press ctrl+c
        print "\nKilling Thread..."
        gpsp.running = False
        gpsp.join() # wait for the thread to finish what it's doing
    print "Done.\nExiting."


	#wallfollow(motor, sonar)
	'''
	#start front navigation cam
	mobot_disp = mobot_display(0, sonar)
	mobot_disp.daemon=True
	mobot_disp.start()
	#time.sleep(2)
	#test_gps()

	#mobot_autopilot = auto_move(motor, sonar, threshold, cliff)
	#mobot_autopilot.daemon = True
	#mobot_autopilot.start()
	#print mobot_autopilot

	#while True:
	#	time.sleep(.1)
		

	#start sonar_hit_preventer
	#sonar_hit_preventer = sonar_prevent_hit(motor, sonar, 38)
	#sonar_hit_preventer.daemon=True
	#sonar_hit_preventer.start()
	#sonar_hit_preventer.join()
	#time.sleep(2)
	
	#while True:
	#	auto_move(motor, sonar, 38)
	#	time.sleep(.03)
	#wallfollow(motor, sonar, 40)

	eg.rootWindowPosition = "+60+375"
	while True:
		
		if reply == 'Turn?':
			print "angel_greatest_dist", nav.angel_greatest_dist()
			print "turn_left_or_right", nav.turn_left_or_right()
		
		if reply == 'AutoPilot':
			#auto_move(motor, sonar, threshold)
			if auto_pilot_on == False: 
				auto_pilot_on = True
			else:
				auto_pilot_on = False
			print "auto_pilot_on:", auto_pilot_on
	
		if reply == 'F':
			move_mobot(motor, sonar, threshold, cliff, 'f', 25)
			#time.sleep(movetime)
		if reply == 'B':
			move_mobot(motor, sonar, threshold, cliff, 'b', 25)
			#time.sleep(movetime)
		if reply == 'R':
			move_mobot(motor, sonar, threshold, cliff, 'r', 28)
			time.sleep(movetime)
			motor.stop()
		if reply == 'L':
			move_mobot(motor, sonar, threshold, cliff, 'l', 28)
			time.sleep(movetime)
			motor.stop()
		if reply == 'STOP':
			motor.stop()
		
		if reply == 'TRAIN':
			train_on_terrain()

		if reply == "Quit":
			print "stopping mobot..."
			motor.forward(0)
			time.sleep(.1)
			del mobot_disp	
			motor.terminate()
			sonar.terminate()
			sys.exit(-1)
			#time.sleep(movetime)
			print "Quitting...."

		reply =	eg.buttonbox(title='Mobot Drive', choices=('AutoPilot', 'F', 'B', 'L', 'R', 'STOP', 'TRAIN', 'Quit'), root=None)
'''


#############################################################
#start gps
#get current gps postiion
#get bearing to target position 
# turn toward target bearing
######################################################
gps1 = gps.gps(host="localhost", port="2947")
gps2 = gps.gps(host="localhost", port="2948")
gps3 = gps.gps(host="localhost", port="2949")
gps4 = gps.gps(host="localhost", port="2950")

'''

