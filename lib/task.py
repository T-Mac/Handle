class Task(object):
	'''
	HDL_COMMAND			line
	HDL_EXIT			None
	HDL_UPDATE			None
	HDL_CHECKUP			None
	NET_JOB				None
	NET_SCREEN			None
	NET_VERSION			None
	NET_LINEUP			line
	SRV_START			None
	SRV_STOP			None
	SRV_RESTART			None
	SRV_INPUT			line
	CLT_UPDATE			data
	CLT_INPUT			line
	CLT_LINEUP			line
	'''
	HDL_COMMAND, HDL_EXIT, HDL_UPDATE, HDL_CHECKUP, NET_JOB, NET_SCREEN, NET_VERSION, NET_LINEUP, SRV_START, SRV_STOP, SRV_RESTART, SRV_INPUT, CLT_UPDATE, CLT_INPUT, CLT_LINEUP  = range(15)
	stype = {
		0:'HDL_COMMAND',
		1:'HDL_EXIT',
		2:'HDL_UPDATE',
		3:'HDL_CHECKUP',
		4:'NET_JOB',
		5:'NET_SCREEN',
		6:'NET_VERSION',
		7:'NET_LINEUP',
		8:'SRV_START',
		9:'SRV_STOP',
		10:'SRV_RESTART',
		11:'SRV_INPUT',
		12:'CLT_UPDATE',
		13:'CLT_INPUT',
		14:'CLT_LINEUP'
		}
		
	def __init__(self, type, data):	
		self.type = type
		self.data = data
		#self.types = self.stype['type']