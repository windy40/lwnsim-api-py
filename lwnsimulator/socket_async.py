from lwnsimulator import LoRa_async as LoRa


import json
import time
import asyncio

AF_LORA =1
SOCK_RAW=1

SOL_LORA=1
# socket options
SO_DR=1
SO_CONFIRMED= 2

def set_blocking_send_status():
	global lorawan_stack
	events = lorawan_stack.events()
	if events & LoRa.TX_PACKET_EVENT:
		socket.tx_packet_event=True
	if events & LoRa.TX_FAILED_EVENT:
		socket.tx_failed_event=True
	return

global lora_socket

class socket_async:
	
	def __init__(self, af, type, proto=0, log_enable=False):
		if af != AF_LORA or type != SOCK_RAW:
			return
		self.confirmed=False
		self.log_enable=log_enable
		self.stack = LoRa.lorawan_stack
		#self.stack.callback(trigger=(LoRa.TX_PACKET_EVENT | LoRa.TX_FAILED_EVENT), handler=self.set_blocking_send_status, arg=()
		self.timeout=None
		
	def log(self, msg):
		if self.log_enable:
			print('[socket]'+msg)

	def setsockopt(self, level, optname, value):
		if level != SOL_LORA:
			return
		if optname == SO_CONFIRMED:
			self.confirmed=value
		elif optname== SO_DR:
			self.dr=value

	def	setblocking(self, flag=False):
		if flag:
			self.timeout=None
		else:
			self.timeout=0.0

	def settimeout(self, value):
		self.timeout=value

	def close(self):
		pass

	async def send(self, data):
		msg={"MType": "UnconfirmedDataUp","Payload": data}
		if self.confirmed:
			msg.update({"MType": "ConfirmedDataUp"})
		self.log('[send]'+json.dumps(msg))

		await self.stack.send(msg)
		if self.timeout != 0.0:
			self.stack.create_event_fut(LoRa.TX_PACKET_EVENT|LoRa.TX_FAILED_EVENT)
			await self.stack.wait_for_event_fut(LoRa.TX_PACKET_EVENT|LoRa.TX_FAILED_EVENT, self.timeout)
			
			evt_seen=self.stack.result_event_fut(LoRa.TX_PACKET_EVENT|LoRa.TX_FAILED_EVENT)
			
			if evt_seen==LoRa.TX_PACKET_EVENT:
				self.log('[blocking send] sucess')
			if evt_seen==LoRa.TX_FAILED_EVENT:
				self.log('[blocking send] failed')
			self.stack.delete_event_fut(LoRa.TX_PACKET_EVENT|LoRa.TX_FAILED_EVENT)
		return

	async def recv(self, buffersize):
		msg={"BufferSize": buffersize}
		self.log('[recv]'+json.dumps(msg))
		
		recv_buf, err=await self.stack.recv( msg)
		if err==LoRa.LWNSim.DevErrorNoDataDWrecv and self.timeout != 0.0:
			self.stack.create_event_fut(LoRa.RX_PACKET_EVENT)
			await self.stack.wait_for_event_fut(LoRa.RX_PACKET_EVENT, self.timeout)
			recv_buf, err=await self.stack.recv( msg)
			self.stack.delete_event_fut(LoRa.RX_PACKET_EVENT)
		return recv_buf