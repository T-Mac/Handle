import curses
import threading
import Queue
import math
from task import Task
import logging
import time
import re
import string
class Gui:
	def __init__(self, client = None):
		self.stdscr = curses.initscr()
		curses.start_color()
		curses.curs_set(0)
		self.queue = Queue.Queue(maxsize=0)
		self.Paint = Paint(self.stdscr, self.queue, self)
		self.client = client
		self.log = logging.getLogger('GUI')
		curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)
		curses.init_pair(7, curses.COLOR_WHITE, curses.COLOR_BLACK)
		curses.init_pair(9, curses.COLOR_WHITE, curses.COLOR_BLACK)
		curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
		curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
		curses.init_pair(5, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
		curses.init_pair(6, curses.COLOR_CYAN, curses.COLOR_BLACK)
		curses.init_pair(10, curses.COLOR_WHITE, curses.COLOR_GREEN)
		curses.init_pair(11, curses.COLOR_BLACK, curses.COLOR_YELLOW)
		curses.init_pair(12, curses.COLOR_BLACK, curses.COLOR_RED)

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
			elif item[0] == 'players':
				if item[1]['action'] == 'disconnected':
					for player in self.Paint.Status.nfo:
						if player['name'] == item[1]['name'] and item[1]['action'] == 'disconnected':
							self.Paint.Status.nfo.remove(player)
				elif item[1]['action'] == 'connected':
					self.Paint.Status.nfo.append(item[1])
						
	
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
		self.log = logging.getLogger('LOG')
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
			line = self.remove_escapes(line)
			self.log.debug('Line after replacement: %s'%line)
			self.screen.append(line)
			self.screen.pop(0)

	def remove_escapes(self, line):
		escapes = ['[33;22m','[37;1m','[0m','[32m','[31m','[35m','[m','[33;1m','[37;22m','[31;1m','[32;1m']
		replacements = ['[YEL]','[WHI]','[OFF]','[GRE]','[RED]','[MAG]','','[YEL]','[WHI]','[RED]','[GRE]']
		w = string.printable[:-5]
		line = "".join(c for c in line if c in w)	
		x = 0
		while x < len(escapes):
			line = line.replace(escapes[x],replacements[x])
			x = x+1
		return line
		
	def paint(self):
		self.window.erase()
		self.window.border()
		display = self.screen[100-(self.height-2):]
		y = self.height - 2
		x = len(display)-1
		while x >= 0:
			wrappedline = self.wrapline(display[x])
			for line in wrappedline:
		

				#self.window.addstr(y,1,line)
				
				self.color_print(self.colorize(line),y)
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
		
	def color_print(self, line, y):
		cur_attr = 0
		colors = {'[YEL]':3,'[WHI]':7,'[OFF]':9,'[GRE]':2,'[RED]':1,'[MAG]':5, '[CYN]':6}
		pos = 0 
		startpos = 0
		hpos = 1
		remaining = line
		while pos < len(line):
			if line[pos] == '[':
				#print line[pos:pos+5]
				if line[pos:pos+5] in colors:
					#print 'Attr:%s %s' % (cur_attr, line[startpos:pos])
					self.window.addstr(y,hpos,line[startpos:pos],curses.color_pair(cur_attr))
					hpos = hpos + len(line[startpos:pos])
					cur_attr = colors[line[pos:pos+5]]
					remaining = line[pos+5:]
					startpos = pos+5

			pos = pos+1
		self.window.addstr(y,hpos,remaining,curses.color_pair(cur_attr))
	#print 'Attr:%s %s' % (cur_attr,remaining) 
	def colorize(self, line):
		
		elements = {'[WARNING]':'[RED]','For help, type "help" or "?"':'[YEL]','enabled':'[GRE]','[HANDLE]':'[CYN]','Connected to Handle ver.':'[GRE]','Loading':'[YEL]'}
		for item in elements:
			pos = line.find(item)
			if pos != -1:
				line = line[:pos] + elements[item] + line[pos:pos+len(item)] + '[WHI]' + line[pos+len(item):]
		
		return line
		
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
			self.command = self.scrollback[self.sbpos-1]
			self.log.debug(self.scrollback[self.sbpos-1])
			self.log.debug('Scrolled up to pos: %s' % str(self.sbpos-1))
			self.paint()
		
	def scrolldown(self):
		if self.sbpos < 11:
			self.sbpos = self.sbpos + 1
			self.command = self.scrollback[self.sbpos-1]
			self.log.debug(self.scrollback[self.sbpos-1])
			self.paint()
			
class Status:
	def __init__(self, window):
		self.log = logging.getLogger('STATUS')
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
		elif self.page == 'nfo':
			self.draw_nfo()
		
	def topdraw(self):	
		self.window.hline(2,0,curses.ACS_HLINE,29)
		self.window.addstr(1,4,'SYS',curses.color_pair(6))
		self.window.addch(1,8,curses.ACS_VLINE,)
		self.window.addstr(1,10,'HDL',curses.color_pair(6))
		self.window.addch(1,14,curses.ACS_VLINE)
		self.window.addstr(1,16,'BKT',curses.color_pair(6))
		self.window.addch(1,20,curses.ACS_VLINE)
		self.window.addstr(1,22,'NFO',curses.color_pair(6))
		self.window.border(' ',0,0,0,curses.ACS_HLINE,0,curses.ACS_HLINE,0)
		if self.page == 'sys':
			self.window.addstr(1,4,'SYS',curses.A_REVERSE,)
		elif self.page == 'hdl':
			self.window.addstr(1,10,'HDL',curses.A_REVERSE)
		elif self.page == 'bkt':
			self.window.addstr(1,16,'BKT',curses.A_REVERSE)
		elif self.page == 'nfo':
			self.window.addstr(1,22,'NFO',curses.A_REVERSE)
		self.window.refresh()
		
	def draw_sys(self):
		self.window.addstr(4,3,'Handle Ver:',curses.color_pair(6))
		self.window.addstr(4,15,str(self.sys['handlev']),curses.color_pair(2))
		self.window.addstr(5,3,'Server Ver:',curses.color_pair(6))
		self.window.addstr(5,15,str(self.sys['serverv']),curses.color_pair(2))
		self.window.addstr(6,3,'Port:',curses.color_pair(6))
		self.window.addstr(6,15,str(self.sys['port']),curses.color_pair(2))
		#self.window.addstr(7,3,'Uptime:')
		#self.window.addstr(7,15,str(self.sys['uptime']))
		
		x = 11
		for letter in 'RAM':
			self.window.addstr(x,4,letter,curses.color_pair(6))
			x = x+1
		self.draw_graph(11,6,float(self.sys['maxmem']),float(self.sys['usemem']))
		x = 11
		for letter in 'DISK':
			self.window.addstr(x,12,letter,curses.color_pair(6))
			x = x+1
		self.draw_graph(11,14,float(self.sys['maxdsk']),float(self.sys['useddsk']))
		x = 11
		for letter in 'PLAYERS':
			self.window.addstr(x,20,letter,curses.color_pair(6))
			x = x+1
		self.draw_graph(11,22,float(self.sys['plimit']),float(len(self.nfo)))
		self.window.refresh()
	
	def draw_hdl(self):
		self.window.addstr(4,7,'Scheduled Tasks', curses.A_UNDERLINE)
		x = 6
		for event in self.hdl:
			self.window.addnstr(x,1,event[0],18)
			time_str = time.strftime('%H:%M:%S',time.localtime(event[1]))
			self.window.addstr(x,19,time_str,curses.color_pair(6))
			x = x+1
		self.window.refresh()

	def draw_bkt(self):
		self.window.addstr(4,8,'Bukkit Plugins', curses.A_UNDERLINE)
		x = 6
		for plugin in self.bkt:
			self.window.addstr(x,0,'[ ]')
			if plugin['enabled']:
				self.window.addstr(x,1,'Y',curses.color_pair(2))
			else:
				self.window.addstr(x,1,'N',curses.color_pair(1))
			self.window.addnstr(x,4,plugin['name'],13)
			self.window.addnstr(x,18,plugin['version'],11,curses.color_pair(6))
			x = x+1
		self.window.refresh()
	
	def draw_nfo(self):
		self.window.addstr(4,11,'Players', curses.A_UNDERLINE)
		x = 6
		for player in self.nfo:
			self.window.addstr(x,1,player['name'])
			time_str = time.strftime('%H:%M:%S',time.localtime(int(player['time'])))
			self.window.addstr(x,19,time_str)
			x = x+1
		self.window.refresh()
	def draw_graph(self, top, left, max, used):
		height = (self.height-3)-top
		percent = used/max
		fill = int(math.floor(height*percent))
		blank_lines = (height-fill) + top
		rbottom = self.height-3
		drawn = 0
		total = len(range(top,rbottom))
		for x in range(top,rbottom):
			yellow = (len(range(top,rbottom))/2) - 1
			red = len(range(top,rbottom)) - (len(range(top,rbottom))/4)-1
			if total-drawn == yellow or total-drawn == red-1:
				self.window.addch(x,left,curses.ACS_SBSS)
			else:
				self.window.addch(x,left,curses.ACS_VLINE)
			self.window.addch(x,left+3,curses.ACS_VLINE)
			line_color = 10
			cur_char = ' '
			
			if total - drawn > yellow:
				line_color = 11
			if total - drawn > red:
				line_color = 12
			#self.log.info('y = %s r = %s' % (str(yellow), str(red)))
			if x < yellow:
				line_color = 11
			if x < red:
					line_color = 12
			if x > blank_lines:
				self.window.addstr(x,left+1,cur_char,curses.color_pair(line_color))
				self.window.addstr(x,left+2,' ',curses.color_pair(line_color))
			drawn = drawn+1
		self.window.addch(rbottom,left,curses.ACS_LLCORNER)
		self.window.addch(rbottom,left+1,curses.ACS_HLINE)
		self.window.addch(rbottom,left+2,curses.ACS_HLINE)
		self.window.addch(rbottom,left+3,curses.ACS_LRCORNER)
		num_color = 2
		if int(percent*100) > 50:
			num_color = 3
		if int(percent*100) > 75:
			num_color = 1
		if int(percent*100) < 10:
			self.window.addstr(rbottom+1,left+1,str(0),curses.color_pair(2))
			self.window.addstr(rbottom+1,left+2,str(int(percent*100)),curses.color_pair(2))
		else:
			self.window.addstr(rbottom+1,left+1,str(int(percent*100)),curses.color_pair(num_color))
		self.window.refresh()
		
		
	
		