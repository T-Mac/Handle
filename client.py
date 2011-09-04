#!/usr/bin/python
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
import comm
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
	
	
	
	

class network(threading.Thread):
	
	def __init__(self):
		self.queue = Queue.Queue(maxsize=0)
		self.net = comm.comm(self.queue,'client')
		self.net.start()
		

		self.net.pack({'id':0x01, 'item':1})
		self.net.pack({'id':0x01, 'item':2})
		

			
		threading.Thread.__init__ ( self )
		
	def run(self):
		while(True):
			packet = self.queue.get()
			self.parse(packet)
			
	
	def parse(self, packet):
		id = packet['id']	
		if id == 0x03:
			#ine = ''
			#for item, obj in packet:
			#	line = item + ':' + obj	+ ', '
			#_conf.gui.handlesay(line)
			if packet['item'] == 1:
				
				_conf.jobup(packet['jobs'])
			elif packet['item'] == 2:
				
				_conf.gui.fullup(packet['screen'])
			#elif packet['item'] == 3:
				#Update Version
			elif packet['item'] == 4:
				
				_conf.gui.handlesay(packet['line'],packet['updatable'])
			
			
				
			
			
		
		

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
	def fullup(self,screen):
		x = 0
		while x <= len(self.screenarray):
			self.screenarray[x-1] = screen[x-1]
			x = x+1
		self.handlesay('Client Reconnected')

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
			#command = raw_input()
			command = _conf.gui.input()
			_conf.comm.net.pack({'id':0x02,'command':command})
			
			
	
			
			
			
def startgui(screen):
	guiid = globals()['gui'](screen)
	_conf.setgui(guiid)
	guiid.start()
	


global _conf
_conf = database()

network1 = network()
_conf.setcomm(network1)

prog = globals()['startgui']
curses.wrapper(prog)
network1.start()
terminal().start()
