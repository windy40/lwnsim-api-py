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
		else
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
		if self.blocking:
			events=self.stack.events()
			while not (events&LoRa.TX_PACKET_EVENT) and not(events&LoRa.TX_FAILED_EVENT) :
				await asyncio.sleep(1)
				events=self.stack.events()
			if events & LoRa.TX_PACKET_EVENT:
				self.log('[blocking send] sucess')
			if events & LoRa.TX_FAILED_EVENT:
				self.log('[blocking send] sucess')
		return

	async def recv(self, buffersize):
		msg={"BufferSize": buffersize}
		self.log('[recv]'+json.dumps(msg))
		recv_buf=await self.stack.recv( msg)
		if recv_buf=="" and self.blocking:
			while not self.stack.events() & LoRa.RX_PACKET_EVENT:
				await asyncio.sleep(2.5)
			recv_buf=await self.stack.recv( msg)
		return recv_buf


		