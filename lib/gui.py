import curses
import threading
import Queue

class Gui:
	def __init__(self, client = None):
		self.stdscr = curses.initscr()

		self.queue = Queue.Queue(maxsize=0)
		self.Paint = Paint(self.stdscr, self.queue, self)
		self.client = client
		self.initscreen()
		
	def initscreen(self):
		self.Paint.initialpaint()
		self.Paint.start()
		
	def addline(self, line):
		self.queue.put({'type':'log', 'line':line})
		
	def exit(self):
		curses.endwin()
	
	def resize(self, screensaver):
		self.Paint.exit = True
		self.Paint = Paint(self.stdscr, self.queue, self, screensaver)
		self.initscreen()
		
	def outputcommand(self, command):
		if self.client == None:
			self.addline(command)
		else:
			self.addline('[HANDLE] ' + command)
			self.client.addtask({'id':'client.command', 'data':command})
		
		
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
		self.queue = queue
		self.Log = Log(self.winlog)
		if screensaver:
			self.Log.screen = screensaver
		self.wininput.nodelay(True)
		self.Input = Input(self.wininput)
		self.exit = False

		threading.Thread.__init__(self)
		
	def initialpaint(self):
		self.winlog.border()
		self.winstatus.border(' ',0,0,0,curses.ACS_HLINE,0,curses.ACS_HLINE,0)
		self.wininput.border(0,0,' ',0,4194424,4194424,0,0)
		self.winlog.refresh()
		self.winstatus.refresh()
		self.wininput.refresh()

	def run(self):
		while not self.exit:

			try:
				item = self.queue.get_nowait()
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

			elif not code == -1:
				#self.queue.put({'type':'log', 'line':str(code)})
				x = self.Input.parsechar(code)
				self.queue.put({'type':'input'})
		
	def parse(self, item):
		if item['type'] == 'log':
			self.Log.addline(item['line'])
			self.Log.paint()
		elif item['type'] == 'status':
			pass
		elif item['type'] == 'input':
			self.Input.paint()
		elif item['type'] == 'resize':
			self.stdscr.erase()
			self.parentgui.resize(self.Log.screen)
	
		
	
		
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
		if len(line) > (self.width-2):
			xline = line
			while len(xline) > (self.width-2):
				sub1 = xline[:self.width-2]
				lastspace = sub1.rfind(' ')
				if not lastspace == -1:
					wrapped.append(xline[:lastspace])
					xline = '     ' + xline[lastspace:]
			wrapped.append(xline)
		else:
			wrapped.append(line)
		return wrapped
				
class Input():
	def __init__(self, window):
		self.window = window
		self.command = ''
		
	def parsechar(self, code):
		if code >= 32 and code <= 126:
			self.command = self.command + chr(code)
			return code
		elif code == 26:
			curses.endwin()
		elif code == 127:
			self.command = self.command[:-1]
			return code
		
	def paint(self):	
		self.window.erase()
		self.window.border(0,0,' ',0,4194424,4194424,0,0)
		self.window.addstr(0,1,'> ' + self.command)
		self.window.refresh()
	
	def send(self):
		x = self.command
		self.command = ''
		return x


		