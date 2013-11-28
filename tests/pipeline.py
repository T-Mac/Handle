import sys
sys.path.append('../lib/')
#sys.path = sys.path.append('..')
#print path
print sys.path
import lib.msg
import logging


LOGLVL = logging.DEBUG

logging.basicConfig(level=LOGLVL, format='%(asctime)s %(name)s %(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
module_logger = logging.getLogger(__name__)

class TestFilter(lib.msg.pipeline.Filter):
	def Execute(self, msg):
		module_logger.debug('Executing TestFilter: %s'%str(msg))
		return msg+1
		
class TestService(object):
	def __init__(self):
		self.pipeline = lib.msg.pipeline.Pipeline()
		self.pipeline.Register(TestFilter())
		self.pipeline.Register(TestFilter())
	
	def Invoke(self, msg):
		self.pipeline.Execute(msg)
		
		
TS = TestService()
msg = 0
TS.Invoke(msg)
