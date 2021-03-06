#!/usr/bin/python

import dbus
import time
import thread
import pika
''' 
	Pulbishes signal strength of given SSID

USAGE:
	signal_strength(SSID)
	
	wlist = WiFiList()
	while True:
		time.sleep(.0001)
		print wlist.signal_strength('isotope11_wireless')
'''

class WiFiList():
	def __init__(self):
		self.NM = 'org.freedesktop.NetworkManager'
		self.has_nm = True
		self.strength = None
		self.aps = []
		try:
			self.bus = dbus.SystemBus()
			nm = self.bus.get_object(self.NM, '/org/freedesktop/NetworkManager')
			self.devlist = nm.GetDevices(dbus_interface = self.NM)	
			#-------------connection variables
			self.channel_name = 'wifi.1'
			self.connection = None
			self.channel = None
			#----------------------RUN
			self.run()	  
		except:
			self.has_nm = False	

		
	
	def dbus_get_property(self, prop, member, proxy):
		return proxy.Get(self.NM+'.' + member, prop, dbus_interface = 'org.freedesktop.DBus.Properties')

	def repopulate_ap_list(self):
		apl = []
		res = []
		for i in self.devlist:
		    tmp = self.bus.get_object(self.NM, i)
		    if self.dbus_get_property('DeviceType', 'Device', tmp) == 2:
		        apl.append(self.bus.get_object(self.NM, i).GetAccessPoints(dbus_interface = self.NM+'.Device.Wireless'))
		for i in apl:
		    for j in i:
		        res.append(self.bus.get_object(self.NM, j))
		return res

	def update(self):
		self.aps = []
		if self.has_nm:
			for i in self.repopulate_ap_list():
				try:
					ssid = self.dbus_get_property('Ssid', 'AccessPoint', i)
					ssid = "".join(["%s" % k for k in ssid])
					ss = self.dbus_get_property('Strength', 'AccessPoint', i);
					mac = self.dbus_get_property('HwAddress', 'AccessPoint', i);
					#self.aps.append({"mac":str(mac), "ssid": unicode(ssid), "ss": float(ss)})
					self.aps.append([str(unicode(ssid)), int(ss)])
				except:
					pass
	
	def signal_strength(self, ssid):
			to_return = -1
			self.update()
			#filter(lambda x: 'abc' in x,lst)
			for i in self.aps:
				if i[0] == ssid: 
					to_return = i[1]
			self.publish(str(to_return))	
			return to_return
	
	def run(self):
		self.connect()
		#self.th = thread.start_new_thread(self.update, ())

	def connect(self):
		self.connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
		self.channel = self.connection.channel()
		self.channel.exchange_declare(exchange='mobot_data_feed',type='topic')	
		#self.channel.queue_declare(queue='mobot_wifi', auto_delete=True, arguments={'x-message-ttl':100})
		#self.channel.queue_bind(queue='mobot_wifi', exchange='mobot_data_feed', auto_delete=True, arguments={'x-message-ttl':1000})
	
	def publish(self, data):
			self.channel.basic_publish(exchange='mobot_data_feed', routing_key=self.channel_name,  body=data, properties=pika.BasicProperties(expiration=str(100)))


if __name__ == "__main__":
	wlist = WiFiList()
	i = 0
	while True:
		time.sleep(.0001)
		print wlist.signal_strength('isotope11_wireless'), i
		i += 1
	
	
