import curses
import threading
import Queue
import math
from task import Task
import logging
import time

class Gui:
	def __init__(self, client = None):
		self.stdscr = curses.initscr()
		curses.start_color()
		
		self.queue = Queue.Queue(maxsize=0)
		self.Paint = Paint(self.stdscr, self.queue, self)
		self.client = client
		self.log = logging.getLogger('GUI')
		#self.initscreen()
		
	def initscreen(self):
		self.Paint.start()
		self.Paint.queue.put({'type':'initial'})

		
	def addline(self, line):
		self.queue.put({'type':'log', 'line':line})
		
	def exit(self):
		self.Paint.join()
		curses.endwin()
	
	def resize(self, screensaver):
		#self.Paint.exit = True
		self.Paint.exit = True
		self.Paint = Paint(self.stdscr, self.queue, self, screensaver)
		self.Paint.start()
		self.Paint.queue.put({'type':'initial'})
		
	def outputcommand(self, command):
		if self.client == None:
			self.addline(command)
		else:
			self.addline('[HANDLE] ' + command)
			self.client.addtask(Task(Task.CLT_INPUT, command))
	
	def update(self, items):
		self.log.debug('Update Called')
		for item in items:
			self.log.debug('Got %s for update to %s'%(item[0], item[1]))
			if item[0] == 'screen':
				self.log.debug('caught screen update')
				screendc = []
				for line in item[1]:
					#screendc.append(line.decode('hex_codec'))
					self.Paint.queue.put({'type':'log','line':line.decode('hex_codec')})
			elif item[0] == 'events':
				self.Paint.Status.hdl = item[1]
				self.log.debug('Got Events: %s'% str(item[1]))
			elif item[0] == 'plugins':
				self.Paint.Status.bkt = item[1]
				self.log.debug('Got Plugins for update')
			else:
				self.Paint.Status.sys[item[0]] = item[1]
		self.Paint.queue.put({'type':'status'})
		self.Paint.queue.put({'type':'initial'})
		self.Paint.queue.put({'type':'screen','data':None})

		
class Paint(threading.Thread):
	def __init__(self, stdscr, queue, gui, screensaver = None):
		self.parentgui = gui
		self.stdscr = stdscr
		size = self.stdscr.getmaxyx()	
		self.width = size[1]
		self.height = size[0]
		self.winlog = self.stdscr.subwin(self.height-2,self.width-30,0,0)
		self.winstatus = self.stdscr.subwin(self.height-2,30,0,self.width-30)
		self.wininput = self.stdscr.subwin(self.height-2,0)
		self.wininput.keypad(1)
		self.queue = queue
		self.Log = Log(self.winlog)
		if screensaver:
			self.Log.screen = screensaver
			self.Log.paint()
		self.wininput.nodelay(True)
		self.Input = Input(self.wininput)
		self.Status = Status(self.winstatus)
		self.exit = False

		threading.Thread.__init__(self)
		
	def initialpaint(self):
		self.winlog.erase()
		self.winlog.border()
		self.winstatus.border(' ',0,0,0,curses.ACS_HLINE,0,curses.ACS_HLINE,0)
		self.wininput.border(0,0,' ',0,4194424,4194424,0,0)
		self.winlog.refresh()
		self.winstatus.refresh()
		self.wininput.refresh()
		self.Log.paint()
		self.Input.paint()
		self.Status.draw()

	def run(self):
		
		self.Status.draw()
		while not self.exit:

			try:
				item = self.queue.get(True, 0.1)
			except Queue.Empty:
				pass
			else:
				self.parse(item)
			code = self.wininput.getch()
			if code == 410:
				self.queue.put({'type':'resize'})
			elif code == 10:
				if len(self.Input.command) > 0:
					self.parentgui.outputcommand(self.Input.send())
					self.queue.put({'type':'input'})
					
			elif code == curses.KEY_LEFT:
				if self.Status.page == 'nfo':
					self.Status.page = 'bkt'
				elif self.Status.page == 'bkt':
					self.Status.page = 'hdl'
				elif self.Status.page == 'hdl':
					self.Status.page = 'sys'
				self.queue.put({'type':'status'})
				
			elif code == curses.KEY_RIGHT:
				if self.Status.page == 'sys':
					self.Status.page = 'hdl'
				elif self.Status.page == 'hdl':
					self.Status.page = 'bkt'
				elif self.Status.page == 'bkt':
					self.Status.page = 'nfo'
				self.queue.put({'type':'status'})
				
			elif code == curses.KEY_UP:
				self.Input.scrollup()
			elif code == curses.KEY_DOWN:
				self.Input.scrolldown()
				
			elif not code == -1:
				#self.queue.put({'type':'log', 'line':str(code)})
				x = self.Input.parsechar(code)
				self.queue.put({'type':'input'})
		
	def parse(self, item):
		if item['type'] == 'log':
			self.Log.addline(item['line'])
			self.Log.paint()
		elif item['type'] == 'status':
			self.Status.draw()
		elif item['type'] == 'input':
			self.Input.paint()
		elif item['type'] == 'resize':
			self.stdscr.erase()
			self.parentgui.resize(self.Log.screen)
		elif item['type'] == 'initial':
			self.initialpaint()
		elif item['type'] == 'screen':
			if item['data'] == None:
				self.Log.paint()
			else:
				self.Log.screen = item['data']
				self.Log.paint()
			
	def join(self):
		self.exit = True
		threading.Thread.join(self)
	
		
	
		
class Log:
	def __init__(self, window):
		self.screen = []
		for x in range(0,100):
			self.screen.append(' ')
		self.window = window
		self.height, self.width = self.window.getmaxyx()
		self.wrapper = []

	def addline(self, line):
		#if len(line) > (self.width-2):
		#	sub1 = line[:self.width-2]
		#	sub2 = line[self.width-2:]
		#	lastspace = sub1.rfind(' ')
		#	if not lastspace == -1:
		#		sub1 = line[:lastspace]
		#		sub2 = '     ' + line[lastspace:]
		#		self.screen.append(sub1)
		#		self.screen.pop(0)
		#		self.addline(sub2)
			
		#else:
			self.screen.append(line)
			self.screen.pop(0)

		
	def paint(self):
		self.window.erase()
		self.window.border()
		display = self.screen[100-(self.height-2):]
		y = self.height - 2
		x = len(display)-1
		while x >= 0:
			wrappedline = self.wrapline(display[x])
			for line in wrappedline:
				self.window.addstr(y,1,line)
		
		
			#self.window.addstr(y,1,display[x])
			x = x-1
			y = y-1
		self.window.refresh()
		
	def setsize(self):
		self.height, self.width = self.window.getmaxyx()
		
	def wrapline(self, line):
		wrapped = []
		wrapped.append(line[:self.width-2])
		#if len(line) > (self.width-2):
		#	xline = line
		#	while len(xline) > (self.width-2):
		#		sub1 = xline[:self.width-2]
		#		lastspace = sub1.rfind(' ')
		#		if not lastspace == -1:
		#			wrapped.append(xline[:lastspace])
		#			xline = '     ' + xline[lastspace:]
		#	wrapped.append(xline)
		#else:
		#	wrapped.append(line)
		return wrapped
				
class Input:
	def __init__(self, window):
		self.window = window
		self.command = ''
		self.scrollback = ['','','','','','','','','','','']
		self.sbpos = 11
		self.log = logging.getLogger('PAINT')
	def parsechar(self, code):
		if code >= 32 and code <= 126:
			self.command = self.command + chr(code)
			return code
		elif code == 26:
			curses.endwin()
		elif code == 127:
			self.command = self.command[:-1]
			return code
			
		elif code == 263:
			self.command = self.command[:-1]
		
	def paint(self):	
		self.window.erase()
		self.window.border(0,0,' ',0,4194424,4194424,0,0)
		self.window.addstr(0,1,'> ' + self.command)
		self.window.refresh()
	
	def send(self):
		x = self.command
		if len(self.scrollback) > 10:
			self.scrollback.pop(0)
		self.scrollback.append(x)
		self.log.debug(str(self.scrollback))
		self.sbpos = 11
		self.command = ''
		return x
	
	
	def scrollup(self):
		if self.sbpos > 0 :
			#if self.sbpos == 11:
			#	self.scrollback.append(self.command)
			self.sbpos = self.sbpos - 1
			self.command = self.scrollback[self.sbpos]
			self.log.debug(self.scrollback[self.sbpos])
			self.log.debug('Scrolled up to pos: %s' % str(self.sbpos))
			self.paint()
		
	def scrolldown(self):
		if self.sbpos < 11:
			self.sbpos = self.sbpos + 1
			self.command = self.scrollback[self.sbpos]
			self.log.debug(self.scrollback[self.sbpos])
			self.paint()
			
class Status:
	def __init__(self, window):
		self.window = window
		self.height, self.width = self.window.getmaxyx()
		self.page = 'sys'
		self.sys = {}
		self.sys['bukkitv'] = 0
		self.sys['plimit'] = 1
		self.sys['pcount'] = 0
		self.sys['plugins'] = 0
		self.sys['port'] = 0
		self.sys['serverv'] = 0
		self.sys['maxdsk'] = 1
		self.sys['useddsk'] = 0
		self.sys['maxmem'] = 1
		self.sys['usemem'] = 0
		self.sys['handlev'] = 0
		self.sys['uptime'] = 0
		self.hdl = []
		self.bkt = []
		self.nfo = []
	def draw(self):
		self.window.erase()
		self.topdraw()
		if self.page == 'sys':
			self.draw_sys()
		elif self.page == 'hdl':
			self.draw_hdl()
		elif self.page == 'bkt':
			self.draw_bkt()
		
	def topdraw(self):	
		self.window.hline(2,0,curses.ACS_HLINE,29)
		self.window.addstr(1,4,'SYS')
		self.window.addch(1,8,curses.ACS_VLINE)
		self.window.addstr(1,10,'HDL')
		self.window.addch(1,14,curses.ACS_VLINE)
		self.window.addstr(1,16,'BKT')
		self.window.addch(1,20,curses.ACS_VLINE)
		self.window.addstr(1,22,'NFO')
		if self.page == 'sys':
			self.window.addstr(1,4,'SYS',curses.A_REVERSE)
		elif self.page == 'hdl':
			self.window.addstr(1,10,'HDL',curses.A_REVERSE)
		elif self.page == 'bkt':
			self.window.addstr(1,16,'BKT',curses.A_REVERSE)
		elif self.page == 'nfo':
			self.window.addstr(1,22,'NFO',curses.A_REVERSE)
		self.window.refresh()
		
	def draw_sys(self):
		self.window.addstr(4,3,'Handle Ver:')
		self.window.addstr(4,15,str(self.sys['handlev']))
		self.window.addstr(5,3,'Server Ver:')
		self.window.addstr(5,15,str(self.sys['serverv']))
		self.window.addstr(6,3,'Port:')
		self.window.addstr(6,15,str(self.sys['port']))
		#self.window.addstr(7,3,'Uptime:')
		#self.window.addstr(7,15,str(self.sys['uptime']))
		
		x = 11
		for letter in 'RAM':
			self.window.addstr(x,4,letter)
			x = x+1
		self.draw_graph(11,6,float(self.sys['maxmem']),float(self.sys['usemem']))
		x = 11
		for letter in 'DISK':
			self.window.addstr(x,12,letter)
			x = x+1
		self.draw_graph(11,14,float(self.sys['maxdsk']),float(self.sys['useddsk']))
		x = 11
		for letter in 'PLAYERS':
			self.window.addstr(x,20,letter)
			x = x+1
		self.draw_graph(11,22,float(self.sys['plimit']),float(self.sys['pcount']))
		self.window.refresh()
	
	def draw_hdl(self):
		self.window.addstr(4,7,'Scheduled Tasks', curses.A_UNDERLINE)
		x = 6
		for event in self.hdl:
			self.window.addnstr(x,1,event[0],18)
			time_str = time.strftime('%H:%M:%S',time.localtime(event[1]))
			self.window.addstr(x,19,time_str)
			x = x+1
		self.window.refresh()

	def draw_bkt(self):
		self.window.addstr(4,8,'Bukkit Plugins', curses.A_UNDERLINE)
		x = 6
		for plugin in self.bkt:
			self.window.addstr(x,0,'[ ]')
			if plugin['enabled']:
				self.window.addstr(x,1,'Y')
			self.window.addstr(x,4,plugin['name'])
			self.window.addstr(x,18,plugin['version'])
			x = x+1
		self.window.refresh()
	
	def draw_graph(self, top, left, max, used):
		height = (self.height-3)-top
		percent = used/max
		bottom = int(math.floor(height*percent))
		rbottom = self.height-3
		for x in range(top,rbottom):
			self.window.addch(x,left,curses.ACS_VLINE)
			self.window.addch(x,left+3,curses.ACS_VLINE)
		for x in range(top,top+bottom):
			self.window.addstr(x,left+1,' ',curses.A_REVERSE)
			self.window.addstr(x,left+2,' ',curses.A_REVERSE)
		self.window.addch(rbottom,left,curses.ACS_LLCORNER)
		self.window.addch(rbottom,left+1,curses.ACS_HLINE)
		self.window.addch(rbottom,left+2,curses.ACS_HLINE)
		self.window.addch(rbottom,left+3,curses.ACS_LRCORNER)
		if int(percent*100) < 10:
			self.window.addstr(rbottom+1,left+1,str(0))
			self.window.addstr(rbottom+1,left+2,str(int(percent*100)))
		else:
			self.window.addstr(rbottom+1,left+1,str(int(percent*100)))
		self.window.refresh()
		
		
	
		