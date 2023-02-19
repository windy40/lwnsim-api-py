#!/bin/python 
#import time // check if a asyncio compatible version of time is not provided by asyncio
import sys
#import signal
import asyncio

import lwnsim_setup_async as lwnsim_setup

'''
#def sigint_handler(signum, frame):
def sigint_handler():
	print("KeyboardInterrupt received")
	print("LWNSim state="+str(lwnsim_setup.lwnsim.status))
	if lwnsim_setup.lwnsim.status==lwnsim_setup.LWNSim.ConnLinkDevOK:
		lwnsim_setup.lwnsim.unlink_dev()
		lwnsim_setup.lwnsim.disconnect()
		sys.exit()
	return

#signal.signal(signal.SIGINT, sigint_handler)
#print("Signal SIGINT handler setpup")
'''

async def send_recv_loop():
	s= lwnsim_setup.s
	s.settimeout(10)
	while True:
		await lwnsim_setup.lwnsim.sleep(3)
		s.setblocking(True)
		await s.send("Hello")
		print(">>>>>>>>>>>>>>>>>>>>>>Hello")
		
		await lwnsim_setup.lwnsim.sleep(8)

		s.setblocking(True)	
		data=await s.recv(2000)
		print ('<<<<<<<<<<<<<<<<<<<'+str(data))
	
async def main():
	
	await lwnsim_setup.setup()
	
	#lwnsim_setup.lwnsim.start_background_task(send_recv_loop())
	
	simple_io_task=asyncio.create_task(send_recv_loop())
	await simple_io_task
	
	await lwnsim_setup.lwnsim.wait()


	sys.exit()
	
asyncio.run(main())