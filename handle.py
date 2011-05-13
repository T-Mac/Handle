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
		
		
#--------------------------Class to handle all config files and globaly needed objects----------------------------	--------
class database():
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
		self.threadstatus = {}
		self.queue = {}
		self.uid = 0
		self.locks = {}
		self.exit = None
		self.autoids = []
		self.autoobjs = {}
		self.allclear = threading.Event()
		

		
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
		for k, v in self.threadstatus.items():
			if v == 'reviewed':
				del self.threads[k]
				del self.threadstatus[k]
			
	def cancel(self):
		self.exit = 1
		
	def threadadd(self, object, id = None):
		if id == None:
			id = self.uid
			self.uid += 1	
		else:
			if self.threads.get(id, None) != None:
				raise KeyError('Id: ' + str(id) + ' already exists')

		self.threads[id] = object
		self.threadstate(id, 'ready')
		return id
	
	def threadstate(self, id, status = None):
		if status == None:
			return self.threadstatus[id]
		else:
			self.threadstatus[id] = status
	
	def getthread(self, query = None):
		if query == None:
			return self.threads
		for k, v in self.threads.items():
			if k == query:
				return v
			elif v == query:
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
	def addid(self, id):
		self.autoids.append(id)
	
	def addobj(self, id, obj):
		self.autoobjs[id] = obj
	
#-----------------------------------------		
		
class update(threading.Thread):
	def __init__( self, version):
		self.version = version
		threading.Thread.__init__ ( self )
	def run(self):
		version = self.version
		lock = _conf.getlock('server')
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
		startcmd = 'screen -dmS ' + self.config['screen_bukkit'] +  ' java -Xmx' + str(self.config['start_heap']) + 'M -Xms' + str(self.config['max_heap'])  + 'M -jar ' + str(path)
		stopcmd = 'screen -S ' + self.config['screen_bukkit'] + ' -p 0 -X stuff "`printf "stop\r"`"'
		self.lockobj.acquire()
		while True:
			oper = self.oper.get()		
			if oper == 'start':
				print 'Starting Server....',
				os.chdir(self.config['path_to_bukkit'])
				os.system(startcmd)
				os.chdir(self.config['original_path'])
				print 'Started!'
			elif oper == 'stop':
				#chatttimer('Server', 60)
				os.system(stopcmd)
			elif oper =='restart':
				#chattimer('Server Restart', 300)
				print 'Stopping Server....'
				os.system(stopcmd)
				print 'Server Stopped!.......Waiting 30 secs'
				time.sleep(30)
				print 'Starting Server....'
				os.system(startcmd)
				print 'Server Started!'
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
		self.config['screenbukkit'] = _conf.getconf('Handle','screen_bukkit')
		self.config['chatlock'] = _conf.getlock('chat')
		self.id = self.config['id']
		threading.Thread.__init__ ( self )
	def run(self):
		x = self.config['interval'] * 60
		nextrun = time.time() + x
		print self.config['message'] + ' at ' + time.strftime('%H:%M',time.localtime(nextrun))
		while x > 360:
			if _conf.threadstate(self.id) == 'canceled':
				print self.config['message'] + ' timer canceling'
				serversay(self.config['message'] + ' canceling')
				self.config['signal'].set()
				return None
			x = x - 10
			time.sleep(10)
		threshhold = 360		
		while x <= 360 and x > 20:
			if _conf.threadstate(self.id) == 'canceled':
				print self.config['message'] + ' timer canceling'
				serversay(self.config['message'] + ' canceling')
				self.config['signal'].set()
				return None
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
		if _conf.threadstate(self.id) == 'canceled':
				print self.config['message'] + ' timer canceling'
				serversay(self.config['message'] + ' canceling')
				self.config['signal'].set()
				return None
		time.sleep(5)
		self.config['chatlock'].acquire()
		print self.config['message'] + ' in 10 secs'
		serversay(self.config['message'] + ' in 10 secs')
		self.config['chatlock'].release()
		if _conf.threadstate(self.id) == 'canceled':
				print self.config['message'] + ' timer canceling'
				serversay(self.config['message'] + ' canceling')
				self.config['signal'].set()
				return None
		time.sleep(5)
		y = 5
		while y > 0:
			if _conf.threadstate(self.id) == 'canceled':
				print self.config['message'] + ' timer canceling'
				serversay(self.config['message'] + ' canceling')
				self.config['signal'].set()
				return None
			self.config['chatlock'].acquire()
			print self.config['message'] + ' in ' + str(y) + ' secs'
			serversay(self.config['message'] + ' in ' + str(y) + ' secs')
			self.config['chatlock'].release()
			time.sleep(1)
			y = y-1
		self.config['signal'].set()
		
	def cancel(self):
		if _conf.threadstate(self.id) == 'canceled':
			print self.config['message'] + ' timer canceling'
			serversay(self.config['message'] + ' canceling')
			self.config['signal'].set()
			return True

			
class mapper(threading.Thread):
	def __init__( self):
		threading.Thread.__init__ ( self )
	def run(self):
		#Load config
		self.setid()
		config = {}
		_conf.threadstate(self.id,'running')
		config['interval'] = int(_conf.getconf('Mapper','interval'))
		config['message'] = 'Server map'
		config['signal'] = threading.Event()
		config['id'] = self.id
		#Create timer thread
		timer = chattimer(config)
		#start it
		timer.start()
		#wait for signal
		config['signal'].wait()
		if _conf.threadstate(self.id) == 'canceled':
			_conf.threadstate(self.id,'stopped')
			print 'Mapper canceling'
			return ''
		updatewd()
		_conf.getlock('cwc').acquire()
		print 'Mapping......',
		time.sleep(5)
		print 'Done!'
		_conf.getlock('cwc').release()
		_conf.threadstate(self.id,'stopped')
	def setid(self):
		self.id = _conf.getthread(self)
		
class backup(threading.Thread):
	def __init__( self):
		threading.Thread.__init__ ( self )
	def run(self):
		#Load config
		self.setid()
		_conf.threadstate(self.id,'running')
		config = {}
		config['interval'] = int(_conf.getconf('Backup','interval'))
		config['signal'] = threading.Event()
		config['id'] = self.id
		config['message'] = 'Backup'
		config['path'] = _conf.getconf('Handle','path_to_bukkit')
		config['worlds'] = _conf.getconf('Handle','worlds')
		config['worlds'] = config['worlds'].strip()
		timer = chattimer(config)
		timer.start()
		config['signal'].wait()
		if _conf.threadstate(self.id) == 'canceled':
			_conf.threadstate(self.id,'stopped')
			print 'Backup Canceled'
			return ''
		updatewd()
		_conf.getlock('cwc').acquire()
		print 'Backing up......',
		if os.path.exists(config['path'] + '/wd/') == False:
			os.mkdir(config['path'] + '/wd')
		for world in config['worlds']:
			os.system('tar -cf ./backups/' + world + '/' + str(time.strftime('%b-%d-%H:%M')) + '.tar.gz' + config['path'] + world)
		print 'Done!'
		_conf.getlock('cwc').release()
		_conf.threadstate(self.id, 'stopped')
	def setid(self):
		self.id = _conf.getthread(self)
		
class restarter(threading.Thread):
	def __init__( self):
		threading.Thread.__init__ ( self )
	def run(self):
		self.setid()
		_conf.threadstate(self.id, 'running')
		config = {}
		configfile = ConfigParser.RawConfigParser()
		configfile.read('handle.cfg')
		config['interval'] = int(_conf.getconf('Restart','interval'))
		config['signal'] = threading.Event()
		config['id'] = self.id
		config['message'] = 'Server restart'
		config['screenbukkit'] = _conf.getconf('Handle','screen_bukkit')
		timer = chattimer(config)
		timer.start()
		config['signal'].wait()
		if _conf.threadstate(self.id) == 'canceled':
			_conf.threadstate(self.id,'stopped')
			print 'Restart Canceled'
			return ''
		_conf.getqueue('server').put('restart')
		_conf.threadstate(self.id, 'stopped')
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
			for id in _conf.autoids:
				if _conf.threadstate(id) == 'stopped':
					thread = _conf.autoobjs[id]()
					thread.start()
					
		print 'Killing Threads.....'
		_conf.getqueue('server').put('kill')
		x = 0
		for id, o in _conf.getthread().items():
			_conf.threadstate(id, 'canceled')
			x += 1
		while x > 0:
			for id, o in _conf.getthread().items():
				if _conf.threadstate(id) == 'stopped':
					_conf.threadstate(id,'reviewed')
					print 'Killed: ' + id
					_conf.prune()
					x = x - 1
	
	
		_conf.allclear.set()
	def defaultthreads(self):
		_conf.addid('auto_mapper')
		_conf.addid('auto_backup')
		_conf.addid('auto_restart')
		
		_conf.addobj('auto_mapper', globals()['mapper'])
		_conf.addobj('auto_backup', globals()['backup'])
		_conf.addobj('auto_restart', globals()['restarter'])
		
		for id in _conf.autoids:
			thread = _conf.autoobjs[id]()
			_conf.threadadd(thread,id)
			thread.start()
			

class terminal(threading.Thread):
	def run(self):
		self.prompt()
	
	
	def prompt(self):
		x = True
		while x:
			command = raw_input()
			x = self.interpret(command)
			
	def interpret(self,command):
		if command == 'exit':
			_conf.cancel()
			_conf.allclear.wait()
			return False
		elif command == 'start':
			_conf.getqueue('server').put('start')
		elif command == 'restart':
			_conf.getqueue('server').put('restart')
		elif command == 'sched':
			print _conf.autoids
		else:
			print 'Invalid Command'
		return True
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
	bacluppath = _conf.getconf('Handle','original_path')
	_conf.getlock('cwc').acquire()
	for world in worlds:
		os.system('rsync -r -t -v ' + path + '/' + world + ' ./wd/ > ./wd/' + world + 'changes') 
	_conf.getlock('cwc').release()
	# rsync -r -t -v /minecraft/minesrv/world /minecraft/pigmap/ > /minecraft/pigmap/change'
	#os.system('rsync -r ' + path + 'world/ .')

def serversay(message):
	screen = _conf.getconf('Handle','screen_bukkit')
	os.system('screen -S ' + screen + ' -p 0 -X stuff "`printf "say ' + message + '\r"`"')
	
#---------new conig--------------------
global _conf
_conf = database()	
_conf.initserver()	

_conf.getqueue('server').put_nowait('start')

#------------------------------------------------------

servercontroller = servercontrol()
scheduler = scheduler()
print 'Handle version 0.1'
servercontroller.start()
scheduler.start()
terminalinst = terminal()
terminalinst.start()