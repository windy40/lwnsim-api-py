from lwnsimulator import lwnsimulator as LWNSim
import datetime
import json
# LoRa stack mode
LORAWAN = 1
# LoRaWAN region
EU868 =1
# LoRaWAN join procedure
ABP =0
OTAA =1
# LoRa triggers
RX_PACKET_EVENT=1
TX_PACKET_EVENT=2
TX_FAILED_EVENT=4
JOIN_ACCEPT_EVENT=16
UNJOIN_EVENT=32
lora_event_name=["RX_PACKET_EVENT","TX_PACKET_EVENT","TX_FAILED_EVENT","JOIN_ACCEPT_EVENT"]
# standard Python
#devEUI='359ac7cd01bc8aff'

global lorawan_stack

class LoRa:
	
	def __init__(self, mode, region, log_enable=False):
		self.lwnsim=LWNSim._LWNSim
		self.devEUI=self.lwnsim.linked_dev_mac()
		self.joined=False
		self.log_enable=log_enable
		self.last_event=0
		self.trigger=0
		self.handler=None
		self.arg=None

	def __del__(self):
		pass

	def log(self,msg):
		if self.log_enable:
			now=datetime.datetime.now()
			print(now.strftime("%Y-%m-%d %H:%M:%S")+' [LoRa]'+msg)
	
	def mac(self):
		return self.devEUI

	def join(self, activation, auth, timeout=None, dr=None):
		global lorawan_stack
		lorawan_stack=self
		msg={}
		if timeout!= None and timeout!=0:
			self.log('[join]join with timeout not implemented')
			return
		self.log('[join]')
		self.handle_user_data(LWNSim.CmdJoinRequest,msg)
		
	def has_joined(self):
		return self.joined
		
	def send(self,msg):
		self.handle_user_data(LWNSim.CmdSendUplink, msg)
	
	def recv(self, msg):
		self.clear_error_status()
		self.clear_recv_buf()
		self.handle_user_data(LWNSim.CmdRecvDownlink, msg, mode='call')
		recv_buf=self.get_recv_buf()
		err=self.get_error_status()
		if err != 0:
			self.log('[recv][ERROR]'+LWNSim.cmd_error_name[err])
		return recv_buf
		
	def handle_user_data(self, event, msg, mode='emit'):
		msg.update({"Cmd":event,"DevEUI": self.devEUI})
		self.log('['+event+']'+ json.dumps(msg))

		self.lwnsim.send_cmd(event, msg, mode)


	def callback(self, trigger, handler=None, arg=None):
		self.trigger=trigger
		self.handler=handler

	def events(self):
		evt=self.last_event
		self.last_event=0
		return evt
		
	def handle_lora_event(self, msg):
		if msg['event'] == JOIN_ACCEPT_EVENT:
			self.log('[Event]JoinAccept')
			self.joined=True
			return
		elif msg['event'] == UNJOIN_EVENT:
			self.log('[Event]Unjoin')
			self.joined=False
			return
		
		self.log('[Event]'+ str(msg['event']))
		self.last_event |= msg['event']
		if self.last_event & self.trigger:
			self.log('[Event] triggers a callback')
			self.handler()

	def set_recv_buf(self, data):
		self.recv_buf=data
		
	def get_recv_buf(self):
		buf=self.recv_buf
		self.clear_recv_buf()
		return buf

	def clear_recv_buf(self):
		self.recv_buf=""

	def set_error_status(self, error):
		self.error_status |= error

	def get_error_status(self):
		err=self.error_status
		self.clear_error_status()
		return err

	def clear_error_status(self):
		self.error_status=0
