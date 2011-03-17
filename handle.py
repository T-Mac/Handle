from feedparser import parse
import ConfigParser
import threading
import time
import sys

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
		if self.config['bukkit'][-1:] != '/':
			path = self.config['bukkit'] + '/craftbukkit.jar'
		else:
			path = self.config['bukkit'] + 'craftbukkit.jar'
		startcmd = 'screen -dmS ' + self.config['screen'] +  ' java -Xmx' + str(self.config['startheap']) + ' -Xms' + str(config['maxheap'])  + ' -jar' + str(path)
		stopcmd = 'screen -S ' + self.config['screen'] + '-p 0 -X stuff "`printf "stop\r"`"'
		if self.oper == 'start':
			print 'Starting Server....'
			self.lockobj.acquire()
			os.system(startcmd)
			print 'Server Started!'
			self.eventobj.wait()
			#self.lockobj.release()
		#elif self.oper == 'stop':
			#chatttimer('Server', 60)
			#os.system(stopcmd)
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
	def __init__( self, lockobj, eventobj, message, time, function, chatlock):
		self.eventobj = eventobj
		self.massage = message
		self.time = time
		self.function = function
		self.lockobj = lockobj
		threading.Thread.__init__ ( self )
	def run(self):
		x = self.timer
		if x > 360:
			x = x - 360
			time.sleep(x)
		while x >= 30:
			if x > 60:
				print self.message + ' in' + str(x/60) + ' minutes'
			if x < 60:
				print self.message + ' in' + str(x) + ' secs'
			x = x/2
			time.sleep(x)
		print self.message + 'in 15 secs'
		time.sleep(5)
		print self.message + 'in 10 secs'
		time.sleep(5)
		y = 5
		while y > 0:
			print self.message + 'in ' + str(y) + ' secs'
			time.sleep(1)
			y = y-1
		thread = self.function()
		thread.start()

			
		
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
		configfile = ConfigParser.RawConfigParser()
		configfile.read('handle.cfg')
		#Load Options
		config['autoup'] = configfile.getboolean('Config','autoupdate')
		config['bukkit'] = configfile.get('Config','pathtobukkit')
		config['interval'] = configfile.getint('Config','updateevery')
		config['startheap'] = configfile.getint('Config','startheap')
		config['maxheap'] = configfile.getint('Config','maxheap')
		config['screen'] = configfile.getint('Config','screen')
		#Load Build Number if known
		if configfile.has_option('Config','currentbuild'):
			config['instbuild'] = configfile.getint('Config','currentbuild')
		else:	
			#otherwise set to 0 and save it
			config['instbuild'] = 0
			configfile.set('Config','currentbuild','0')
			configfile2 = open('bukkitup.cfg', 'wb')
			configfile.write(configfile2)
			configfile2.close()
	else:
		print 'No config file found'
		print 'Quitting......'

def updatecheck(config):
	version = getversion()
	if (config['instbuild'] + config['interval']) <= version:
		return 1
	else:
		return 0
		
def initlocks(objs):
	x = len(objs)
	locks = []
	while x >=0:
		locks.append(threading.Lock()	)
		x = x+1
	print 'Done allocating locks'
	return locks
	
def initevents(objs):
	x = lens(objs)
	events = []
	while x >=0:
		events.append(thredding.Event())
		x = x+1
	print 'Done allocating events'
		
def initobjs():
	objs = ['servercontrol', 'mapper', 'chat',]
	
def threadcreate(name):
	threadid = globals()[name]
	
	
class test(threading.Thread):			
	def test(self, test):
		print test		
		test = 'blah2'
		return test

blah = test()
blah2 = blah.test('11')
print blah2