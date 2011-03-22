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
		x = self.time
		
		while x > 360:
			if self.cancel.isSet():
				print self.message + ' timer canceling'
				self.signal.set()
				return ''
			x = x - 10
			time.sleep(10)
		threshhold = 360		
		while x <= 360 and x > 20:
			if self.cancel.isSet():
				print self.message + ' timer canceling'
				self.signal.set()
				return ''
			if x > 60 and x <= threshhold:
				self.chatlock.acquire()
				print self.message + ' in ' + str(x/60) + ' minutes'
				self.chatlock.release()
				threshhold = x/2
			if x < 60 and x <=threshhold:
				self.chatlock.acquire()
				print self.message + ' in ' + str(x) + ' secs'
				self.chatlock.release()
				threshhold = x/2
				x = x - 30
			time.sleep(30)
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
				self.signal.set()
				print self.message + ' timer canceling'
				return ''
			self.chatlock.acquire()
			print self.message + 'in ' + str(y) + ' secs'
			self.chatlock.release()
			time.sleep(1)
			y = y-1
		self.signal.set()

			
class mapper(threading.Thread):
	def __init__( self, event, objlock, locks):
		self.event = event
		self.locks = locks
		self.objlock  = objlock
		threading.Thread.__init__ ( self )
	def run(self):
		#Load config
		self.objlock.acquire()
		configfile = ConfigParser.RawConfigParser()
		configfile.read('handle.cfg')
		interval = configfile.getint('Mapper','interval')
		signal = threading.Event()
		timer = chattimer(signal, self.event, 'Server map', interval, self.locks['chat'])
		timer.start()
		signal.wait()
		if self.event.isSet():
			self.objlock.release()
			print 'Mapper canceling'
			return ''
		#updatewd()
		self.locks['cwc'].acquire()
		print 'Mapping......',
		time.sleep(5)
		print 'Done!'
		self.locks['cwc'].release()
		self.objlock.release()
		
class backup(threading.Thread):
	def __init__( self, event, objlock, locks):
		self.event = event
		self.locks = locks
		self.objlock = objlock
		threading.Thread.__init__ ( self )
	def run(self):
		#Load config
		self.objlock.acquire()
		configfile = ConfigParser.RawConfigParser()
		configfile.read('handle.cfg')
		interval = configfile.getint('Backup','interval')
		signal = threading.Event()
		timer = chattimer(signal, self.event, 'Backup', interval, self.locks['chat'])
		timer.start()
		print 'started thread'
		signal.wait()
		if self.event.isSet():
			self.objlock.release()
			print 'Backup cancelling'
			return ''
		#updatewd()
		self.locks['cwc'].acquire()
		print 'Backing up......',
		time.sleep(5)
		print 'Done!'
		self.locks['cwc'].release()
		self.objlocks.release()
class scheduler(threading.Thread):
	def __init__( self, locks, events, objs, config):
		self.locks = locks
		self.events = events
		self.objs = objs
		self.config = config
		#self.queue = queue
		

		threading.Thread.__init__ ( self )
	def run(self):
		while config['serverstop'].isSet() !=True:
			x = 0
			while x <= (len(self.objs)-1):
				if self.locks[x].acquire(False):
					self.locks[x].release()
					thread = self.objs[x](self.events[x], self.locks[x], self.config['locks'])
					thread.start()
				x = x + 1
			time.sleep(10)
		x = 0
		while x <= (len(self.objs)-1):
			self.events[x].set()
			self.locks[x].acquire()
			x = x+1
		config['allclear'].set()

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
	serverlocks['chat'] = threading.Lock()
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
	objs.append(globals()['mapper'])
	objs.append(globals()['backup'])
	
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
config['serverstop'] = serverstop
config['locks'] = serverlocks
config['allclear'] = threading.Event()
servercontroller = servercontrol('start', config, serverlocks['server'], serverstop)
scheduler = scheduler(schedulerlocks, events, objs, config)
servercontroller.start()
scheduler.start()
test = raw_input()
serverstop.set()
config['allclear'].wait()