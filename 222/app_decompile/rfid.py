# uncompyle6 version 3.4.0
# Python bytecode 2.7 (62211)
# Decompiled from: Python 2.7.15+ (default, Jul  9 2019, 16:51:35) 
# [GCC 7.4.0]
# Embedded file name: /home/user/zeus/rfid.py
# Compiled at: 2018-05-11 17:25:12
from M5e import M5e, M5ePoller
import logging, socket, threading
from include import cards_local
from DebugImport import debug_message
logger = logging.getLogger('zeus')

class RfidThread:

    def __init__(self, app_path, unix_socket='', power=1500):
        self.unix_socket = unix_socket
        self.port = None
        self.app_path = app_path
        self.client = None
        self.q = None
        self.recdict = {}
        self.online = True
        self.thread_w = None
        self.power = power
        return

    def get_data(self, data):
        ant, ids, rssi = data
        epc = ids.encode('hex').upper()
        debug_message.print_message('Rfid read data: ' + epc)
        if cards_local.is_rfid_866_active():
            try:
                if self.thread_w is None or not self.thread_w.is_alive():
                    self.thread_w = threading.Thread(target=cards_local.add(rfid=epc))
                    self.thread_w.start()
                else:
                    debug_message.print_message('RFID Card is busy')
            except Exception as e1:
                debug_message.print_message('Rfid get data exp')
                debug_message.print_message(e1)

        return

    def p1(self, M5e):
        M5e.ChangeAntennaPorts(1, 1)
        return 'Ant1'

    def start(self):
        self.run()

    def run(self):
        self.start_read()

    def is_online(self):
        if self.q is None:
            return False
        else:
            return self.q.is_online()

    def start_read(self):
        r = M5e(portSTR='/dev/ttySP1', readPwr=1200)
        self.q = M5ePoller(r, antfuncs=[self.p1], callbacks=[self.get_data])
        self.q.query_mode()

    def exit(self):
        if self.online:
            self.online = False
            try:
                self.q.stop()
            except Exception as e1:
                debug_message.print_message('==================Rfid exp1===================')
                debug_message.print_message(e1)
                debug_message.print_message('==================Rfid exp1===================')

        self.q.join(10)
        if self.q.isAlive():
            debug_message.print_message("Can't stop RFID")
        else:
            debug_message.print_message('RFID stopped')
# okay decompiling /home/a/Desktop/app/rfid.pyc
