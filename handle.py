import threading
import Queue
import lib.server as server
import lib.gui as gui
import lib.network3 as network
import logging
from lib.task import Task
from lib.network3 import NetworkCommand
from lib.network3 import Packet
class Base(threading.Thread):
	def __init__(self):
		self.comp = {}
		self.tasks = Queue.Queue(maxsize = 0)
		self.exit = False
		self.comp['database'] = server.Database()
		self.comp['database'].loadconfig()
		self.log = None
		self.handlers = {
					Task.HDL_COMMAND:self.__handle_hdl_command,
					Task.HDL_EXIT:self.__handle_hdl_exit,
					Task.HDL_UPDATE:self.__handle_hdl_update,
					Task.HDL_CHECKUP:self.__handle_hdl_checkup,
					Task.NET_JOB:self.__handle_net_job,
					Task.NET_SCREEN:self.__handle_net_screen,
					Task.NET_VERSION:self.__handle_net_version,
					Task.NET_LINEUP:self.__handle_net_lineup,
					Task.SRV_START:self.__handle_serv_start,
					Task.SRV_STOP:self.__handle_srv_stop,
					Task.SRV_RESTART:self.__handle_srv_restart,
					Task.SRV_INPUT:self.__handle_srv_input,
					Task.CLT_UPDATE:self.__handle_clt_update,
					Task.CLT_INPUT:self.__handle_clt_input,
					Task.CLT_LINEUP:self.__handle_clt_lineup
				}
		threading.Thread.__init__( self )
	
	def run(self):
		while not self.exit:
			try:
				task = self.tasks.get(True,0.1)
			except Queue.Empty:
				pass
			else:
				if self.log:
					self.log.debug('GOT TASK: ' + str(task.type))
				self.handlers[task.type](task)

	def __handle_hdl_command(self, cmd):
		return False
	def __handle_hdl_exit(self, cmd):
		return False
	def __handle_hdl_update(self, cmd):
		return False
	def __handle_hdl_checkup(self, cmd):
		return False
	def __handle_net_job(self, cmd):
		return False
	def __handle_net_screen(self, cmd):
		return False
	def __handle_net_version(self, cmd):
		return False
	def __handle_net_lineup(self, cmd):
		return False
	def __handle_serv_start(self, cmd):
		return False
	def __handle_srv_stop(self, cmd):
		return False
	def __handle_srv_restart(self, cmd):
		return False
	def __handle_srv_input(self, cmd):
		return False
	def __handle_clt_update(self, cmd):
		return False
	def __handle_clt_input(self, cmd):
		self.log.debug('running input base')
		return False
	def __handle_clt_lineup(self, cmd):
		return False
	def addtask(self, task):
		self.tasks.put(task)


class Handle(Base):
	def __init__(self):
		Base.__init__( self )
		#create instance of bukkit controller
		self.comp['bukkit'] = server.Bukkit(self.comp['database'], self)
		#create Networking
		self.comp['network'] = network.Network(self.tasks)
		self.comp['network'].cmd_q.put(NetworkCommand(NetworkCommand.SERVE, ( '', int(self.comp['database'].config['Handle']['port']))))
		logging.basicConfig(level=logging.DEBUG, filename='server.log', format='%(asctime)s %(name)s %(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
		self.log = logging.getLogger('MainServer')
		self.comp['network'].setlogfile('server.log')
		self.handlers = {
					Task.HDL_COMMAND:self.__handle_hdl_command,
					Task.HDL_EXIT:self.__handle_hdl_exit,
					Task.HDL_UPDATE:self.__handle_hdl_update,
					Task.HDL_CHECKUP:self.__handle_hdl_checkup,
					Task.NET_JOB:self.__handle_net_job,
					Task.NET_SCREEN:self.__handle_net_screen,
					Task.NET_VERSION:self.__handle_net_version,
					Task.NET_LINEUP:self.__handle_net_lineup,
					Task.SRV_START:self.__handle_serv_start,
					Task.SRV_STOP:self.__handle_srv_stop,
					Task.SRV_RESTART:self.__handle_srv_restart,
					Task.SRV_INPUT:self.__handle_srv_input
				}
	def start(self):
		self.comp['network'].start()
		Base.start( self )

	def parsecommand(self, command):
		if command == 'start':
			self.addtask({'id':'server.start'})
		elif command == 'stop':
			self.addtask({'id':'server.stop'})
		elif command == 'help':
			self.addtask({'id':'network.lineup', 'data':'[HANDLE] Command	Description'})
			self.addtask({'id':'network.lineup', 'data':'[HANDLE] start		Start the server'})
			self.addtask({'id':'network.lineup', 'data':'[HANDLE] stop		Stop the server'})
			self.addtask({'id':'network.lineup', 'data':'[HANDLE] restart	Restart the Server'})
			self.addtask({'id':'network.lineup', 'data':'[HANDLE] exit		Stop the server and close Handle'})
			self.addtask({'id':'server.input', 'data':'help'})
		else:
			self.addtask({'id':'server.input', 'data':command})
	
	def __handle_hdl_command(self, cmd):
		self.parsecommand(cmd.data)
		
	def __handle_hdl_exit(self, cmd):
		return False
	def __handle_hdl_update(self, cmd):
		return False
	def __handle_hdl_checkup(self, cmd):
		return False
	def __handle_net_job(self, cmd):
		return False
	def __handle_net_screen(self, cmd):
		return False
	def __handle_net_version(self, cmd):
		return False
	def __handle_net_lineup(self, cmd):
		self.comp['network'].cmd_q.put(NetworkCommand(NetworkCommand.SEND, Packet(Packet.LINEUP, cmd.data)))

	def __handle_serv_start(self, cmd):
		self.comp['bukkit'].startserver()
		
	def __handle_srv_stop(self, cmd):
		self.comp['bukkit'].stopserver()
		
	def __handle_srv_restart(self, cmd):
		return False
	def __handle_srv_input(self, cmd):
		self.comp['bukkit'].input(task['data'])


class Client(Base):
	def __init__(self):
		Base.__init__( self )
		self.comp['network']= network.Network(self.tasks)
		self.comp['network'].cmd_q.put(NetworkCommand(NetworkCommand.CONNECT, ( '127.0.0.1', int(self.comp['database'].config['Handle']['port']))))
		self.comp['gui'] = gui.Gui(self)
		logging.basicConfig(level=logging.DEBUG, filename='client.log', format='%(asctime)s %(name)s %(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
		self.log = logging.getLogger('MainClient')
		self.comp['network'].setlogfile('client.log')
		self.handlers = {

					Task.CLT_INPUT:self.__handle_clt_input,
					Task.CLT_LINEUP:self.__handle_clt_lineup
				}
	def start(self):
		self.comp['network'].start()
		Base.start( self )

	def __handle_clt_input(self, cmd):
		self.comp['network'].cmd_q.put(NetworkCommand(NetworkCommand.SEND, Packet(Packet.INPUT, cmd.data)))
		self.log.debug('running input')

		
	def __handle_clt_lineup(self, cmd):
		self.comp['gui'].addline(cmd.data)
		self.log.debug('running lineup')
	
	
	
	
	
