from feedparser import parse
import ConfigParser
import threading
import time
import sys
import os
import Queue

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
		global serveraction
		if self.config['bukkit'][-1:] != '/':
			path = self.config['bukkit'] + '/craftbukkit.jar'
		else:
			path = self.config['bukkit'] + 'craftbukkit.jar'
		startcmd = 'screen -dmS ' + self.config['screenbukkit'] +  ' java -Xmx' + str(self.config['startheap']) + 'M -Xms' + str(config['maxheap'])  + 'M -jar ' + str(path)
		stopcmd = 'screen -S ' + self.config['screenbukkit'] + ' -p 0 -X stuff "`printf "stop\r"`"'
		self.lockobj.acquire()
		while True:
			oper = self.oper.get()		
			serveraction.clear()
			if oper == 'start':
				print 'Starting Server....',
				os.chdir(config['bukkit'])
				os.system(startcmd)
				os.chdir(config['origpath'])
				print 'Started!'
				serveraction.wait()
			elif oper == 'stop':
				#chatttimer('Server', 60)
				os.system(stopcmd)
				serveraction.wait()
			elif oper =='restart':
				#chattimer('Server Restart', 300)
				print 'Stopping Server....'
				os.system(stopcmd)
				print 'Server Stopped!.......Waiting 30 secs'
				time.sleep(30)
				print 'Starting Server....'
				os.system(startcmd)
				print 'Server Started!'
				serveraction.wait()
			elif oper == 'release':
				self.lockobj.release()
				print 'Server lock released!'
				time.sleep(1)
			elif oper == 'kill':
				os.system(stopcmd)
				return
			
class chattimer(threading.Thread):
	def __init__( self, config):
		self.config = config
		threading.Thread.__init__ ( self )
	def run(self):
		x = self.config['interval']	
		nextrun = time.time() + x
		print self.config['message'] + ' at ' + time.strftime('%H:%M',time.localtime(nextrun))
		while x > 360:
			if self.config['cancel'].isSet():
				print self.config['message'] + ' timer canceling'
				self.config['signal'].set()
				return ''
			x = x - 10
			time.sleep(10)
		threshhold = 360		
		while x <= 360 and x > 20:
			if self.config['cancel'].isSet():
				print self.config['message'] + ' timer canceling'
				serversay(self.config['message'] + ' canceling')
				self.config['signal'].set()
				return ''
			if x > 60 and x <= threshhold:
				self.config['chatlock'].acquire()
				print self.config['message'] + ' in ' + str(x/60) + ' minutes'
				serversay(self.config['message'] + ' in ' + str(x/60) + ' minutes')
				self.config['chatlock'].release()
				threshhold = x/2
			if x < 60 and x <=threshhold:
				self.config['chatlock'].acquire()
				print self.config['message'] + ' in ' + str(x) + ' secs'
				serversay(self.config['message'] + ' in ' + str(x) + ' secs')
				self.config['chatlock'].release()
				threshhold = x/2
				x = x - 30
			time.sleep(30)
		self.config['chatlock'].acquire()
		print self.config['message'] + ' in 15 secs'
		serversay(self.config['message'] + ' in 15 secs')
		self.config['chatlock'].release()
		time.sleep(5)
		self.config['chatlock'].acquire()
		print self.config['message'] + ' in 10 secs'
		serversay(self.config['message'] + ' in 10 secs')
		self.config['chatlock'].release()
		time.sleep(5)
		y = 5
		while y > 0:
			if self.config['cancel'].isSet():
				self.config['signal'].set()
				print self.config['message'] + ' timer canceling'
				serversay(self.config['message'] + ' canceling')
				return ''
			self.config['chatlock'].acquire()
			print self.config['message'] + ' in ' + str(y) + ' secs'
			serversay(self.config['message'] + ' in ' + str(y) + ' secs')
			self.config['chatlock'].release()
			time.sleep(1)
			y = y-1
		self.config['signal'].set()

			
class mapper(threading.Thread):
	def __init__( self, event, objlock, locks):
		self.event = event
		self.locks = locks
		self.objlock  = objlock
		threading.Thread.__init__ ( self )
	def run(self):
		#Load config
		config = {}
		self.objlock.acquire()
		configfile = ConfigParser.RawConfigParser()
		configfile.read('handle.cfg')
		config['interval'] = configfile.getint('Mapper','interval')
		config['screenbukkit'] = configfile.get('Handle','screen_bukkit')
		config['message'] = 'Server map'
		config['signal'] = threading.Event()
		config['cancel'] = self.event
		config['chatlock'] = self.locks['chat']
		#Create timer thread
		timer = chattimer(config)
		#start it
		timer.start()
		#wait for signal
		config['signal'].wait()
		if self.event.isSet():
			self.objlock.release()
			print 'Mapper canceling'
			return ''
		updatewd()
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
		config = {}
		configfile = ConfigParser.RawConfigParser()
		configfile.read('handle.cfg')
		config['interval'] = configfile.getint('Backup','interval')
		config['signal'] = threading.Event()
		config['cancel'] = self.event
		config['chatlock'] = self.locks['chat']
		config['message'] = 'Backup'
		config['screenbukkit'] = configfile.get('Handle','screen_bukkit')
		config['path'] = configfile.get('Handle','path_to_bukkit')
		config['worlds'] = configfile.get('Handle','worlds')
		config['worlds'] = config['worlds'].strip()
		timer = chattimer(config)
		timer.start()
		config['signal'].wait()
		if self.event.isSet():
			self.objlock.release()
			print 'Backup cancelling'
			return ''
		updatewd()
		self.locks['cwc'].acquire()
		print 'Backing up......',
		if os.path.exists(config['path'] + '/wd/') == False:
			os.mkdir(config['path'] + '/wd')
		for world in config['worlds']:
			os.system('tar -cf ./backups/' + world + '/' + str(time.strftime('%b-%d-%H:%M')) + '.tar.gz' + config['path'] + world)
		print 'Done!'
		self.locks['cwc'].release()
		self.objlock.release()
		
class restarter(threading.Thread):
	def __init__( self, event, objlock, locks):
		self.event = event
		self.locks = locks
		self.objlock = objlock
		threading.Thread.__init__ ( self )
	def run(self):
		self.objlock.acquire()
		config = {}
		configfile = ConfigParser.RawConfigParser()
		configfile.read('handle.cfg')
		config['interval'] = configfile.getint('Restart','interval')
		config['signal'] = threading.Event()
		config['cancel'] = self.event
		config['message'] = 'Server restart'
		config['screenbukkit'] = configfile.get('Handle','screen_bukkit')
		config['chatlock'] = self.locks['chat']
		timer = chattimer(config)
		timer.start()
		config['signal'].wait()
		if self.event.isSet():
			self.objlock.release()
			print 'Restarter Canceling'
			return ''
		serverque.put('restart')
		serveraction.set()
		objlock.release()
		
		
		
		
class scheduler(threading.Thread):
	def __init__( self, locks, events, objs, config, queue):
		self.locks = locks
		self.events = events
		self.objs = objs
		self.config = config
		self.queue = queue
		

		threading.Thread.__init__ ( self )
	def run(self):
		os.chdir(config['origpath'])
		while config['serverstop'].isSet() !=True:
			x = 0
			while x <= (len(self.objs)-1):
				if self.locks[x].acquire(False):
					self.locks[x].release()
					thread = self.objs[x](self.events[x], self.locks[x], self.config['locks'])
					thread.start()
				x = x + 1
				
		x = 0
		print 'Killing Threads.....'
		config['serverque'].put('kill')
		global serveraction
		serveraction.set()
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
		config['origpath'] = os.getcwd()
		configfile.set('Handle','original_path',config['origpath'])
		file = open('handle.cfg', 'wb')
		configfile.write(file)
		file.close()
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
	#objs.append(globals()['mapper'])
	objs.append(globals()['backup'])
	objs.append(globals()['restarter'])
	
	print 'Done obtaining objects'
	return objs
def threadcreate(name):
	threadid = globals()[name]
	
def updatewd():
	configfile = ConfigParser.RawConfigParser()
	configfile.read('handle.cfg')
	path = configfile.get('Handle','path_to_bukkit')
	worldconfig = configfile.get('Handle', 'worlds')
	worlds = worldconfig.split()
	backuppath = configfile.get('Handle','original_path')
	serverlocks['cwc'].acquire()
	for world in worlds:
		os.system('rsync -r -t -v ' + path + '/' + world + ' ./wd/ > ./wd/' + world + 'changes') 
	serverlocks['cwc'].release()
	# rsync -r -t -v /minecraft/minesrv/world /minecraft/pigmap/ > /minecraft/pigmap/change'
	#os.system('rsync -r ' + path + 'world/ .')

def serversay(message):
	configfile = ConfigParser.RawConfigParser()
	configfile.read('handle.cfg')
	screen = configfile.get('Handle','screen_bukkit')
	os.system('screen -S ' + screen + ' -p 0 -X stuff "`printf "say ' + message + '\r"`"')
	
config = loadconfig()
objs = initobjs()
schedulerlocks = initschlocks(objs)
global serverlocks
serverlocks = initserverlocks()
events = initevents(objs)
serverstop = threading.Event()
config['serverstop'] = serverstop
global serveraction
serveraction = threading.Event()
config['locks'] = serverlocks
config['allclear'] = threading.Event()
config['schedque'] = Queue.Queue(maxsize=0)
global serverque
config['serverque'] = Queue.Queue(maxsize=0)
serverque = config['serverque']
config['serverque'].put_nowait('start')
servercontroller = servercontrol(config['serverque'], config, serverlocks['server'], serverstop)
scheduler = scheduler(schedulerlocks, events, objs, config, config['schedque'])
print 'Handle version 0.1'
servercontroller.start()
scheduler.start()
test = raw_input()
serverstop.set()
config['allclear'].wait()