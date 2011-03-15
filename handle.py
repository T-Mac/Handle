#Import RSS Parser
from feedparser import parse
#Import Commandline Arguements Parser
from optparse import OptionParser
#Import Config File Parser
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
		#Run function passed
		result = globals()[self.func](self.lockobj)
		
class update(threading.Thread):
	def __init__( self, func, version, lockobj):
		self.func = func
		self.lockobj = lockobj
		self.version = version
		threading.Thread.__init__ ( self )
	def run(self):
		version = self.version
		serverlock = self.lockobj
		print 'Waiting for Lock'
		#Wait for lock
		serverlock.acquire()
		print 'Lock acquired....',
		print 'Updating....',
		url = 'http://ci.bukkit.org/job/dev-CraftBukkit/' + str(version) + '/artifact/target/craftbukkit-0.0.1-SNAPSHOT.jar'
		#Download new server version
		urllib.urlretrieve(url,'craftbukkit.jar')
		if config['bukkit'][-15:] == 'craftbukkit.jar':
			path = config['bukkit']
		else:
			if config['bukkit'][-1:] != '/':
				path = config['bukkit'] + '/craftbukkit.jar'
			else:
				path = config['bukkit'] + 'craftbukkit.jar'
		shutil.move('craftbukkit.jar', path)
		#Save version to config file
		configfile = ConfigParser.RawConfigParser()
		configfile.read('bukkitup.cfg')
		configfile.set('Config','currentbuild',config['curbuild'])
		configfile2 = open('bukkitup.cfg', 'wb')
		configfile.write(configfile2)
		configfile2.close()
		#Release Lock
		serverlock.release()
		print 'Updated!'

class servercontrol(threading.Thread):
	def __init__( self, oper, config, lockobj, eventobj):
		self.oper
		self.lockobj = lockobj
		self.eventobj = eventobj
		self.config = config
		threading.Thread.__init__ ( self )
	def run(self):
		if config['bukkit'][-1:] != '/':
				path = config['bukkit'] + '/craftbukkit.jar'
			else:
				path = config['bukkit'] + 'craftbukkit.jar'
		startcmd = 'screen -dmS mine java -Xmx2560M -Xms2560M -jar' + str(path)
		stopcmd = 'screen -S mine -p 0 -X stuff "`printf "stop\r"`"'
		#Start Server
		if oper == 'start':
			print 'Starting Server....'
			self.lockobj.acquire()
			os.system(startcmd)
			print 'Server Started!'
			self.eventobj.wait()
			self.lockobj.release()
		#Stop Server
		elif oper == 'stop':
			chatttimer('Server', 60)
			os.system(stopcmd)
		#Restart Server
		elif oper =='restart':
			chattimer('Server Restart', 300)
			print 'Stopping Server....'
			os.system(stopcmd)
			print 'Server Stopped!.......Waiting 30 secs'
			time.sleep(30)
			print 'Starting Server....'
			os.system(startcmd)
			print 'Server Started!'

			
			
serverlock = threading.Lock()
mapperlock = threading.Lock()
backuplock = threading.Lock()
restartlock = threading.Lock()
serverlockrelease = threading.Event()
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
		#Load Build Number if known
		if configfile.has_option('Config','currentbuild'):
			config['instbuild'] = configfile.getint('Config','currentbuild')
		else:	
			#otherwise set to 0 and save it
			build = 0
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