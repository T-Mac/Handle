from backend import ClientFactory
from twisted.internet import reactor
from twisted.internet.endpoints import TCP4ClientEndpoint
import threading
import logging
module_logger = logging.getLogger(__name__)


class Client(threading.Thread):
	def __init__(self, receiveCallback = None):
		self.logger = module_logger.getChild(self.__class__.__name__)
		self.receiveCallback = receiveCallback
		self.factory = ClientFactory(self.receiveCallback)
		threading.Thread.__init__(self)
		
	def setup(self, host, port):
		self.endpoint = TCP4ClientEndpoint(reactor, host, port)
		self.endpoint.connect(self.factory)
		
	def run(self):
		self.logger.debug('Connecting.....')
		reactor.run(installSignalHandlers=0)

	def send(self, line):
		self.factory.send(line)
		
		
	def stop(self):
		reactor.callFromThread(reactor.stop)
		
	def join(self):
		self.stop()
		threading.Thread.join(self)