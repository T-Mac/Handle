import pipeline

class FormatAspect(object):
	def __init__(self, action):
		self.pipeline = pipeline.Pipeline()
		self.pipeline.Register(check_format())
		
	def Execute(self, msg):
		for filter in filters:
			msg = filter.Execute(msg)
		return msg
		

		
		
		
		
		
class check_format(Filter):
	def Execute(self, msg):
		if msg.meta:
			if msg.command:
				return msg
				
		msg.StopProcessing = True
		msg.error = 'MALFORMED'
		return msg
		