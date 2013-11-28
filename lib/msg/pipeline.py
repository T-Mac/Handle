import logging

LOGLVL = logging.DEBUG

logging.basicConfig(level=LOGLVL, format='%(asctime)s %(name)s %(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)

class Pipeline(object):
	def __init__(self):
		self.filters = []
		self.globalAspects = []
		self.filterAspects = {}
		self.gACompiled = None
	
	def Register(self, filter):
		self.filters.append(filter)
		
	def Execute(self, msg):
		for filter in self.filters:
			self.currentfilter = self.constructFilterAspects(filter) 
			if self.gACompiled:
				msg = self.gACompiled(msg)
			else:	
				msg = self.currentfilter(msg)
		return msg
	
	def addGlobalAspect(self, aspect):
		self.globalAspects.append(aspect)
		self.constructGlobalAspects()
		return True
		
	def addFilterAspect(self, aspect):
		filter = self.filters[len(self.filters)-1]
		if filter in self.filterAspects:
			self.filterAspects[filter].append(aspect)		
		else:
			self.filterAspects[filter] = [aspect]
		return True
	
	def constructGlobalAspects(self):
		saved = self.globalAspects.pop()
		lastaspect = saved(self.globalAspectRoot).Execute
		for aspect in reversed(self.globalAspects):
			lastaspect = aspect(lastaspect).Execute
		self.gACompiled = lastaspect
		self.globalAspects.append(saved)
		
	def constructFilterAspects(self, filter):
		if filter in self.filterAspects:
			saved = self.filterAspects[filter].pop()
			lastaspect = saved(filter.Execute).Execute
			for aspect in reversed(self.filterAspects[filter]):
				lastaspect = aspect(lastaspect).Execute
			self.filterAspects[filter].append(saved)
			return lastaspect
		else:
			return filter.Execute
	
	def globalAspectRoot(self, msg):
		msg = self.currentfilter(msg)
		return msg
		
		
class Filter(object):
	def Execute(self, msg):
		raise NotImplementedError
		
class Aspect(object):
	def __init__(self, action):
		self.action = action
		
	def Execute(self, msg):
		return self.action(msg)
			
#class FilterAspect(object):
	#def _init__(self, 
		
class DebugLoggingAspect(Aspect):
	def Execute(self, msg):
		logger.debug('Executing Aspect: %s'%__name__)
		return Aspect.Execute(self, msg)

class SPDebugger(Aspect):
	def Execute(self, msg):
		if msg.StopProcessing:
			print msg.error
		
class DummyFilter(Filter):
	def Execute(self, msg):
		return msg

		
class Message(object):
	def __init__(self,meta, command, data=None):
		self.StopProcessing = False
		self.error=None
		self.ReProcess = False
		self.meta = meta
		self.command = command
		self.data= data
	
	