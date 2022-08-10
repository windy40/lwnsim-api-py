"""
This program runs on Python3 in terminal mode and Lopy4. On LoPy4, it sends
information either on LoRaWAN Networks, Sigfox or Wi-Fi. Selection is done
with the variable SERVER (see below). If a BME280 is connected to the LoPY,
measurement are taken from the sensor, otherwise sensor's behavior is emulated.
On python terminal values are emulated.

Data are sent with CoAP on 4 different URI /temperature, /pressure, /humidity,
/memory. On Sigfox, the SCHC compression of the CoAP header is provided and only
one parameter is sent (it can be changed in the code). On LoRaWAN and Wi-Fi all
the parameters are sent on a full CoAP message. Downlink is limited to error
messages (4.xx and 5.xx) and not taken into account by the program.

"""
SERVER = "LWNSIM"
#SERVER = "LORAWAN" # change to your server's IP address, or SIGFOX or LORAWAN
#SERVER = "LORAWAN_STACK" # configurable stack 
#SERVER="SIGFOX"
#SERVER = "192.168.1.XX" # change to your server's IP address, or SIGFOX or LORAWAN
PORT   = 5683 # port serveur COAP par defaut
destination = (SERVER, PORT)

# import CoAP # DW imported below depending on server


import time
import sys
import binascii
upython = (sys.implementation.name == "micropython")
print (upython, sys.implementation.name)
if upython:
	import kpn_senml.cbor_encoder as cbor #pycom
	import pycom
	import gc
	import struct
else:
	import cbor2 as cbor  # terminal on computer
	import psutil

#----- CONNECT TO THE APPROPRIATE NETWORK --------



sigfox = False
if SERVER == "LWNSIM":
	from lwnsimulator import lwnsimulator as LWNSim
	from lwnsimulator import LoRa
	from lwnsimulator import socket

	import signal
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

elif (SERVER == "LORAWAN") and (not upython):
	import socket
	from network import LoRa
	import CoAP

	lora = LoRa(mode=LoRa.LORAWAN, region=LoRa.EU868)
	#
	mac = lora.mac()
	print ('devEUI: ',  binascii.hexlify(mac))

	# create an OTAA authentication parameters
	app_eui = binascii.unhexlify('0000000000000000'.replace(' ',''))
	app_key = binascii.unhexlify('2CC172969D5CC26382E0AD054568CE3E'.replace(' ',''))   # Acklio
	lora.join(activation=LoRa.OTAA, auth=(app_eui, app_key),  timeout=0)

	pycom.heartbeat(False) # turn led to white
	pycom.rgbled(0x101010) # white

	# wait until the module has joined the network
	while not lora.has_joined():
		time.sleep(2.5)
		print('Not yet joined...')

	pycom.rgbled(0x000000) # black

	s = socket.socket(socket.AF_LORA, socket.SOCK_RAW)
	s.setsockopt(socket.SOL_LORA, socket.SO_DR, 5)
	s.setsockopt(socket.SOL_LORA,  socket.SO_CONFIRMED,  False)

	send_ack= CoAP.send_ack

	MTU = 200 # Maximun Transmission Unit, for DR 0 should be set to less than 50

elif SERVER == "LORAWAN_STACK":
	import socket
	# configure stack
	import L2_LORA
	import L_COAP as CoAP

	l2= L2_LORA.L2_LORAWAN()

	l_coap_m= CoAP.L_COAP_M()
	l2.set_ul(l_coap_m)
	l_coap_m.set_ll(l2)

	l_coap_s= CoAP.L_COAP_S()
	l_coap_m.set_ul(l_coap_s)
	l_coap_s.set_ll(l_coap_m)

	s= None
	send_ack= l_coap_s.send_ack

	MTU = 200 # Maximun Transmission Unit, for DR 0 should be set to less than 50

elif SERVER == "SIGFOX":
	import socket
	from network import Sigfox
	import CoAP

	# initalise Sigfox for RCZ1 (You may need a different RCZ Region)
	sfx = Sigfox(mode=Sigfox.SIGFOX, rcz=Sigfox.RCZ1)
	s = socket.socket(socket.AF_SIGFOX, socket.SOCK_RAW)

	MTU = 12
	print ("SIGFOX", binascii.hexlify(sfx.id()))
	sigfox = True
	send_ack= CoAP.send_ack

else: # WIFI with IP address
	import socket
	import COAP

	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	MTU = 200 # maximum packet size, could be higher

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
