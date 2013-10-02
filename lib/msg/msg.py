import pipeline

class Construct(pipeline.Pipeline):
	def New(self, meta, command, data=None):
		msg = pipeline.Message(meta, command, data)
		print msg
		msg = self.Execute(msg)
		print msg
		return msg
		
	def Execute(self, msg):
		msg = pipeline.SPDebugger(pipeline.Pipeline.Execute).Execute(msg)
		return msg
		
class generic_format(pipeline.Filter):
	def Execute(self, msg):
		if msg.meta:
			if msg.command:
				if msg.data or msg.data == None:
					return msg
		msg.StopProcessing = True
		msg.error = 'Malformed'
		return msg