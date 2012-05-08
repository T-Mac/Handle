import threading
import Queue
import uuid
import logging 

class Schedule(threading.Thread):
	def __init__(self, reply_q, cmd_q = Queue.Queue(maxsize = 0)):
		self.reply_q = reply_q
		self.cmd_q = cmd_q
		self.events = []
		self.event_lock = threading.Lock()
		self.alive = threading.Event()
		self.alive.set()
		self.handlers = {
			SchedCommand.ADD:self.__add,
			SchedCommand.REMOVE:self.__remove,
			}
		self.log = logging.getLogger('SCHEDULE')
		threading.Thread.__init__(self)
	
	def run(self):
		self.log.debug('Schedule Loop Started')
		while self.alive.isSet():
			try:
				#self.log.debug('Getting Tasks')
				cmd = self.cmd_q.get(True, 0.1)
				self.log.debug('Got Task: %s' % cmd.stype[cmd.type])
				#self.log.debug('Got Task: %s: %s' % cmd.stype[cmd.type], str(cmd.data))
				self.handlers[cmd.type](cmd)
				
			except Queue.Empty:
				#self.log.debug('Empty Q')
				pass
		
		self.log.debug('Dropped from loop')


				
	def __add(self, task):
		if len(task.data) == 3:
			event = Event(task.data[0], task.data[1], task.data[2])
		else:
			event = Event(task.data[0], task.data[1])
		timer = threading.Timer(task.data[1], self.__call, [event])
		event.timer = timer
		self.events.append(event) 		
		self.log.debug('Event Added: %s' % event.task.stype[event.task.type])
		timer.start()
		
	def __remove(self, task):
		self.events.remove(task.data)
		task.data.timer.cancel()
		#self.log.debug('Event Removed: %s, %s : %s' % task.data.id, str(task.data.delay), task.data.task.stype[task.data.task.type])
		
	def join(self):
		for event in self.events:
			event.timer.cancel()
		self.alive.clear()
		self.log.debug('JOIN THREAD BEING CALLED')
		threading.Thread.join(self)
		
	def __call(self, event):
		self.log.debug('Timer Returned - Adding Task %s' % event.task.stype[event.task.type])
		self.reply_q.put(event.task)
		if event.repeat:
		
			scmd = SchedCommand(SchedCommand.ADD, (event.task, event.delay, True))
			self.cmd_q.put(scmd)
			self.log.debug('Repeat Flag: True - Recreating Timer')
		else:
			self.events.remove(event)
			self.log.debug('Repeat Flag: False - Deleting Event')
		
class Event(object):
	def __init__(self, task, delay, repeat=False):
		self.task = task
		self.delay = delay
		self.timer = None
		self.repeat = repeat
		self.id = uuid.uuid4()

		
		
class SchedCommand(object):
	
	'''
	ADD			(task, delay, [repeat])
	REMOVE		id to stop
	'''
	ADD, REMOVE = range(2)
	
	stype = {
		0:'ADD',
		1:'REMOVE',
		}
	

	def __init__(self, type, data = None):
		self.type = type
		self.data = data