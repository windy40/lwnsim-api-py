from lwnsimulator import lwnsimulator_async as LWNSim

import json
import asyncio

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

class LoRa_async:
	
	def __init__(self, mode, region, log_enable=False):
		self.lwnsim=LWNSim._LWNSim
		self.devEUI=self.lwnsim.linked_dev_mac()
		self.joined=False
		self.events_fut=dict()
		self.log_enable=log_enable
		self.last_event=0
		self.trigger=0
		self.handler=None
		self.arg=None

	def __del__(self):
		pass

	def log(self,msg):
		if self.log_enable:
			print('[LoRa]'+msg)
	
	def mac(self):
		return self.devEUI

	async def join(self, activation, auth, timeout=None, dr=None):
		global lorawan_stack 
		lorawan_stack = self
		msg={}
		self.log('[join]')
		if timeout != None and timeout != 0 :
			self.log('[join] timeout= '+str(timeout))
			self.create_event_fut(JOIN_ACCEPT_EVENT)
		await self.process_user_data(LWNSim.CmdJoinRequest,msg)
		if timeout != None and timeout != 0 :
			await self.wait_for_event(JOIN_ACCEPT_EVENT,timeout)
		
		
	def has_joined(self):
		return self.joined
		
	async def send(self,msg):
		await self.process_user_data(LWNSim.CmdSendUplink, msg)
	
	async def recv(self, msg):
		self.clear_error_status()
		self.clear_recv_buf()
		await self.process_user_data(LWNSim.CmdRecvDownlink, msg, mode='call')
		recv_buf=self.get_recv_buf()
		err=self.get_error_status()
		if err != 0:
			self.log('[recv][ERROR]'+LWNSim.cmd_error_name[error])
		return recv_buf
		
	async def process_user_data(self, event, msg, mode='emit'):
		msg.update({"Cmd":event,"DevEUI": self.devEUI})
		self.log('['+event+']'+ json.dumps(msg))
		await self.lwnsim.send_cmd(event, msg, mode)


	def callback(self, trigger, handler=None, arg=None):
		self.trigger=trigger
		self.handler=handler

	def events(self):
		evt=self.last_event
		self.last_event=0
		return evt
		
	def process_lora_event(self, msg):
		self.log('[Event]'+ str(msg['event']))
		# process futures when appropriate
		if msg['event'] == JOIN_ACCEPT_EVENT:
			self.joined=True
			if JOIN_ACCEPT_EVENT in self.events_fut.keys():
				self.set_result_event_fut(JOIN_ACCEPT_EVENT,1)
		elif msg['event'] == UNJOIN_EVENT:
			self.joined=False
		elif msg['event'] == TX_PACKET_EVENT:
			self.set_result_event_fut(TX_PACKET_EVENT,TX_PACKET_EVENT)
			self.set_result_event_fut(TX_PACKET_EVENT|TX_FAILED_EVENT,TX_PACKET_EVENT)
		elif msg['event'] == TX_FAILED_EVENT:
			self.set_result_event_fut(TX_FAILED_EVENT,TX_FAILED_EVENT)
			self.set_result_event_fut(TX_PACKET_EVENT|TX_FAILED_EVENT,TX_FAILED_EVENT)
		elif msg['event'] == RX_PACKET_EVENT:
			pass
		
		self.last_event |= msg['event']
		if self.last_event & self.trigger:
			self.log('[Event] triggers a callback NIY')
			#self.handler()
			
	def create_event_fut(self, evt):
		if  not evt in self.events_fut.keys():
			loop=asyncio.get_running_loop()
			self.events_fut[evt]=loop.create_future()

	def delete_event_fut(self, evt):
		if evt in self.events_fut.keys():
			self.events_fut.pop(evt,None)
			
	def set_result_event_fut(self, evt, result=0):
		if evt in self.events_fut.keys():
			self.events_fut[evt].set_result(result)
	
	async def wait_for_event(self, evt, timeout):
		if (not evt in self.events_fut.keys()) or self.events_fut[evt].done():
			return
		await asyncio.wait_for(self.events_fut[evt], timeout)
		self.delete_event_fut(evt)


			

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
