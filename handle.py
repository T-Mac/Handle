from feedparser import parse
import ConfigParser
import threading
import time
import sys
import os
import Queue
import curses
import curses.wrapper
import subprocess
import shlex
import datetime
from optparse import OptionParser

class runfunc(threading.Thread):
	def __init__( self, func, lockobj):
		self.func = func
		self.lockobj = lockobj
		threading.Thread.__init__ ( self )
	def run(self):
		result = globals()[self.func](self.lockobj)
		
		
#--------------------------Class to handle all config files and globaly needed objects----------------------------	--------
class database:
	def __init__(self):
		config = {}
		configfile = ConfigParser.RawConfigParser()
		configfile.read('handle.cfg')
		sections = configfile.sections()
		for section in sections:
			options = configfile.options(section)
			internal = {}
			for option in options:
				internal[option] = configfile.get(section,option)
			config[section] = internal
		self.config = config
		self.threads = {}

		self.queue = {}
		self.uid = 0
		self.locks = {}
		self.exit = None
		self.objects = {}
		self.allclear = threading.Event()
		self.stdin = None
		self.stdout = None
		self.gui = None
		self.serverstatus = None	
		
		
	def initserver(self):
		self.makeque('server')
		self.makeque('scheduler')
		self.makelock('server')
		self.makelock('chat')
		self.makelock('cwc')
	
	def checkid(self,dict,id):
		if dict.get(id, None) != None:
			raise KeyError('Id: ' + str(id) + ' already exists')
			
	def getconf(self,section = None,option = None):
		if option == None:
			if section == None:
				return self.config
			else:
				return self.config[section]
		else:	
			return self.config[section][option]
			
	def prune(self):
		for id, thread in self.threads.items():
			if thread.state == 'reviewed':
				del self.threads[id]
			
	def cancel(self):
		self.exit = 1
		
	def threadadd(self, objname, runlvl, id = None):
	
		if id == None and self.threads.get(objname, None) != None:
			id = objname + '-' + str(self.uid)
			self.uid += 1	
		elif id == None and self.threads.get(objname, None) == None:
			id = objname
		elif id != None and self.threads.get(objname, None) != None:
			id = id + '-' + str(self.uid)
			self.uid += 1
			
		self.threads[id] = thread(objname,runlvl,id)
		
		return id

	
	def getthread(self, query = None):
		if query == None:
			return self.threads
		for k, v in self.threads.items():
			if k == query:
				return v.obj
			elif v.obj == query:
				return k
		raise KeyError('Query: ' + str(query) + ' not found!')
		
	def makeque(self, id = None):
		if id == None:
			id = self.uid
			self.uid += 1
		else:
			if self.queue.get(id, None) != None:
				raise KeyError('Id: ' + str(id) + ' already exists')
		self.queue[id] = Queue.Queue(maxsize=0)
		return self.queue[id]

	def getqueue(self, query = None):
		if query == None:
			return self.queue
		for k, v in self.queue.items():
			if k == query:
				return v
			elif v == query:
				return k	
	
	def makelock(self, id=None):
		if id == None:
			id = self.uid
			self.uid +=1
		else:
			self.checkid(self.locks,id)
		self.locks[id] =threading.Lock()
	
	def getlock(self, query = None):
		if query == None:
			return self.locks
		for k, v in self.locks.items():
			if k == query:
				return v
			elif v == query:
				return k

	
	def addobj(self, id, obj):
		self.objects[id] = obj
	
	def setstd(self, stdin, stdout):
		self.stdin = stdin
		self.stdout = stdout
	
	def setgui(self, gui):
		self.gui = gui
		
	def setsrvstat(self, status):
		if status == 'running' or status == 'stopped':
			self.serverstatus = status
			
	

#---------------------------------------------------------------------------

class thread:
	def __init__(self, objname, runlvl, id):
		
		self.properties = {'basename':objname, 'runlvl':runlvl, 'id':id, 'state':'ready', 'nextrun':None}
		self.properties['obj'] = _conf.objects[objname]()
		self.updateself()
		self.arg = None
	def start(self):
		self.properties['obj'].start()


	
	def setattr(self,attr,value):
		self.properties[attr] = value
		self.updateself()
		
	def updateself(self):
		self.id = self.properties['id']
		self.obj = self.properties['obj']
		self.state = self.properties['state']
		self.runlvl = self.properties['runlvl']
		self.nextrun = self.properties['nextrun']
		self.basename = self.properties['basename']
		
	def args(self,arg):
		self.properties['obj'] = _conf.objects[self.basename](int(arg))
		self.updateself()
		
		
class update(threading.Thread):
	def __init__( self, version):
		self.version = version
		threading.Thread.__init__ ( self )
	def run(self):
		version = self.version
		lock = _conf.getlock('server')
		_conf.gui.handlesay('Waiting for Lock....',2)
		lock.acquire()
		_conf.gui.handlesay('Lock acquired!',1)		
		_conf.gui.handlesay('Updating....',2)
		url = 'http://ci.bukkit.org/job/dev-CraftBukkit/' + str(version) + '/artifact/target/craftbukkit-0.0.1-SNAPSHOT.jar'
		urllib.urlretrieve(url,'craftbukkit.jar')
		if config['bukkit'][-15:] == 'craftbukkit.jar':
			path = config['bukkit']
		else:
			if config['bukkit'][-1:] != '/':
				path = config['bukkit'] + '/craftbukkit.jar'
			else:
				path = config['bukkit'] + 'craftbukkit.jar'
		shutil.move('craftbukkit.jar', path)
		configfile = ConfigParser.RawConfigParser()
		configfile.read('bukkitup.cfg')
		configfile.set('Config','currentbuild',config['curbuild'])
		configfile2 = open('bukkitup.cfg', 'wb')
		configfile.write(configfile2)
		configfile2.close()
		lock.release()
		_conf.gui.handlesay('Updated!',1)

class servercontrol(threading.Thread):
	def __init__( self):
		self.oper = _conf.getqueue('server')
		self.lockobj = _conf.getlock('server')
		self.config = _conf.getconf('Handle')
		threading.Thread.__init__ ( self )
	def run(self):
		global serveraction
		if self.config['path_to_bukkit'][-1:] != '/':
			path = self.config['path_to_bukkit'] + '/craftbukkit.jar'
		else:
			path = self.config['path_to_bukkit'] + 'craftbukkit.jar'
		startcmd = 'java -Xmx' + str(self.config['start_heap']) + 'M -Xms' + str(self.config['max_heap'])  + 'M -jar ' + str(path)
		startcmd = shlex.split(startcmd)
		self.lockobj.acquire()
		while True:
			oper = self.oper.get()		
			if oper == 'start':
				_conf.gui.handlesay('Starting Server....',2)
				os.chdir(self.config['path_to_bukkit'])
				p = subprocess.Popen(startcmd, shell=False, stdin = subprocess.PIPE, stdout = subprocess.PIPE, stderr = subprocess.STDOUT)
				os.chdir(self.config['original_path'])
				_conf.setstd(p.stdin, p.stdout)
				_conf.setsrvstat('running')
				_conf.gui.handlesay('Started!',1)
			elif oper == 'stop':
				#chatttimer('Server', 60)
				try:
						p.stdin.write('stop\n')
				except IOError:
					pass
				q = 1
				p.communicate(None)
				
				#while q == 1:
					#try:
					#	p.stdin.write('')
					#except IOError:
				_conf.setsrvstat('stopped')
					#	q = 2
			elif oper =='restart':
				if _conf.serverstatus == 'running':
				#chattimer('Server Restart', 300)
					_conf.gui.handlesay('Stopping Server....',2)
					try:
							p.stdin.write('stop\n')
					except IOError:
						pass
					p.communicate(' ')
					_conf.setsrvstat('stopped')
					_conf.gui.handlesay('Server Stopped!.......Waiting 30 secs',1)
					time.sleep(15)
					_conf.gui.handlesay('Server starting in 15 secs')
					time.sleep(10)
					_conf.gui.handlesay('Server starting in 5 secs')
					time.sleep(5)
					_conf.gui.handlesay('Starting Server....',2)
					os.chdir(self.config['path_to_bukkit'])
					p = subprocess.Popen(startcmd, shell=False, stdin = subprocess.PIPE, stdout = subprocess.PIPE, stderr = subprocess.STDOUT)
					os.chdir(self.config['original_path'])
					_conf.setstd(p.stdin, p.stdout)
					_conf.setsrvstat('running')
					_conf.gui.handlesay('Server Started!',1)
				else:
					_conf.gui.handlesay("[ERROR] The server isn't running")
			elif oper == 'release':
				self.lockobj.release()
				_conf.gui.handlesay('Server lock released!')
				time.sleep(1)
			elif oper == 'kill':
				if _conf.serverstatus == 'running':
					p.stdin.write('stop\n')
					self.lockobj.release()
				return
			
class chattimer(threading.Thread):
	def __init__( self, config):
		self.config = config
		self.config['screenbukkit'] = _conf.getconf('Handle','screen_bukkit')
		self.config['chatlock'] = _conf.getlock('chat')
		self.id = self.config['id']
		threading.Thread.__init__ ( self )
	def run(self):
		x = self.config['interval'] * 60
		nextrun = time.time() + x
		_conf.threads[self.id].setattr('nextrun',nextrun)
		_conf.gui.handlesay(self.config['message'] + ' at ' + time.strftime('%H:%M',time.localtime(nextrun)))
		while x > 360:
			if self.statecheck() == 1:
				return None
			elif self.statecheck() == 2:
				x = x + 10
				nextrun = nextrun + 10
				_conf.threads[self.id].setattr('nextrun',nextrun)
			x = x - 10
			time.sleep(10)

		threshhold = x
		while x > 25:
			if self.statecheck() == 1:
				return None
			elif self.statecheck() == 2:
				x = x + 10
				nextrun = nextrun + 10
				_conf.threads[self.id].setattr('nextrun',nextrun)
				
			if x > 60 and x <= threshhold:
				self.config['chatlock'].acquire()
				_conf.gui.handlesay(self.config['message'] + ' in ' + str(x/60) + ' minutes')
				serversay(self.config['message'] + ' in ' + str(x/60) + ' minutes')
				self.config['chatlock'].release()
				threshhold = threshhold/2
				
			if x <= 60 and x <= threshhold:
				self.config['chatlock'].acquire()
				_conf.gui.handlesay(self.config['message'] + ' in ' + str(x) + ' secs')
				serversay(self.config['message'] + ' in ' + str(x) + ' secs')
				self.config['chatlock'].release()
				threshhold = threshhold/2
				
			x = x - 10
			if x < 25:
				x = x + 10
				time.sleep(x-15)
				x = 0
			else:
				time.sleep(10)
		self.config['chatlock'].acquire()
		_conf.gui.handlesay(self.config['message'] + ' in 15 secs')
		serversay(self.config['message'] + ' in 15 secs')
		self.config['chatlock'].release()
		if self.statecheck() == 1:
			return None
		time.sleep(5)
		self.config['chatlock'].acquire()
		_conf.gui.handlesay(self.config['message'] + ' in 10 secs')
		serversay(self.config['message'] + ' in 10 secs')
		self.config['chatlock'].release()
		if self.statecheck() == 1:
			return None
		time.sleep(5)
		y = 5
		while y > 0:
			if self.statecheck() == 1:
				return None
			self.config['chatlock'].acquire()
			_conf.gui.handlesay(self.config['message'] + ' in ' + str(y) + ' secs')
			serversay(self.config['message'] + ' in ' + str(y) + ' secs')
			self.config['chatlock'].release()
			time.sleep(1)
			y = y-1
		self.config['signal'].set()
		
	def cancel(self):
		if _conf.threads[self.id].state == 'canceled':
			_conf.gui.handlesay(self.config['message'] + ' timer canceling')
			serversay(self.config['message'] + ' canceling')
			self.config['signal'].set()
			return True
			
			
	def statecheck(self):
		if _conf.threads[self.id].state == 'canceled':
			self.config['signal'].set()
			return 1
		elif _conf.threads[self.id].state == 'paused':
			return 2
		else:
			return 0

			
class mapper(threading.Thread):
	def __init__( self, interval = None):
		self.interval = interval
		threading.Thread.__init__ ( self )
	def run(self):
		#Load config
		self.setid()
		config = {}
		_conf.threads[self.id].setattr('state','running')
		if self.interval == None:
			config['interval'] = int(_conf.getconf('Mapper','interval'))
		else:
			config['interval'] = self.interval
		config['message'] = 'Server map'
		config['signal'] = threading.Event()
		config['id'] = self.id
		#Create timer thread
		timer = chattimer(config)
		#start it
		timer.start()
		#wait for signal
		config['signal'].wait()
		if _conf.threads[self.id].state == 'canceled':
			_conf.threads[self.id].setattr('state','stopped')
			_conf.gui.handlesay('Mapper Canceled!',1)
			return ''
		updatewd()
		_conf.getlock('cwc').acquire()
		_conf.gui.handlesay('Mapping......',2)
		time.sleep(30)
		_conf.gui.handlesay('Done!',1)
		time.sleep(10)
		_conf.getlock('cwc').release()
		_conf.threads[self.id].setattr('state','stopped')
	def setid(self):
		self.id = _conf.getthread(self)
		
class backup(threading.Thread):
	def __init__( self, interval = None):
		self.interval = interval
		threading.Thread.__init__ ( self )
	def run(self):
		#Load config
		self.setid()
		_conf.threads[self.id].setattr('state','running')
		config = {}
		if self.interval == None:
			config['interval'] = int(_conf.getconf('Backup','interval'))
		else:
			config['interval'] = self.interval
		config['signal'] = threading.Event()
		config['id'] = self.id
		config['message'] = 'Backup'
		config['path'] = _conf.getconf('Handle','path_to_bukkit')
		if config['path'][-1:] == '/':
			config['path'] = config['path'][:-1]
		config['worlds'] = _conf.getconf('Handle','worlds')
		config['worlds'] = config['worlds'].split()
		config['handlepath'] = _conf.getconf('Handle','original_path')
		timer = chattimer(config)
		timer.start()
		config['signal'].wait()
		if _conf.threads[self.id].state == 'canceled':
			_conf.threads[self.id].setattr('state','stopped')
			_conf.gui.handlesay('Backup Canceled',1)
			return ''
		updatewd()
		_conf.getlock('cwc').acquire()
		_conf.gui.handlesay('Backing up......',2)
		if not os.path.exists(config['handlepath'] + '/backups'):
			os.mkdir(config['handlepath'] + '/backups')
 
		if not os.path.exists(config['handlepath'] + '/wd/'):
			os.mkdir(config['handlepath'] + '/wd')
		os.chdir(config['handlepath'] + '/wd/')
		for world in config['worlds']:
			if not os.path.exists(config['handlepath'] + '/backups/' + world):
				os.mkdir(config['handlepath'] + '/backups/' + world)
			os.system('tar -cf ' + config['handlepath'] + '/backups/' + world + '/' + str(time.strftime('%b-%d-%H%M')) + '.tar.gz ' + world)
			
		_conf.gui.handlesay('Done!',1)
		_conf.getlock('cwc').release()
		_conf.threads[self.id].setattr('state','stopped')
		
	def setid(self):
		self.id = _conf.getthread(self)
		
class restarter(threading.Thread):
	def __init__( self, interval = None):
		self.interval = interval
		threading.Thread.__init__ ( self )
	def run(self):
		self.setid()
		_conf.threads[self.id].setattr('state','running')
		config = {}
		configfile = ConfigParser.RawConfigParser()
		configfile.read('handle.cfg')
		if self.interval == None:
			config['interval'] = int(_conf.getconf('Restart','interval'))
		else:
			config['interval'] = self.interval
		config['signal'] = threading.Event()
		config['id'] = self.id
		config['message'] = 'Server restart'
		config['screenbukkit'] = _conf.getconf('Handle','screen_bukkit')
		timer = chattimer(config)
		timer.start()
		config['signal'].wait()
		if _conf.threads[self.id].state == 'canceled':
			_conf.threads[self.id].setattr('state','stopped')
			_conf.gui.handlesay('Restart Canceled',1)
			return ''
		_conf.getqueue('server').put('restart')
		time.sleep(60)
		_conf.threads[self.id].setattr('state','stopped')
	def setid(self):
		self.id = _conf.getthread(self)
		
		
		
class scheduler(threading.Thread):
	def __init__( self):
		threading.Thread.__init__ ( self )
	def run(self):
		self.defaultthreads()
		os.chdir(_conf.getconf('Handle','original_path'))
		while _conf.exit == None:
			x = 0
			for id, thread in _conf.threads.items():
				if _conf.threads[id].state == 'stopped':
					_conf.threads[id].setattr('state','reviewed')
					if _conf.threads[id].runlvl == 'system' or _conf.threads[id].runlvl == 'normal':
						basename = _conf.threads[id].basename
						runlvl = _conf.threads[id].runlvl
						if len(id) > 5:
							if id[:5] == 'auto_':
								_conf.prune()
								name = _conf.threadadd(basename,runlvl,id)
							else:
								pass
						else:
							_conf.prune()
							name = _conf.threadadd(basename,runlvl)
						_conf.threads[name].start()
					else:
						_conf.prune()
					
		_conf.gui.handlesay('Killing Threads.....')
		_conf.getqueue('server').put('kill')
		x = 0
		for id, o in _conf.threads.items():
			_conf.threads[id].setattr('state', 'canceled')
			x += 1
		y = 0
		while x > 0:
			dict = _conf.threads
			for id, o in dict.items():
				if _conf.threads[id].state == 'stopped':
					_conf.threads[id].setattr('state','reviewed')
					_conf.gui.handlesay('Killed: ' + id)
					_conf.prune()
					x = x - 1
				
	
		_conf.getlock('server').acquire()
		_conf.allclear.set()
	def defaultthreads(self):
		_conf.addobj('mapper', globals()['mapper'])
		_conf.addobj('backup', globals()['backup'])
		_conf.addobj('restart', globals()['restarter'])
	
		_conf.threadadd('mapper','normal','auto_mapper')
		_conf.threadadd('backup','normal','auto_backup')
		_conf.threadadd('restart','normal','auto_restart')
	
		for id, thread in _conf.threads.items():
			thread.start()			

class terminal(threading.Thread):
	def run(self):
		self.prompt()
	
	
	def prompt(self):
		x = True
		while x:
		
			x = self.interpret(_conf.gui.input())
			
	def interpret(self,command):
		if command == 'exit':
			_conf.cancel()
			_conf.allclear.wait()
			return False
		elif command == 'start':
			if _conf.serverstatus == 'running':
				_conf.gui.handlesay('The server is already running!')
			else:
				_conf.getqueue('server').put('start')
		elif command == 'restart':
			_conf.getqueue('server').put('restart')
		elif command[:5] == 'sched':
			command = command.split()
			x = 0
			if len(command) > 1:
				for item, obj in _conf.objects.items():
					if item == command[1]:
						x = 1
			if len(command) == 3:
				if x == 1:
					id = _conf.threadadd(command[1],'user')
					_conf.threads[id].args(command[2])
					_conf.gui.handlesay('Scheduled: ' + id)
					_conf.threads[id].start()
				else:
					_conf.gui.handlesay('No such job: ' + command[1])
					_conf.gui.handlesay('Avaliable jobs:')
					line = '[ '
					for item, obj  in _conf.objects.items():
						line = line + item + ', '
					line = line + ' ]'
					_conf.gui.handlesay(line)
			elif len(command) == 2:
				if x == 1:
					
					id = _conf.threadadd(command[1],'user')
					_conf.gui.handlesay('Scheduled: ' + id)
					_conf.threads[id].start()
				else:
					_conf.gui.handlesay('No such job: ' + command[1])
					line = '[ '
					for item, obj  in _conf.objects.items():
						line = line + item + ', '
					line = line + ' ]'
					_conf.gui.handlesay(line)
					_conf.gui.handlesay('Avaliable jobs:')
			else:
				line = '[ '
				for item, obj  in _conf.objects.items():
					line = line + item + ', '
				line = line + ' ]'
				_conf.gui.handlesay(line)
			
		elif command == 'srvstat':
			_conf.gui.handlesay(_conf.serverstatus)
		elif command == 'stop':
			_conf.getqueue('server').put('stop')
		elif command == 'help':
			_conf.gui.handlesay('----------------------Help-------------------------')
			_conf.gui.handlesay('<> optional            [] required')
			_conf.gui.handlesay('start:                 start server')
			_conf.gui.handlesay('stop <secs>:           stop server in <secs>')
			_conf.gui.handlesay('restart:               resart server')
			_conf.gui.handlesay('exit:                  stop server and close Handle')
			_conf.gui.handlesay('sched <job> <mins>:    w/o args list running jobs, w/ start <job> with <mins> delay.')
			_conf.gui.handlesay('cancel <job>:          cancel any user started jobs')
			_conf.gui.handlesay('pause <job>:           pause any job')
			_conf.gui.handlesay('unpause:               unpause jobs')
			_conf.gui.handlesay('jobs:                  list avaliable jobs')
			_conf.gui.handlesay('help:                  print this help')
			
			if _conf.serverstatus == 'running':
				try:
					_conf.stdin.write(command + '\n')
				except IOError:
					pass
		elif command[:6] == 'cancel':
			try:
				_conf.getthread(command[7:])
			except KeyError:
				_conf.gui.handlesay('[ERROR] ' + command[7:] + ": Job doesn't exist")
				line = ' ['
				for item, obj  in _conf.objects.items():
					line = line + item + ', '
				line = line + ' ]'
				_conf.gui.handlesay(line,1)
			else:	
				_conf.gui.handlesay(command[7:] + ' Canceling....',2)
				_conf.threads[command[7:]].setattr('state','canceled')
				_conf.gui.info.erase()
		
		elif command[:5] == 'pause':
			try:
				_conf.getthread(command[6:])
			except KeyError:
				_conf.gui.handlesay('[ERROR] ' + command[6:] + ": Job doesn't exist")
			else:
				_conf.threads[command[6:]].setattr('state','paused')
				_conf.gui.handlesay(command[6:] + ' Paused')
				
		elif command[:7] == 'unpause':
			try:
				_conf.getthread(command[8:])
			except KeyError:
				_conf.gui.handlesay('[ERROR] ', + command[8:] + ": Job doesn't exist")
			else:
				_conf.threads[command[8:]].setattr('state','running')
				_conf.gui.handlesay(command[8:] + ' Unpaused')
		
		elif command == 'jobs':
			line = ' Avaliable Jobs: ['
			for item, obj  in _conf.objects.items():
				line = line + item + ', '
			line = line + ' ]'
			_conf.gui.handlesay(line,1)
			
		else:
			if _conf.serverstatus == 'running':
				try:
					_conf.stdin.write(command + '\n')
				except (IOError, ValueError):
					pass
		
			else:
				_conf.gui.handlesay('Unknown Command')
		return True
		
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
		
		while _conf.exit != 1:
			
			if _conf.serverstatus == 'running':
				try:
					line = _conf.stdout.readline()
				except (AttributeError,ValueError, IOError):
					line = ''
				self.screenup(line.strip())
		_conf.allclear.wait()
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
		for id, thread in _conf.threads.items():
			if thread.nextrun != None and thread.runlvl != 'system' and thread.state != 'canceled':	
				timerem = thread.nextrun
				timerem = int(timerem - time.time())
				if timerem < 0:
					timerem = 0
				
				timerem = datetime.timedelta(seconds=timerem)
				line = id + ': ' + str(timerem)
				if thread.state == 'paused':
					line = id + ': [PAUSED]'
				self.info.addstr(y,1,line)
				y = y+1
		self.info.addstr(self.info.getmaxyx()[0]-2,2,'Handle version ' + _conf.getconf('Handle','version'))
		self.info.box()
		self.info.refresh()


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
		
def getversion():
	#Read from CraftBukkit Build RSS
	bukkit = feedparser.parse('http://ci.bukkit.org/job/dev-CraftBukkit/rssAll')
	# Extract current version
	version = bukkit.entries[0].link[-4:-1]
	return version


def updatecheck(config):
	version = getversion()
	if (config['instbuild'] + config['interval']) <= version:
		return 1
	else:
		return 0
		
def updatewd():
	path = _conf.getconf('Handle','path_to_bukkit')
	worldconfig = _conf.getconf('Handle','worlds')
	worlds = worldconfig.split()
	backuppath = _conf.getconf('Handle','original_path')
	_conf.getlock('cwc').acquire()
	if not os.path.exists(backuppath + '/wd/'):
		os.mkdir(backuppath + '/wd/')
	for world in worlds:
		if not os.path.exists(backuppath + '/wd/' + world):
			os.mkdir(backuppath + '/wd/' + world)
		os.system('rsync -r -t -v ' + path + '/' + world + ' ' + backuppath + '/wd/ > ./wd/' + world + 'changes') 
	_conf.getlock('cwc').release()

def serversay(message):
	screen = _conf.getconf('Handle','screen_bukkit')
	#os.system('screen -S ' + screen + ' -p 0 -X stuff "`printf "say ' + message + '\r"`"')
	
def startgui(screen):
	guiid = globals()['gui'](screen)
	_conf.setgui(guiid)
	guiid.start()

		
#---------new config--------------------
global _conf
_conf = database()	
_conf.initserver()	

_conf.getqueue('server').put_nowait('start')

#------------------------------------------------------

prog = globals()['startgui']
curses.wrapper(prog)
servercontroller = servercontrol()
scheduler = scheduler()
_conf.gui.handlesay('Handle version 0.1')
servercontroller.start()
scheduler.start()
terminalinst = terminal()
terminalinst.start()