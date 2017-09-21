from pycom import rgbled, heartbeat
RED = 0xFF0000
GREEN = 0x00FF00
BLUE = 0x0000FF

class RgbWrapper(object):
    def __init__(self):
        heartbeat(False)    #Turn off the pulsing of the LED to gain control of it
        self.output = 0x000000

    def _set(self):
        #print(hex(self.output))
        rgbled(self.output)

    def red_on(self):
        self.output = (self.output & (GREEN | BLUE)) | RED
        self._set()
    
    def red_off(self):
        self.output = self.output & (GREEN | BLUE)
        self._set()

    def green_on(self):
        self.output = (self.output & (RED | BLUE)) | GREEN
        self._set()

    def green_off(self):
        self.output = self.output & (RED | BLUE)
        self._set()

    def blue_on(self):
        self.output = (self.output & (RED | GREEN)) | BLUE
        self._set()

    def blue_off(self):
        self.output = self.output & (RED | GREEN)
        self._set()

    def red(self, value):
        value = int(value) & 0xFF
        self.output = (int(self.output) & 0x00FFFF) | (value << 16)
        self._set()

    def green(self, value):
        value = value & 0xFF
        self.output = (int(self.output) & 0xFF00FF) | (value << 8)
        self._set()

    def blue(self, value):
        value = int(value) & 0xFF
        self.output = (int(self.output) & 0xFFFF00) | (value)
        self._set()

