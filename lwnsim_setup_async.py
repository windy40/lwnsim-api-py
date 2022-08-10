import time
import sys
import binascii
import signal
import asyncio

#--- how to setup the device to use the LoRaWAN simulator 
from lwnsimulator import lwnsimulator_async as LWNSim
from lwnsimulator import LoRa_async as LoRa
from lwnsimulator import socket_async as socket



global lwnsim, lora, s

'''
On Windows, KeyboardInterrupt raises an excpetion 
On Unix, KeyboardInterrupt handled as signal SIGINT ?
#def sigint_handler(signum, frame):
def sigint_handler():
	global lwnsim
	print("KeyboardInterrupt received")
	print("LWNSim state="+str(lwnsim.status))
	if lwnsim.status==LWNSim.ConnSimOK:
		lwnsim.unlink_dev()
		lwnsim.disconnect()
		sys.exit()
	return

#signal.signal(signal.SIGINT, sigint_handler)
# with asyncio :
	loop=asyncio.get_event_loop()
	loop.add_signal_handler(getattr(signal,'SIGINT'), sigint_handler())

#print("Signal SIGINT handler setup")
'''
async def setup():
	global lwnsim, s
	#signal.signal(signal.SIGINT, sigint_handler)
	lwnsim_url= "http://127.0.0.1:8000"
	devEUI='359ac7cd01bc8aff'

	lwnsim = LWNSim.lwnsimulator_async(lwnsim_url,ack_cmd=False, log_enable=True)
	

	await lwnsim.connect_and_link_dev(devEUI)
	
	while not lwnsim.connected:
		lwnsim.log("[SETUP]Not yet connected...")
		await lwnsim.sleep(1)
		
	
	#await lwnsim.link_dev()
	#await lwnsim.sleep(3)

	lora=LoRa.LoRa_async( mode=LoRa.LORAWAN, region=LoRa.EU868, log_enable=True)
	
	#await lwnsim.sleep(3)
	
	# create an OTAA authentication parameters
	app_eui = binascii.unhexlify('0000000000000000'.replace(' ',''))
	app_key = binascii.unhexlify('2CC172969D5CC26382E0AD054568CE3E'.replace(' ',''))    
	
	#await lora.join(activation=LoRa.OTAA, auth=(app_eui, app_key),  timeout=0)

	#while not lora.has_joined():
	#	lwnsim.log("[SETUP]Not yet joined...")
	#	await lwnsim.sleep(2.5)
		
	try:
		await lora.join(activation=LoRa.OTAA, auth=(app_eui, app_key),  timeout=10)
		lwnsim.log("[SETUP] device joined")
	except asyncio.TimeoutError:
		lwnsim.log("[SETUP] timeout while trying to join")

	s=socket.socket_async(socket.AF_LORA, socket.SOCK_RAW, log_enable=True)
	s.setsockopt(socket.SOL_LORA, socket.SO_DR, 5)
	s.setsockopt(socket.SOL_LORA,  socket.SO_CONFIRMED,  True)

	 
	await lwnsim.sleep(5)

