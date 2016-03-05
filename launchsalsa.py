#!/usr/bin/python2

#https://pypi.python.org/pypi/alsaseq
import alsaseq

import time

# Button maps - These are the actual MIDI notes
UP = 91
DOWN = 92
LEFT = 93
RIGHT = 94
SESSION = 95
NOTE = 96
DEVICE = 97
USER = 98

SHIFT = 80
CLICK = 70
UNDO = 60
DELETE = 50
QUANTISE = 40
DUPLICATE = 30
DOUBLE = 20
RECORD = 10

ARM = 1
SELECT = 2
MUTE = 3
SOLO = 4
VOLUME = 5
PAN = 6
SENDS = 7
STOP = 8

# Psuedo-notes for buttons that map to arrays
PLAY = 128 
GRID = 129

# MIDI types
_MIDI_CONNECT = 66
_MIDI_DISCONNECT = 67;
_MIDI_ON = 6
_MIDI_OFF = 7
_MIDI_CC = 10
_MIDI_MAFTER = 12
_MIDI_PAFTER = 8

#asla connect numbers
_devi = 0
_devo = 0

# TODO: create functions for each MIDI message
def _midiOut(port, mtype, params):
    alsaseq.output((mtype, 1, 0, 253, (0, 0), (_devi, port), (_devo, 0), params))

def __b2idx(but):
    r = int(but / 10)
    c = int(but - r * 10)
    return r, c

# TODO: seperate classes for including border buttons in grid indexing
# TODO: implement screen regions for scrolling
# TODO: split screens from views (essentially sprites)
class ScreenView:
    def __init__(self, rows = 8, columns = 8):
        self.__rows = rows
        self.__columns = columns
        self._offset = (0, 0)
        self.__grid = []
        self.__dirty = []
        for i in range(0, rows):
            g = []
            d = []
            for i in range(0, columns):
                g.append(0)
                d.append(True)
            self.__grid.append(g)
            self.__dirty.append(d)
    
    # TODO: THE SEMANTICS OF THIS WILL CHANGE
    # TODO: Only grid updates are working
    def update(self, but, val = 0, row = 0, col = 0):
        if but == GRID:
            self.__grid[row - 1][col - 1] = val
            self.__dirty[row - 1][col - 1] = True

    def scroll(self, rows, columns):
        r = self._offset[0] + rows
        c = self._offset[1] + columns
        if r > self.__rows - 8:
            r = self.__rows - 8
        if c > self.__columns - 8:
            c = self.__columns - 8
        if r < 0:
            r = 0
        if c < 0:
            c = 0
        self._offset = (r, c)
        self.redraw()

    def redraw(self):
        self.draw(True)

    def draw(self, redraw = False):
        for r in range(1, 9):
            for c in range(1, 9):
                grow = 9 - r - 1 + self._offset[0]
                gcol = c - 1 + self._offset[1]
                if redraw or self.__dirty[grow][gcol]:
                    _midiOut(1, _MIDI_ON, (0, r * 10 + c, self.__grid[grow][gcol], 0, 0)) 
                    self.__dirty[grow][gcol] = False

# TODO: figure out how to trigger a redraw event after all connections are made
class ScreenController:
    def onButtonDown(self, but, vel, row, col):
        #print("%s - %s, %s @ %s down" % (but, row, col, vel))
        return
    
    def onButtonUp(self, but, row, col):
        #print("%s - %s, %s up" % (but, row, col))
        return
    
    def onMonoAftertouch(self, pressure):
        #print("%s aftertouch" % (pressure))
        return
    
    def onPolyAftertouch(self, row, col, pressure):
        #print("%d, %d: %s aftertouch" % (col, row, pressure))
        return

# TODO: break ALSA away into a seperate module to standardize I/O (Jack on the way?)
def run(clientName, inPorts, outPorts, controller):
    curScreen = controller
    alsaseq.client(clientName, inPorts, outPorts, True)
    initd = False
    while True:
        if not alsaseq.inputpending():
            time.sleep(0.001)
            continue
        val = alsaseq.input()
        
        mtype = val[0]
        if mtype == _MIDI_CONNECT:
            __devi = val[7][0]
            __devo = val[7][2]
            initd = True
        elif not initd:
            continue
        elif mtype == _MIDI_CC:
            but = val[7][4]
            vel = val[7][5]
            r,c = __b2idx(but)
            if c == 9:
                but = PLAY
            if vel == 0:
                curScreen.onButtonUp(but, 9 - r, c)
            else:
                curScreen.onButtonDown(but, vel, 9 - r, c)
        elif mtype == _MIDI_ON:
            but = val[7][1]
            vel = val[7][2]
            r,c = __b2idx(but)
            if vel == 0:
                curScreen.onButtonUp(but, 9 - r, c)
            else:
                curScreen.onButtonDown(GRID, vel, 9 - r, c)
        elif mtype == _MIDI_OFF:
            but = val[7][1]
            vel = val[7][2]
            r,c = __b2idx(but)
            curScreen.onButtonUp(GRID, 9 - r, c)
        elif mtype == _MIDI_MAFTER:
            vel = val[7][5]
            curScreen.onMonoAftertouch(vel)
        elif mtype == _MIDI_PAFTER:
            but = val[7][1]
            vel = val[7][2]
            r,c = __b2idx(but)
            curScreen.onPolyAftertouch(9 - r, c, vel)
        #else:
        #    print val
