from twisted.internet import reactor
from twisted.internet.endpoints import TCP4ServerEndpoint
import threading
import logging
module_logger = logging.getLogger(__name__)
from backend import ServerFactory

class Server(threading.Thread):
	def __init__(self, receiveCallback=None):
		self.logger = module_logger.getChild(self.__class__.__name__)
		self.receiveCallback = receiveCallback
		self.factory = ServerFactory(self.receiveCallback)
		
		threading.Thread.__init__(self)
		
	def setup(self, host, port):
		self.endpoint = TCP4ServerEndpoint(reactor, port)
		self.endpoint.listen(self.factory)
					
	def run(self):
		self.logger.debug('Listening....')
		reactor.run(installSignalHandlers=0)
		
	def send(self, line):
		self.factory.send(line)
		
	def stop(self):
		reactor.callFromThread(reactor.stop)
		
	def join(self):
		self.stop()
		threading.Thread.join(self)
	