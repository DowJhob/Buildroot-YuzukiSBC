# uncompyle6 version 3.4.0
# Python bytecode 2.7 (62211)
# Decompiled from: Python 2.7.15+ (default, Oct  7 2019, 17:39:04) 
# [GCC 7.4.0]
# Embedded file name: /home/user/zeus/daemon_thread.py
# Compiled at: 2016-07-04 16:26:08
import threading, time
from daemon import Daemon

class DaemonThread(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)
        self.online = True
        self.server = None
        self.timeout = 2.0
        self.thread_w = None
        self.rfid_id = ''
        return

    def get_path(self):
        return self.app_path

    def run(self):
        Daemon.log('Listening...')
        while self.online:
            try:
                Daemon.log('+In the Thread')
                time.sleep(1)
            except Exception as e:
                Daemon.log('Exception in daemon thread')
                Daemon.log(e)

    def exit(self):
        self.online = False
        self.join(5)
        if self.isAlive():
            Daemon.log("Can't stop daemon thread")
        else:
            Daemon.log('Daemon thread stopped')


class DaemonCircle:

    def __init__(self):
        self.online = True
        self.server = None
        self.timeout = 2.0
        self.thread_w = None
        self.rfid_id = ''
        return

    def get_path(self):
        return self.app_path

    def run(self):
        Daemon.log('Listening...')
        while self.online:
            try:
                Daemon.log('+In the Thread')
                time.sleep(1)
            except Exception as e:
                Daemon.log('Exception in daemon thread')
                Daemon.log(e)

        Daemon.log('Exit from circle')

    def exit(self):
        self.online = False