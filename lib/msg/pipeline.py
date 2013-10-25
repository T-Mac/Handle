import logging

LOGLVL = logging.DEBUG

logging.basicConfig(level=LOGLVL, format='%(asctime)s %(name)s %(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)

class Pipeline(object):
	filters = []
	def Register(self, filter):
		self.filters.append(filter)
		
	def Execute(self, msg):
		for filter in self.filters:
			logger.debug('Executing: %s'%str(filter))
			msg = filter.Execute(msg)
		return msg
		
		
class Filter(object):
	def Execute(self, msg):
		raise NotImplementedError
		
class Aspect(object):
	def __init__(self, action):
		self.action = action
		
class DebugLoggingAspect(object):
	def __init__(self, action):
		self.action=action
		
		
	def Execute(self, msg):
		logger.debug('GOT: %s'%str(msg))
		self.action(msg)

class SPDebugger(Aspect):
	def Execute(self, msg):
		if msg.StopProcessing:
			print msg.error
		

		
class Message(object):
	def __init__(self,meta, command, data=None):
		self.StopProcessing = False
		self.error=None
		self.ReProcess = False
		self.meta = meta
		self.command = command
		self.data= data
	
	