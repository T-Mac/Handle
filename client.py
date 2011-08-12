import curses
import curses.wrapper
import threading
import sys
import os
import struct
import time
import pickle
import Queue
import datetime
class database:
	def __init__(self):
		
		self.jobs = {}
		self.gui = None
		self.comm = None
		self.exit = 0
		
	def jobup(self, data):
		self.jobs = data
		
	def setgui(self, id):
		self.gui = id
	
	def setcomm(self,id):
		self.comm = id
	
	
	
	

class comm(threading.Thread):
	
	def __init__(self):
		self.srvoutf = './tmp/serverout'
		self.srvinf = './tmp/serverin'
		self.queue = Queue.Queue(maxsize=0)
		if not os.path.exists(self.srvoutf):
			os.mkfifo(self.srvoutf)
		self.pipeout = os.fdopen(os.open(self.srvinf, os.O_WRONLY),'w')
		self.pack(0x01, {'id':0x01, 'item':1})
		
		
		if not os.path.exists(self.srvinf):
			os.mkfifo(self.srvinf)
		self.pipein = os.fdopen(os.open(self.srvoutf, os.O_RDONLY),'r')
			
		threading.Thread.__init__ ( self )
		
	def run(self):
		while(True):
			packet = pickle.load(self.pipein)
			self.parse(packet)
			
	
	def send(self, data):
		try:
			_conf.gui.handlesay('Sending Packet: ' + str(data['id']))
			pickle.dump(data, self.pipeout)
			self.pipeout.flush()
		except IOError:
			_conf.gui.handlesay('Exception')
			self.queue.put_nowait(data)
	
	def pack(self, packetid, data = None):
		if packetid == 0x00:
			data = {'id':0x00}
		self.queue.put_nowait(data)
			
		
		
	
	def parse(self, packet):
		id = packet['id']
		if id == 0x00:
			self.send(0x00)		
		elif id == 0x03:
			_conf.gui.handlesay(packet['line'],packet['updatable'])
		elif id == 0x04:
			_conf.jobup(packet['jobs'])
		elif id == 0x05:
			_conf.gui.fullup(packet['screen'])
			
			
				
			
			
		
		

class gui(threading.Thread):
	def __init__(self,screen):
		
		self.screen = screen
		self.screen.clear()
		max = self.screen.getmaxyx()
		self.text = self.screen.subwin(max[0]-3,0)
		self.info = self.screen.subwin(max[0]-3,30,0,max[1]-30)
		self.status = self.screen.subwin(max[0]-3,max[1]-30,0,0)
		self.text.box()

		self.info.box()
		self.screen.refresh()
		curses.echo()
		self.clear = '                                                                                                                                                                                                  '
		self.updatable = 0
		self.max = self.status.getmaxyx()
		self.screenarray = []
		for x in range(self.max[0]-1):
			self.screenarray.append('')
		

		
		threading.Thread.__init__ ( self )

	def run(self):
		side = sidebar(self.info,self.screen)
		side.start()
		print 'yes'
		while _conf.exit != 1:
			time.sleep(1)
		curses.endwin()
		
	def screenup(self,line, update = 0):
		
		if update == 2:
			self.updatable = 1
			self.screenarray.append(line)
			del self.screenarray[0]
		elif update == 1:	
			if self.updatable == 1:
				self.screenarray[self.max[0]-2] = self.screenarray[self.max[0]-2] + line
			else:
				self.screenarray.append(line)
				del self.screenarray[0]
			self.updatable = 0
		else:
			self.updatable = 0
			self.screenarray.append(line)
			del self.screenarray[0]
		self.status.erase()
		y = 0
		for x in self.screenarray:
			self.status.addnstr(y,0,self.clear,self.max[1])
			self.status.addnstr(y,0,x,self.max[1])
			y = y + 1
		self.status.refresh()
		
	def input(self):
		self.text.box()
		self.text.addstr(1,1,'>')
		command = self.text.getstr(1,2)
		self.text.erase()
		return command
	
	def handlesay(self,line,update = 0):
		if update == 1 and self.updatable == 1:
			compline = line
		else:
			compline = time.strftime("%H:%M:%S") + ' [HANDLE] ' + line
		self.screenup(compline,update)
	
	def timers(self):
		y = 1
		for id, thread in _conf.jobs.items():
			if thread['nextrun'] != None and thread['runlvl'] != 'system' and thread['state'] != 'canceled':	
				timerem = thread['nextrun']
				timerem = int(timerem - time.time())
				if timerem < 0:
					line = id + ': [WORKING]'
				else:
					timerem = datetime.timedelta(seconds=timerem)
					line = id + ': ' + str(timerem)
				if thread['state'] == 'paused':
					line = id + ': [PAUSED]'

				self.info.addstr(y,1,line)
				y = y+1
		#self.info.addstr(self.info.getmaxyx()[0]-2,2,'Handle version ' + _conf.getconf('Handle','version'))
		self.info.box()
		self.info.refresh()
	def fullup(screen):
		self.screenarray = screen
		self.status.erase()
		y = 0
		for x in self.screenarray:
			self.status.addnstr(y,0,self.clear,self.max[1])
			self.status.addnstr(y,0,x,self.max[1])
			y = y + 1
		self.status.refresh()

class sidebar(threading.Thread):
	def __init__(self,screen,screen2):
		self.screen = screen
		self.screen2 = screen2
		threading.Thread.__init__ ( self )
	def run(self):
		x = 0
		while _conf.exit != 1:
			_conf.gui.timers()
			x = x + 1
			if x == 100:
				_conf.gui.info.erase()
			time.sleep(1)

class terminal(threading.Thread):
	def run(self):
		self.prompt()
	
	
	def prompt(self):
		x = True
		while x:
		
			command = _conf.gui.input()
			_conf.comm.pack(0x02,{'id':0x02,'command':command})
			
			
class sender(threading.Thread):
	def __init__( self):
		self.queue = _conf.comm.queue
		threading.Thread.__init__ ( self )
	def run(self):
		while True:
			
			packet = self.queue.get()
			
			_conf.comm.send(packet)
		
			
	
			
			
			
def startgui(screen):
	guiid = globals()['gui'](screen)
	_conf.setgui(guiid)
	guiid.start()
	


global _conf
_conf = database()

network = comm()
_conf.setcomm(network)

prog = globals()['startgui']
curses.wrapper(prog)
network.start()
sender().start()
terminal().start()
