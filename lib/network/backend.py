import logging
from twisted.internet.protocol import Factory, Protocol, ReconnectingClientFactory
from twisted.protocols.basic import LineReceiver, LineOnlyReceiver
from twisted.internet import reactor
import threading
module_logger = logging.getLogger(__name__)


class NetworkProtocol(LineOnlyReceiver):
	def __init__(self):
		self.logger = module_logger.getChild(self.__class__.__name__)
		self.peer = None
		
	def connectionMade(self):
		self.peer = self.transport.getPeer().host
		self.logger.debug('Connected to %s'%self.peer)
		self.factory.onConnect(self)
		
	def connectionLost(self, reason):
		self.factory.onDisconnect(self)
		self.logger.debug('Connection Lost - %s'%self.peer)
		
	def lineReceived(self, line):
		self.logger.debug('Received: %s'%line.strip())
		self.factory.onReceive(line)
		

class NetworkAction(object):
	def __init__(self, receiveCallback = None):
		self.logger = module_logger.getChild(self.__class__.__name__)
		self.connections = []
		self.connected = False
		self.receiveCallback = receiveCallback
		
	def onConnect(self, connection):
		self.connections.append(connection)
		self.connected = True
		self.logger.debug('Connected to: %s'%connection.peer)
		
	def onDisconnect(self, connection):
		try:
			self.connections.remove(connection)
		except ValueError:
			pass
			
		if len(self.connections) == 0:
			self.connected = False
		self.logger.debug('%s Disconnected'%connection.peer)
					
	def onReceive(self, line):
		if self.receiveCallback:
			self.receiveCallback(line)
		else:
			self.logger.debug('No Callback - Printing: %s'%line)
			
	def send(self, line):
		if self.connected:
			for connection in self.connections:
				reactor.callFromThread(connection.sendLine, line)
				self.logger.debug('%s - Sent: %s'%(connection.peer, line))
		else:
			self.logger.debug('Not Connected - Dropping: %s'%line)
			
class ServerFactory(NetworkAction, Factory):
	def buildProtocol(self, addr):
		conn = NetworkProtocol()
		conn.factory = self
		return conn

class ClientFactory(NetworkAction, ReconnectingClientFactory):
	def startedConnecting(self, connector):
		self.logger.debug('Connecting')
		
	def buildProtocol(self, addr):
		self.resetDelay()
		conn = NetworkProtocol()
		conn.factory = self
		return conn
		
		
		
			