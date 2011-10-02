import pickle
import os
import threading
import time

class comm:

	def __init__(self):
		self.srvinf = './tmp/serverout'
		self.srvoutf = './tmp/serverin'

		if not os.path.exists(self.srvinf):
			os.mkfifo(self.srvinf)
		if not os.path.exists(self.srvinf):
			os.mkfifo(self.srvoutf)
		
		
	def run(self):
		x = 1
		data = {}
		self.pipeout = os.fdopen(os.open(self.srvinf, os.O_WRONLY),'w')
		while True:
			
			
			print 'Sent'
			data['id'] = x
			try:
				pickle.dump(data, self.pipeout)
				self.pipeout.flush()
			except IOError:
				pass
			time.sleep(5)
			x = x + 1
test = comm()
test.run()