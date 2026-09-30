#!/usr/bin/env python3
"""Send one key transition to the isolated emulator X display via XTest."""
import ctypes as c
import ctypes.util
import sys

x11 = c.CDLL(ctypes.util.find_library('X11'))
xtest = c.CDLL(ctypes.util.find_library('Xtst'))
x11.XOpenDisplay.argtypes = [c.c_char_p]
x11.XOpenDisplay.restype = c.c_void_p
x11.XStringToKeysym.argtypes = [c.c_char_p]
x11.XStringToKeysym.restype = c.c_ulong
x11.XKeysymToKeycode.argtypes = [c.c_void_p, c.c_ulong]
x11.XKeysymToKeycode.restype = c.c_uint
x11.XFlush.argtypes = [c.c_void_p]
x11.XCloseDisplay.argtypes = [c.c_void_p]
xtest.XTestFakeKeyEvent.argtypes = [c.c_void_p, c.c_uint, c.c_int, c.c_ulong]
if len(sys.argv) != 3 or sys.argv[1] not in ('keydown', 'keyup'):
    raise SystemExit('usage: x11-input.py keydown|keyup KEY')
display = x11.XOpenDisplay(None)
if not display:
    raise SystemExit('Cannot open the test display')
try:
    keycode = x11.XKeysymToKeycode(display, x11.XStringToKeysym(sys.argv[2].encode()))
    if not keycode:
        raise SystemExit('Unknown X11 key')
    if not xtest.XTestFakeKeyEvent(display, keycode, sys.argv[1] == 'keydown', 0):
        raise SystemExit('XTest key event failed')
    x11.XFlush(display)
finally:
    x11.XCloseDisplay(display)
