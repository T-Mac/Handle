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