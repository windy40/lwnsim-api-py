#!/bin/python 
import time
import sys

import lwnsim_setup

s= lwnsim_setup.s

while True:
	time.sleep(10)
	s.setblocking(False)
	s.send("Hello")
	print("Hello")
	
	time.sleep(0)
	s.setblocking(True)	
	data=s.recv(2000)
	print (data)



time.sleep(60)
s.close()
time.sleep(5)
sys.exit()