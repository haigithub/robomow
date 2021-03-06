#!/usr/bin/env python
import sys
sys.path.append( "../lib/" )

import pika
from pylab import imread
import time
import cv, cv2
import cPickle as pickle
import gc

'''
helps on ubunutu to not drop frames
lsmod
rmmod uvcvideo
modprobe uvcvideo nodrop=1 timeout=5000 quirks=0x80
'''


class mobot_video_feed():
	def __init__(self, camera_num, x, y):
		self.camera_num = camera_num
		self.x = x
		self.y = y
		self.camera = None
		self.frame_count = 0
		self.recovery_count = 0
		self.feed_num = 'video.' + str(camera_num )
		self.frame = None
		self.connection = None
		self.channel = None
		self.capture_time = 0.0
		self.run()

	def connect(self):
		self.connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
		self.channel = self.connection.channel()
		#channel.queue_declare(queue='mobot_video1', auto_delete=True, arguments={'x-message-ttl':1000})
		self.channel.exchange_declare(exchange='mobot_data_feed',type='topic')

		print self.feed_num
	'''
	 queue_declare(callback, queue='', passive=False, durable=False, exclusive=False, auto_delete=False, nowait=False, arguments=None)[source]

		Declare queue, create if needed. This method creates or checks a queue. When creating a new queue the client can specify various properties that control the durability of the queue and its contents, and the level of sharing for the queue.

		Leave the queue name empty for a auto-named queue in RabbitMQ
		Parameters:	

		    callback (method) - The method to call on Queue.DeclareOk
		    queue (str or unicode) - The queue name
		    passive (bool) - Only check to see if the queue exists
		    durable (bool)- Survive reboots of the broker
		    exclusive (bool)- Only allow access by the current connection
		    auto_delete (bool) - Delete after consumer cancels or disconnects
		    nowait (bool) - Do not wait for a Queue.DeclareOk
		    arguments (dict) - Custom key/value arguments for the queue

	'''

	def publish(self, data):
			self.channel.basic_publish(exchange='mobot_data_feed', 
								routing_key=self.feed_num, body=data)

	def enable_local_display(self):
		cv2.namedWindow('Front Camera', cv.CV_WINDOW_AUTOSIZE)
		#webcam1 =  cv.CreateCameraCapture(1)
		webcam1 = cv2.VideoCapture(1)
		cv2.imshow('Front Camera', frame1)	
		cv2.waitKey(30)


	def initialize_camera(self, camera_num, x, y):
			if camera_num <> "":
				self.camera = cv2.VideoCapture(camera_num)
				self.camera.set(cv2.cv.CV_CAP_PROP_FRAME_WIDTH, x) 
				self.camera.set(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT, y) 
				#self.camera1.set(cv2.cv.CV_CAP_PROP_FPS, 10)
	
	def run(self):
		self.connect()
		self.initialize_camera(self.camera_num, self.x, self.y)
		while True:
			time.sleep(0.0001) #dont hog resources
			self.frame = None
			self.frame_count += 1
			now = time.time()
			try:
				ret, self.frame = self.camera.read()
			except:
				pass
			self.capture_time = (time.time()-now)
			print 'frames:', self.frame_count , "   capture time:", self.capture_time, "   recovery_count:", self.recovery_count 
			if self.capture_time > 0.9 or self.frame == None:
				self.frame = None
				while self.frame == None:
					self.recovery_count += 1
					try:
						if self.camera != None:
							self.camera.release	
						gc.enable()
						gc.collect()			
						self.initialize_camera(self.camera_num, 320, 240)
						try:
							ret, self.frame = self.camera.read()
						except:
							pass
					except:
						time.sleep(.5)
						pass
			pickled_frame = pickle.dumps(self.frame,-1)
			self.publish(pickled_frame)

#connection.close()

