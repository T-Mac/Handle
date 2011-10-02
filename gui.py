#!/usr/bin/env python


import curses
import curses.wrapper


def guiinit(screen):
	windows = {}
	screen.clear()
	max = screen.getmaxyx()
	textbox = screen.subwin(max[0]-3,0)
	info = screen.subwin(max[0]-3,16,0,max[1]-16)
	status = screen.subwin(max[0]-3,max[1]-16,0,0)
	textbox.box()
	status.box()

	info.box()
	screen.refresh()
	windows['text'] = textbox
	windows['info'] = info
	windows['status'] = status
	curses.echo()
	return windows
	







def gui(screen):
	x = True
	windows = guiinit(screen)
	while x == True:


		windows['text'].addstr(1,1,'>')
		test = windows['text'].getstr(1,2)
	curses.endwin()
prog = globals()['gui']
curses.wrapper(prog)