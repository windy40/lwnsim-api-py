import time
import sys
import binascii

#--- how to setup the device to use the LoRaWAN simulator 
from lwnsimulator import lwnsimulator as LWNSim
from lwnsimulator import LoRa
from lwnsimulator import socket

import signal

global s
global lwnsim

def sigint_handler(signum, frame):
	global lwnsim
	print("KeyboardInterrupt received")
	print("LWNSim state="+str(lwnsim.status))
	if lwnsim.status==LWNSim.ConnSimOK:
		lwnsim.unlink_dev()
		lwnsim.disconnect()
		sys.exit()
	return
signal.signal(signal.SIGINT, sigint_handler)

lwnsim_url= "http://127.0.0.1:8000"
devEUI='359ac7cd01bc8aff'

lwnsim = LWNSim.lwnsimulator(lwnsim_url,ack_cmd=True, log_enable=True)
lwnsim.connect(devEUI)

time.sleep(3)

lora=LoRa.LoRa( mode=LoRa.LORAWAN, region=LoRa.EU868, log_enable=True)
time.sleep(3)
# create an OTAA authentication parameters
app_eui = binascii.unhexlify('0000000000000000'.replace(' ',''))
app_key = binascii.unhexlify('2CC172969D5CC26382E0AD054568CE3E'.replace(' ',''))    
lora.join(activation=LoRa.OTAA, auth=(app_eui, app_key),  timeout=0)

while not lora.has_joined():
	time.sleep(2.5)
	print('Not yet joined...')

s=socket.socket(socket.AF_LORA, socket.SOCK_RAW, log_enable=True)
s.setsockopt(socket.SOL_LORA, socket.SO_DR, 5)
s.setsockopt(socket.SOL_LORA,  socket.SO_CONFIRMED,  True)

 
time.sleep(5)

