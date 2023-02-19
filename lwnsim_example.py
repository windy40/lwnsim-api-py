#!/bin/python
import time
import sys

import lwnsim_setup

s = lwnsim_setup.s

while True:

	s.settimeout(10)

	s.setblocking(False)
	try:
		s.send("Hello")
		print("Hello")
	except lwnsim_setup.socket.TimeoutError :
		print("send timeout")

	time.sleep(1)

	try :
		s.setblocking(True)
		data = s.recv(2000)
		print(data)
	except lwnsim_setup.socket.TimeoutError :
		print("recv timeout")



time.sleep(60)
s.close()
time.sleep(5)

lwnsim_setup.lwnsim.disconnect()
exit()
