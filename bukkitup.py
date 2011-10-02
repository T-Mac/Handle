import feedparser
import ConfigParser
import urllib
import shutil
import os.path
import socket
import time
import os.path
from optparse import OptionParser

def getversion():
	#Read from CraftBukkit Build RSS
	bukkit = feedparser.parse('http://ci.bukkit.org/job/dev-CraftBukkit/rssAll')
	# Extract current version
	step = bukkit.entries[0].link[-4:]
	version = int(step[:3])
	return version

def loadconfig():
	config = {}
	#Check for commandline args
	parser = OptionParser()
	parser.add_option("-t", "--test", action="store_true", dest="testmode", default=False, help="Enable Test Mode")
	parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False, help="Be more Verbose")
	(options, args) = parser.parse_args()
	config['test'] = options.testmode
	config['verbose'] = options.verbose
	if config['test'] == True:
		print 'Test Mode Enabled'
	if config['verbose'] == True:
		print 'Verbose Mode Enabled'
	
	#If Config File Exist... Load it
	if os.path.exists('bukkitup.cfg'):
		#Create Config Parser
		configfile = ConfigParser.RawConfigParser()
		#Read Config File
		configfile.read('bukkitup.cfg')
		autoup = configfile.getboolean('Config','autoupdate')
		bukkitloc = configfile.get('Config','pathtobukkit')
		interval = configfile.getint('Config','updateevery')
		reint = configfile.getint('Config','Restartint')
		backint = configfile.getint('Config','Backupint')
		mapint = configfile.getint('Config','Mapint')
		checkint = configfile.getint('Config','checkinterval')
		if configfile.has_option('Config','currentbuild'):
			build = configfile.getint('Config','currentbuild')
		else:
			build = 0
			configfile.set('Config','currentbuild','0')
			configfile2 = open('bukkitup.cfg', 'wb')
			configfile.write(configfile2)
			configfile2.close()
			
		#Store Config Values for return
		config['interval'] = interval
		config['bukkit'] = bukkitloc
		config['autoup'] = autoup
		config['instbuild'] = build
		config['reint'] = reint
		config['backint'] = backint
		config['mapint'] = mapint
		config['checkint'] = checkint
		return config
	#Otherwise Generate a default one
	else:
		configfile = ConfigParser.RawConfigParser()
		configfile.add_section('Config')
		configfile.set('Config', 'UpdateEvery', '0') 
		configfile.set('Config', 'PathtoBukkit', '.')
		configfile.set('Config', 'Autoupdate', 'false')
		configfile.set('Config', 'Restartint', '0')
		configfile.set('Config', 'Backupint', '0')
		configfile.set('Config', 'Mapint', '0')
		configfile.set('Config', 'checkinterval', '0')
		
		configfile2 = open('bukkitup.cfg', 'wb')
		configfile.write(configfile2)
		configfile2.close()
			
		return loadconfig()


		
def updatecheck(config):
	print 'Getting Latest Version.....',
	config['curbuild'] = getversion()
	print str(config['curbuild'])
	print 'Installed Version', config['instbuild']
	if (config['curbuild'] - config['instbuild']) >= config['interval']:
		print 'Update Interval Reached!'
		if config['autoup']:
			print 'Auto Update: True'
			print 'Starting Update'
			update(config['curbuild'])
		else:
			print 'Auto Update: False'
			print 'Not Updating....Exiting'
	else:
		print 'Update Interval Not Reached....',
		print 'Not Updating'
		
		
def update(version):
	print 'Downloading File....',
	url = 'http://ci.bukkit.org/job/dev-CraftBukkit/' + str(version) + '/artifact/target/craftbukkit-0.0.1-SNAPSHOT.jar'
	urllib.urlretrieve(url,'craftbukkit.jar')
	print 'Download Completed!'
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

def chattimer(msg, secs):
	cmdpre = 'screen -S mine -p 0 -X stuff "`printf "say '
	cmdsuf = '\r"`"'
	a = 0
	if secs > 10:
		while a < 3:
			os.system(cmdpre + msg + ' in ' + str(secs) + ' seconds' + cmdsuf)
			print msg + ' in ' + str(secs) + ' seconds'
			secs = secs/2
			time.sleep(secs)
			a = a + 1
		if secs > 20:
			os.system(cmdpre + msg + ' in 10 seconds' + cmdsuf)
			print msg + ' in 10 seconds'
			time.sleep(10)
			os.system(cmdpre + msg + ' NOW' + cmdsuf)
			print msg + ' NOW'
		
	else:
		os.system(cmdpre + msg + ' in 10 seconds' + cmdsuf)
		time.sleep(10)
		os.system(cmdpre + msg + ' NOW' + cmdsuf)
	
	
def servercontrol(oper):
	startcmd = 'screen -dmS mine java -Xmx2560M -Xms2560M -jar craftbukkit.jar'
	stopcmd = 'screen -S mine -p 0 -X stuff "`printf "stop\r"`"'
	if oper == 'start':
		print 'Starting Server....'
		os.system(startcmd)
		print 'Server Started!'
	elif oper == 'stop':
		chatttimer('Server', 60)
		os.system(stopcmd)
	elif oper =='restart':
		chattimer('Server Restart', 300)
		print 'Stopping Server....'
		os.system(stopcmd)
		print 'Server Stopped!.......Waiting 30 secs'
		time.sleep(30)
		print 'Starting Server....'
		os.system(startcmd)
		print 'Server Started!'

def mapper(mode):
	mapperfull = '/minecraft/pigmap/pigmap/pigmap -B 6 -T 1 -Z 10 -i /minecraft/pigmap/world/ -o /var/www/html/map -g /minecraft/pigmap/ -h 4 -m /minecraft/pigmap/pigmap'
	htmlmove = 'mv -f /var/www/html/map/pigmap-default.html /var/www/html/map/index.html'
	mapperupdate = '/minecraft/pigmap/pigmap/pigmap -i /minecraft/pigmap/world/ -o /var/www/html/map -g /minecraft/pigmap/ -c /minecraft/pigmap/changes -h 4 -x -m /minecraft/pigmap/pigmap'
	mappersync = 'rsync -r -t -v /minecraft/minesrv/world /minecraft/pigmap/ > /minecraft/pigmap/change'
	mapperchanges = 'tail -n +3 /minecraft/pigmap/change > /minecraft/pigmap/changes'
	os.system(mappersync)
	os.system(mapperchanges)
	if mode == 'full':
		chattimer('Full Map Update',60)
		os.system(sync)
		os.system(mapperfull)
		os.system(htmlmove)
		serversay('Mapping Done!')
	elif mode == 'update':
		chattimer('Partial Map Update',60)
		os.system(mappersync)
		os.system(mapperchanges)
		os.system(mapperupdate)
		os.system(htmlmove)
		serversay('Mapping Done!')
	elif mode =='sync':
		os.system(mappersync)
		os.system(mapperchanges)
	
def backup():
	chattimer('World Backup',60)
	mapper('sync')
	os.system('tar -cf /minecraft/backups/' + str(time.strftime('%b%d%H%M')) + '.tar.gz /minecraft/pigmap/world')

def timer(x,timers,params):
	if x == 1:
		curtime =int(time.time())
		retime = params['reint'] + curtime
		backtime = params['backint'] + curtime
		maptime = params['mapint'] + curtime
		timers = {}
		timers['retime'] = retime
		timers['backtime'] = backtime
		timers['maptime'] = maptime
		return timers
	else:
		curtime = int(time.time())
		
		backrem = 'blah'
		restrem = 'blah'
		maprem = 'blah'
		
		if curtime > timers['backtime']:
			if params['backint'] != 0:
				print 'Backing Up....'
				if params['test'] == False: backup()
				curtime = int(time.time())
				timers['backtime'] = curtime + params['backint']
				print 'Secs until Backup:',params['backint']
		else:
			backrem = timers['backtime'] - curtime
		
		if curtime > timers['retime']:
			if params['reint'] != 0:
				print 'Restarting'
				if params['test'] == False:servercontrol('restart')
				curtime = int(time.time())
				timers['retime'] = curtime + params['reint']
				print 'Secs until Restart:',params['reint']
		else:
			restrem = timers['retime'] - curtime
		
		if curtime > timers['maptime']:
			if params['mapint'] != 0:
				print 'Mapping'
				if params['test'] == False:mapper('update')
				curtime = int(time.time())
				timers['maptime'] = curtime + params['mapint']
				print 'Secs until Mapper:',params['reint']
		else:
			maprem = timers['maptime'] - curtime
		
		curtime = int(time.time())
		
		if backrem != 'blah':
			timers['backtime'] = curtime + backrem
		if restrem != 'blah':
			timers['resttime'] = curtime + restrem
		if maprem != 'blah':
			timers['resttime'] = curtime + maprem		
		
		return timers

def serversay(text):
	cmdpre = 'screen -S mine -p 0 -X stuff "`printf "say '
	cmdsuf = '\r"`"'
	os.system(cmdpre + text + cmdsuf)



#---------------------------------------------------MAIN
	
config = loadconfig()

updatecheck(config)
x = 1
timers = {}
if config['test'] == False:servercontrol('start')
while 1:
	timers = timer(x,timers,config)
	x = 0
	if config['verbose'] == True:
		curtime = int(time.time())
		print 'Backup in  ' + str((timers['backtime'] - curtime)/60) + ' minutes'
		print 'Restart in ' + str((timers['retime'] - curtime)/60) + ' minutes'
		print 'Map in ' + str((timers['maptime'] - curtime)/60) + ' minutes'
		print ''
		curtime = int(time.time()) + config['checkint']	
		curtimestruct = time.localtime(curtime)
		print 'Current time '+ time.strftime('%H:%M:%S',time.localtime())
		print 'Next check at ' + time.strftime('%H:%M:%S',curtimestruct)

	time.sleep(config['checkint'])
	
	
	
	
	
	
	
