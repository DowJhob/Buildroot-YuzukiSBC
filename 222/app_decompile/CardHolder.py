# uncompyle6 version 3.4.0
# Python bytecode 2.7 (62211)
# Decompiled from: Python 2.7.15+ (default, Oct  7 2019, 17:39:04) 
# [GCC 7.4.0]
# Embedded file name: /home/user/zeus/CardHolder.py
# Compiled at: 2018-04-28 22:19:12
from lib import singleton
import time, threading, Queue
from DebugImport import debug_message
from include import cards_local
from multiprocessing import Queue as qe
from Models import QueueData

class CardHolderData(object):

    def __init__(self, data_type, code):
        self.type = data_type
        self.code = code


class CardHolder(threading.Thread):

    def __init__(self, readeq):
        threading.Thread.__init__(self)
        self.queue_display = readeq
        self.online = True

    def run(self):
        debug_message.print_message('------CardHolder run----------')
        while self.online:
            try:
                _data = self.queue_display.get(False)
            except Queue.Empty as queue_error:
                _data = None
            else:
                if isinstance(_data, QueueData):
                    debug_message.print_message('-----------RFID1356 receive data-------------')
                    debug_message.print_message('\t' + _data.command)
                    debug_message.print_message(_data.value)
                    if _data.command == 'rfid1356':
                        cards_local.add(rfid=_data.value['uid'], rf1356=True, pwdpack=_data.value['pwdpack'])
                    elif _data.command == 'barcode':
                        cards_local.add(barcode=_data.value)
                time.sleep(0.01)

        return

    def exit(self):
        if self.online:
            self.online = False
        self.join(10)
        debug_message.print_message('!------CardHolder exit----------')