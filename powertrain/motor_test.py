from robomow_motor_class_arduino import *


motor1 = robomow_motor()
print "motor1.isConnected:", motor1.isConnected
print motor1.com_stats()
motor1.right(10)
print motor1.motor1_speed
print motor1.motor2_speed
#time.sleep(1)
motor1.left(90)
print motor1.motor1_speed
print motor1.motor2_speed

'''
for i in xrange(0, 101, 100):
	print "forward"
	print motor1.forward(i)
	time.sleep(1)
	print "l/r motors speeds: ", motor1.lmotor_speed, motor1.rmotor_speed 

	print "reverse"
	print motor1.reverse(i)
	time.sleep(1)
	print "l/r motors speeds: ", motor1.lmotor_speed, motor1.rmotor_speed

	print "left"
	print motor1.left(i)
	time.sleep(1)
	print "l/r motors speeds: ", motor1.lmotor_speed, motor1.rmotor_speed

	print "right"
	print motor1.right(i)
	time.sleep(1)
	print "l/r motors speeds: ", motor1.lmotor_speed, motor1.rmotor_speed 

	print "STOP"
	print motor1.stop()
	time.sleep(1)
	print "l/r motors speeds: ", motor1.lmotor_speed, motor1.rmotor_speed 
'''
