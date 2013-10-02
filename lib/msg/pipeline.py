import logging


class Pipeline(object):
	filters = []
	def Register(self, filter):
		self.filters.append(filter)
		
	def Execute(self, msg):
		for filter in self.filters:
			msg = filter.Execute(msg)
		return msg
		
		
class Filter(object):
	def Execute(self, msg):
		raise NotImplementedError
		
class Aspect(object):
	def __init__(self, action):
		self.action = action
		
class DebugLoggingAspect(object):
	def __init__(self, action, logger):
		self.action=action
		self.logger = logger
		
	def Execute(self, msg):
		self.logger.debug('test')
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
	
	