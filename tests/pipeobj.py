import lib.msg.pipeline as pipeline

class SimpleFilter(pipeline.Filter):
	def Execute(self, msg):
		msg = msg + 1
		print str(msg)
		return msg
		
class SimpleAspect(pipeline.Aspect):
	def Execute(self, msg):
		print 'Before: %s'%str(msg)
		msg = self.action(msg)
		print 'After: %s'%str(msg)
		return msg
		
		
class RetryFilter(pipeline.Filter):
	def Execute(self, msg):
		print 'Received: %s'%str(msg.num)
		msg.num = msg.num+1
		if msg.num != 5:
			msg.Retry = True
			print 'Retrying'
		return msg
		
class RetryAspect(pipeline.Aspect):
	def __init__(self, action):
		self.action = action
		self.max = 5
		self.current = 0
	def Execute(self, msg):
		r = self.action(msg)
		if r.Retry:
			self.current = self.current+1
			if self.current <= self.max:
				msg.Retry = False
				self.Execute(msg)
			else:
				msg.StopProcessing = True
		else:
			msg = r
		return msg
			
class TestMsg(object):
	def __init__(self):
		self.num = 0
		self.Retry = False