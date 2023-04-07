from xbee import XBee
import serial

core_serial = None
xbee_serial = None
xbee = None

def init_core(port: str, baud: int):
    global core_serial
    core_serial = serial.Serial(port, baudrate=baud)


def init_xbee(port: str, baud: int, callback=None):
    global xbee_serial, xbee
    xbee_serial = serial.Serial(port, baudrate=baud)
    xbee = XBee(xbee_serial, escaped=True, callback=callback)
