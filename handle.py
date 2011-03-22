from feedparser import parse
import ConfigParser
import threading
import time
import sys
import os

class runfunc(threading.Thread):
	def __init__( self, func, lockobj):
		self.func = func
		self.lockobj = lockobj
		threading.Thread.__init__ ( self )
	def run(self):
		result = globals()[self.func](self.lockobj)
		
class update(threading.Thread):
	def __init__( self, version, lockobj):
		self.lockobj = lockobj
		self.version = version
		threading.Thread.__init__ ( self )
	def run(self):
		version = self.version
		lock = self.lockobj
		print 'Waiting for Lock'
		lock.acquire()
		print 'Lock acquired....',
		print 'Updating....',
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
		print 'Updated!'

class servercontrol(threading.Thread):
	def __init__( self, oper, config, lockobj, eventobj):
		self.oper = oper
		self.lockobj = lockobj
		self.eventobj = eventobj
		self.config = config
		threading.Thread.__init__ ( self )
	def run(self):
		print self.config['bukkit']
		if self.config['bukkit'][-1:] != '/':
			path = self.config['bukkit'] + '/craftbukkit.jar'
		else:
			path = self.config['bukkit'] + 'craftbukkit.jar'
		startcmd = 'screen -dmS ' + self.config['screenbukkit'] +  ' java -Xmx' + str(self.config['startheap']) + 'M -Xms' + str(config['maxheap'])  + 'M -jar ' + str(path)
		stopcmd = 'screen -S ' + self.config['screenbukkit'] + ' -p 0 -X stuff "`printf "stop\r"`"'
		if self.oper == 'start':
			print 'Starting Server....'
			self.lockobj.acquire()
			print startcmd
			os.system(startcmd)
			print 'Server Started!'
			print ' Waiting for shutdown......'
			self.eventobj.wait()
			self.lockobj.release()
		#elif self.oper == 'stop':
			#chatttimer('Server', 60)
			os.system(stopcmd)
		elif self.oper =='restart':
			#chattimer('Server Restart', 300)
			print 'Stopping Server....'
			os.system(stopcmd)
			print 'Server Stopped!.......Waiting 30 secs'
			time.sleep(30)
			print 'Starting Server....'
			os.system(startcmd)
			print 'Server Started!'
			
class chattimer(threading.Thread):
	def __init__( self, signalevent, cancelevent, message, time, chatlock):
		self.signal = signalevent
		self.message = message
		self.time = time
		self.cancel = cancelevent
		self.chatlock = chatlock
		threading.Thread.__init__ ( self )
	def run(self):
		x = self.time * 60
		if x > 360:
			x = x - 360
			time.sleep(x)
		while x >= 30:
			if x > 60:
				self.chatlock.acquire()
				print self.message + ' in' + str(x/60) + ' minutes'
				self.chatlock.release()
			if x < 60:
				self.chatlock.acquire()
				print self.message + ' in' + str(x) + ' secs'
				self.chatlock.release()
				x = x/2
			if self.cancel.isSet():
				return ''
			time.sleep(x)
		self.chatlock.acquire()
		print self.message + 'in 15 secs'
		self.chatlock.release()
		time.sleep(5)
		self.chatlock.acquire()
		print self.message + 'in 10 secs'
		self.chatlock.release()
		time.sleep(5)
		y = 5
		while y > 0:
			if self.cancel.isSet():
				return ''
			self.chatlock.acquire()
			print self.message + 'in ' + str(y) + ' secs'
			self.chatlock.release()
			time.sleep(1)
			y = y-1
		self.signal.set()

			
class mapper(threading.Thread):
	def __init__( self, event, locks):
		self.event = event
		self.locks = locks
		threading.Thread.__init__ ( self )
	def run(self):
		#Load config
		configfile = ConfigParser.RawConfigParser()
		configfile.read('handle.cfg')
		interval = configfile.getint('Mapper','interval')
		signal = threading.Event()
		timer = chattimer(signal, self.event, 'Server map', interval, locks['chat'])
		timer.start()
		signal.wait()
		updatewd()
		self.locks['cwc'].acquire()
		print 'Mapping......',
		time.sleep(5)
		print 'Done!'
		self.locks['cwc'].release()
		
class backup(threading.Thread):
	def __init__( self, event, locks):
		self.event = event
		self.locks = locks
		threading.Thread.__init__ ( self )
	def run(self):
		#Load config
		configfile = ConfigParser.RawConfigParser()
		configfile.read('handle.cfg')
		interval = configfile.getint('Backup','interval')
		signal = threading.Event()
		timer = chattimer(signal, self.event, 'Backup', interval, locks['chat'])
		timer.start()
		signal.wait()
		updatewd()
		self.locks['cwc'].acquire()
		print 'Backing up......',
		time.sleep(5)
		print 'Done!'
		self.locks['cwc'].release()
		
class scheduler(threading.Thread):
	def __init__( self, locks, events, queue):
		self.locks = locks
		self.events = events
		self.queue = queue
		

		threading.Thread.__init__ ( self )
	def run(self):
		print ''

			
			

def getversion():
	#Read from CraftBukkit Build RSS
	bukkit = feedparser.parse('http://ci.bukkit.org/job/dev-CraftBukkit/rssAll')
	# Extract current version
	version = bukkit.entries[0].link[-4:-1]
	return version

def loadconfig():
	if os.path.exists('handle.cfg'):
		#Parse Config File
		config = {}
		configfile = ConfigParser.RawConfigParser()
		configfile.read('handle.cfg')
		config['bukkit'] = configfile.get('Handle','path_to_bukkit')
		config['startheap'] = configfile.getint('Handle','start_heap')
		config['maxheap'] = configfile.getint('Handle','max_heap')
		config['screenbukkit'] = configfile.get('Handle','screen_bukkit')
		return config
	else:
		print 'No config file found'
		print 'Quitting......'

def updatecheck(config):
	version = getversion()
	if (config['instbuild'] + config['interval']) <= version:
		return 1
	else:
		return 0
		
def initschlocks(objs):
	x = len(objs)
	locks = []
	while x >=0:
		locks.append(threading.Lock()	)
		x = x-1
	print 'Done allocating locks'
	return locks
def initserverlocks():
	serverlocks = {}
	serverlocks['server'] = threading.Lock()
	serverlocks['cwc'] = threading.Lock()
	serverlocks['world'] = threading.Lock()
	return serverlocks

def initevents(objs):
	x = len(objs)
	events = []
	while x >=0:
		events.append(threading.Event())
		x = x-1
	print 'Done allocating events'
	return events
	
def initobjs():
	objs = []
	objs.append(globals()['update'])
	
	print 'Done obtaining objects'
	return objs
def threadcreate(name):
	threadid = globals()[name]

config = loadconfig()
objs = initobjs()
schedulerlocks = initschlocks(objs)
serverlocks = initserverlocks()
events = initevents(objs)
serverstop = threading.Event()
servercontroller = servercontrol('start', config, serverlocks['server'], serverstop)
servercontroller.start()
test = raw_input()
serverstop.set()
