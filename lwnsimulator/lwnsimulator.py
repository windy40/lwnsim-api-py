import socketio
import time
import json
#import sys
#import base64
#import pprint
from lwnsimulator import LoRa

global _LWNSim
# connection status
ConnSimNOK=0
ConnInit=1
ConnOK=2
ConnLinkDevNOK=2
ConnLinkDevInit=3
ConnLinkDevOK=4 # usefull ?
ConnSimOK=4
ConnUnlinkDevInit=5
ConnUnlinkDevOK=6
ConnDisInit=7



# sim commands
CmdLinkDev="link-dev"
CmdUnlinkDev="unlink-dev"
CmdJoinRequest="join-request"
CmdSendUplink="send-uplink"
CmdRecvDownlink="recv-downlink"

CMD_TIMEOUT=10
# response-cmd errors
cmd_error_name=["DevCmdOK", "DevCmdTimeout", "NoDeviceWithDevEUI", "NIY", "DeviceNotlinked", "DeviceTurnedOff", "DeviceNotJoined","DeviceAlreadyJoined","RecvBufferEmpty" ]



#sio_hdr={"devEUI": devEUI}
sio=socketio.Client(reconnection=True, request_timeout=10, logger=False,engineio_logger=False )

@sio.event(namespace='/')
def connect():
	global _LWNSim
	_LWNSim.log("[Socket.io][ns='/'] connected")

@sio.event(namespace='/')
def connect_error(data):
	global _LWNSim
	_LWNSim.log("[Socket.io][ns='/'] connection failed")

@sio.event(namespace='/')
def disconnect():
	global _LWNSim
	_LWNSim.log("[Socket.io][ns='/'] disconnected")

ns='/dev'

@sio.event(namespace=ns)
def connect():
	global _LWNSim
	_LWNSim.status=ConnOK
	_LWNSim.log("[Socket.io][ns="+ns+"] connected")
	_LWNSim.link_dev()


@sio.event(namespace=ns)
def connect_error(data):
	global _LWNSim
	_LWNSim.log("[Socket.io][ns="+ns+"] connection failed")

@sio.event(namespace=ns)
def disconnect():
	global _LWNSim
	_LWNSim.log("[Socket.io][ns="+ns+"] disconnected")
#	_LWNSim.unlink_dev()
	_LWNSim.status=ConnSimNOK


@sio.on("response-cmd", namespace=ns)
def response_cmd(msg):
	global _LWNSim
	if msg['error']!=0 :
		_LWNSim.handle_error_resp(msg)
	else:
		_LWNSim.handle_ok_resp(msg)


@sio.on("ack-cmd", namespace=ns)
def ack_cmd(msg):
	global _LWNSim
	_LWNSim.log("[CMD_ACK]["+msg['cmd']+"]"+msg['args'])

@sio.on("dev-log", namespace=ns)
def dev_log(msg):
    _LWNSim.log("[LOG]"+msg)
    


@sio.on("dev-error", namespace=ns)
def dev_error(msg):
	global _LWNSim
	_LWNSim.log("[ERROR]"+msg)
    
@sio.on('*', namespace=ns)
def catch_all(event, data):
    pass
    
@sio.on("recv-dwlink", namespace=ns)
def recv_dwlink(msg):
	global _LWNSim
	_LWNSim.log("[RECV_DWLINK]")
	
@sio.on("lora-event", namespace=ns)
def lora_event(msg):
	#global lorawan_stack
	LoRa.lorawan_stack.handle_lora_event(msg)
	
@sio.on("sim-event", namespace=ns)
def sim_event(msg):
	global _LWNSim
	_LWNSim.handle_sim_event(msg)
	
socket_headers={
	'Accept':['*/*'],
	'Accept-Encoding':['gzip', 'deflate'] ,
	'Connection':['keep-alive'],
	'User-Agent':['python-requests/2.26.0']}
	
class lwnsimulator:
	def __init__(self,url, ack_cmd= False,log_enable=False):
		global ns
		self.url=url
		self.sio=sio
		self.status= ConnSimNOK
		self.namespace=ns
		self.ack_cmd=ack_cmd
		self.log_enable=log_enable

	def connect(self, mac):
		global _LWNSim
		_LWNSim=self
		self.DevEUI=mac
		self.status= ConnInit
		self.sio.connect(self.url,headers={})

	def disconnect(self):
		self.status= ConnDisInit
		self.sio.disconnect()

	def log(self, msg):
		if self.log_enable:
			print('[LWSIM]'+msg)
			
# called on connect event
	def link_dev(self):
		self.status= ConnLinkDevInit
		self.send_cmd(CmdLinkDev,{"DevEUI": self.DevEUI}, mode='call')
		self.status= ConnSimOK

	def unlink_dev(self):
		self.status= ConnUnlinkDevInit
		self.send_cmd(CmdUnlinkDev,{"DevEUI": self.DevEUI})
		self.status=ConnUnlinkDevOK

	def linked_dev_mac(self):
		return self.DevEUI

	def send_cmd(self, cmd, msg, mode='emit'):
		if self.ack_cmd:
			msg.update({'Ack': True})
		else:
			msg.update({'Ack': False})
		msg.update({'Cmd':cmd})
		if mode=='emit':
			self.log('[CMD_EMIT]['+cmd+']'+json.dumps(msg))
			self.sio.emit(cmd, msg, namespace=self.namespace)
		else:
			self.log('[CMD_CALL]['+cmd+']'+json.dumps(msg))
			try:
				resp=self.sio.call(cmd, msg, namespace=self.namespace)
				self.log('[CMD_CALL_ACK]['+cmd+']'+json.dumps(resp))
				if resp['error']!=0 :
					self.handle_error_resp(resp)
				else:
					self.handle_ok_resp(resp)
			except socket.exceptions.TimeoutError:
				self.log('[CMD_CALL]['+cmd+'][EXC] Timeout')
				pass

	def handle_error_resp(self,msg):
		_LWNSim.log('[CMD_RESP]['+msg['cmd']+'][ERROR] '+ cmd_error_name[msg['error']])
		if msg['cmd']==CmdLinkDev:
			_LWNSim.status=ConnLinkDevNOK
		elif msg['cmd'] in ["CmdJoinRequest","CmdSendUplink","CmdRecvDownlink"]:
			LoRa.lorawan_stack.set_error_status(msg['error'])
		elif msg['cmd'] == "CmdRecvDownlink":
			LoRa.lorawan_stack.set_error_status(msg['error'])
			LoRa.lorawan_stack.set_recv_buf(msg['payload'])

	def handle_ok_resp(self,msg):
		_LWNSim.log("[CMD_RESP]["+msg['cmd']+"]"+json.dumps(msg))
		if msg['cmd']==CmdLinkDev:
			_LWNSim.status=ConnLinkDevOK
		elif msg['cmd']==CmdRecvDownlink:
			LoRa.lorawan_stack.set_error_status(msg['error'])
			LoRa.lorawan_stack.set_recv_buf(msg['payload'])

	def handle_sim_event(msg):
		_LWNSim.log("[Event]["+msg['event']+"]"+json.dumps(msg))

	def test(self,data):
		msg={"DevEUI": self.DevEUI,"MType": "UnconfirmedDataUp","Payload": data}
		self.send_cmd(CmdSendUplink,msg)

	def __del__(self):
		if self.sio.connect:
			self.sio.disconnect()
			time.sleep(2)
		del(self.sio)


	