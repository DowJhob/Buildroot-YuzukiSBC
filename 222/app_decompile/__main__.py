# uncompyle6 version 3.4.0
# Python bytecode 2.7 (62211)
# Decompiled from: Python 2.7.15+ (default, Jul  9 2019, 16:51:35) 
# [GCC 7.4.0]
# Embedded file name: /home/user/zeus/__main__.py
# Compiled at: 2018-06-13 14:43:04
from __future__ import print_function
from common import access_point
from config import DirectionTypes
from Barcode import Barcode
from rfid_nfc import RfidNfc
from Queue import Queue
import ConfigParser, os, rfid, socket, time
from daemon import Daemon
import signal, sys
from logging import getLogger, config
from DebugImport import debug_message
from CardHolder import CardHolder, CardHolderData
from HttpServer import ThreadedTCPServer
from multiprocessing import Process
from multiprocessing import Queue as qe
from Models import QueueData
app_path = os.path.dirname(os.path.abspath(__file__))
if os.path.isfile(app_path):
    app_path = os.path.dirname(app_path) + '/zeus'
print('app_path: ' + app_path)
print('Socket timeout: ' + str(socket.getdefaulttimeout()))
socket.setdefaulttimeout(60)
config.fileConfig(app_path + '/logging.conf')
logger = getLogger('zeus')

class Zeus:

    def __init__(self, app_path_zeus, logger_zeus):
        self.prev_device_state = None
        self.app_path = app_path_zeus
        self.logger = logger_zeus
        self.irc_r = None
        self.irc_b = None
        self.irc_http = None
        self.barcode_queue = qe()
        self.rfid_queue = qe()
        self.root_queue = qe()
        self.read_queue = qe()
        self.barcode_thread = None
        self.rfid_thread = None
        self.rfid_1356_queue = qe()
        self.rfid_1356_thread = None
        self.data_thread = None
        self.is_config = False
        self.config = None
        self.options = {'osdb_server': 'iis_pilot', 'sde_server': 'iis_sde', 'point_ip': '11.11.0.112', 'os_ip': '11.11.0.112', 
           'point_direction': DirectionTypes.ENTER, 'master_ip': '11.11.0.112', 'rfid_power': 1400, 
           'monitor_ip': '11.11.0.113', 'rfid866_enable': True, 'rfid1356_enable': True}
        self.reader_status = {'barcode': False, 'rfid1356': False}
        return

    def barcode_usb(self, _app_path, inputqe, outputqe, readeq):
        bc = Barcode(_app_path, inputqe, outputqe, readeq)
        bc.run()

    def init_barcode_usb(self):
        self.barcode_thread = Process(target=self.barcode_usb, args=(self.app_path, self.barcode_queue, self.root_queue, self.read_queue))
        self.barcode_thread.start()

    def init_data(self):
        self.data_thread = CardHolder(self.read_queue)
        self.data_thread.start()

    def init_rfid(self):
        if self.options['rfid866_enable']:
            self.rfid_thread = rfid.RfidThread(self.app_path, power=self.options['rfid_power'])
            self.rfid_thread.start()

    def rfid_1356_uart(self, _app_path, inputqe, outputqe, readeq):
        rf = RfidNfc(_app_path, inputqe, outputqe, readeq)
        rf.run()

    def init_rfid_1356(self):
        if self.options['rfid1356_enable']:
            self.rfid_1356_thread = Process(target=self.rfid_1356_uart, args=(self.app_path, self.rfid_1356_queue, self.root_queue, self.read_queue))
            self.rfid_1356_thread.start()
        else:
            self.reader_status['rfid1356'] = True

    def init_http(self):
        self.irc_http = ThreadedTCPServer()
        self.irc_http.start()

    def init_access_point(self):
        access_point.init_point(app_path, self.options, self.barcode_queue, self.rfid_1356_queue)

    def init_debug_message(self):
        debug_message.set_mode(env=self.options['env'])

    def run(self):
        print('--0')
        self.init_data()
        self.init_debug_message()
        self.init_access_point()
        print('--1')
        self.init_http()
        print('--2')
        self.init_barcode_usb()
        print('--3')
        self.init_rfid()
        print('--4')
        self.init_rfid_1356()

    def is_online(self):
        try:
            if not self.get_reader_state('reader_866') or access_point.is_online() is None or access_point.is_turnstile() is None:
                return False
            if access_point.get_global_lock():
                return
            current_state = self.reader_status['barcode'] and self.get_reader_state('reader_866') and access_point.is_online() and self.reader_status['rfid1356'] and access_point.is_turnstile()
            if self.prev_device_state is None or current_state != self.prev_device_state:
                self.prev_device_state = current_state
                return current_state
            return
        except Exception as e:
            print(e)
            return False

        return

    def get_reader_state(self, reader_name):
        if reader_name == 'reader_866':
            if not self.options['rfid866_enable']:
                return True
            if self.rfid_thread is None:
                return False
            return self.rfid_thread.is_online()
        else:
            if reader_name == 'reader_1356':
                return self.reader_status['rfid1356']
            if reader_name == 'reader_barcode':
                return self.reader_status['barcode']
            return

    def exit(self):
        try:
            self.irc_http.exit()
        except Exception as e:
            print(e)
        else:
            if self.options['rfid1356_enable']:
                try:
                    self.rfid_1356_queue.put(QueueData('exit', True))
                except Exception as e:
                    print(e)

            try:
                self.barcode_queue.put(QueueData('exit', True))
            except Exception as e:
                print(e)

        if self.options['rfid866_enable']:
            try:
                self.rfid_thread.exit()
            except Exception as e:
                print(e)

        self.data_thread.exit()
        access_point.exit()

    def get_queue(self):
        if not self.root_queue.empty():
            try:
                _data = self.root_queue.get(False)
            except Queue.Empty as queue_error:
                _data = None

            if isinstance(_data, QueueData):
                debug_message.print_message('-----------Read queue receive data-------------')
                debug_message.print_message('\t' + _data.command)
                debug_message.print_message(_data.value)
                if _data.command == 'rfid1356' and isinstance(_data.value, dict) and _data.value:
                    if 'status' in _data.value:
                        self.reader_status['rfid1356'] = _data.value['status']
                        debug_message.print_message('Set rfid1356 status to')
                        debug_message.print_message(_data.value['status'])
                elif _data.command == 'barcode' and isinstance(_data.value, dict) and _data.value:
                    if 'status' in _data.value:
                        debug_message.print_message('Set barcode status to')
                        debug_message.print_message(_data.value['status'])
                        self.reader_status['barcode'] = _data.value['status']
        return

    def read_config(self):
        self.config = ConfigParser.ConfigParser()
        self.config.read(self.app_path + '/zeus.ini')
        options = self.config.options('ZeusSection')
        config_options = [
         'osdb_server', 'sde_server', 'point_ip', 'point_direction', 'master_ip', 'env', 'display', 'rfid_power',
         'os_ip', 'monitor_ip', 'rfid866_enable', 'rfid1356_enable']
        for option in options:
            if option == 'enter_level':
                self.options[option] = self.config.getint('ZeusSection', option)
            elif option == 'display':
                self.options[option] = self.config.getint('ZeusSection', option)
            elif option == 'rfid_power':
                self.options[option] = self.config.getint('ZeusSection', option)
            elif option == 'rfid866_enable':
                self.options[option] = self.config.getboolean('ZeusSection', option)
            elif option == 'rfid1356_enable':
                self.options[option] = self.config.getboolean('ZeusSection', option)
            elif option == 'point_direction':
                _op = self.config.getint('ZeusSection', option)
                self.options[option] = DirectionTypes.ENTER
                if _op == 1:
                    self.options[option] = DirectionTypes.EXIT
            else:
                self.options[option] = self.config.get('ZeusSection', option)

        self.is_config = True
        for candidate in config_options:
            if candidate not in self.options:
                self.is_config = False

        print('=======================================')
        print('Zeus params: ' + self.options['osdb_server'] + ' : ' + self.options['sde_server'] + ' : ' + self.options['point_ip'] + ' : ' + str(self.options['point_direction']) + ' : ' + self.options['master_ip'] + ' : ' + self.options['env'] + ' : ' + str(self.options['display']) + ' : ' + str(self.options['rfid_power']) + ' : ' + self.options['os_ip'] + ':' + self.options['monitor_ip'])
        print('=======================================')


class MyDaemon(Daemon):

    def __init__(self, my_app_path, stdin='/dev/null', stdout='/dev/null', stderr='/dev/null'):
        self.thread = Zeus(app_path, logger)
        self.thread.read_config()
        if self.thread.options['env'] == 'development':
            stdout = '/tmp/zeus.log'
        super(MyDaemon, self).__init__(my_app_path, stdin=stdin, stdout=stdout, stderr=stderr)
        self.online = True

    def exit(self):
        print('Zeus exit init')
        self.online = False
        self.thread.exit()
        return 1

    def run(self):
        self.thread.run()
        self.log('Zeus started')
        print('My global pid is: ' + str(self.pid))
        access_point.set_pid(self.pid)
        access_point_tick_var = 0
        min_tick = 0
        list_update_tick_var = 301
        device_tick_var = 11
        first_start = True
        first_init_mb = True
        access_point.get_system_usage()
        while self.online:
            if access_point.is_updating():
                time.sleep(0.05)
                continue
            if min_tick > 1:
                min_tick = 0
                access_point.check_debug_message()
            if access_point_tick_var > 5:
                access_point.check_state()
                access_point.attention_in_offline_mode()
                access_point_tick_var = 0
            if device_tick_var > 10:
                if not first_start:
                    if first_init_mb and access_point.is_turnstile_monitor():
                        first_init_mb = False
                        access_point.set_direction()
                    access_point.get_params_thread()
                    if list_update_tick_var > 300 or access_point.get_is_new_match():
                        access_point.set_is_new_match(False)
                        list_update_tick_var = 0
                        access_point.show_addition_layer()
                        access_point.get_lists()
                        access_point.get_system_usage()
                access_point.get_state()
                cur_state = self.thread.is_online()
                if cur_state is not None:
                    if cur_state:
                        first_start = False
                        access_point.reset_display()
                    else:
                        access_point.show_red()
                        access_point.show_wait()
                device_tick_var = 0
                self.thread.get_queue()
                access_point.check_master_point()
                access_point.check_slave_point()
                access_point.check_monitor()
                access_point.set_reader_866_state(self.thread.get_reader_state('reader_866'))
                access_point.set_reader_1356_state(self.thread.get_reader_state('reader_1356'))
                access_point.set_reader_barcode_state(self.thread.get_reader_state('reader_barcode'))
                access_point.check_update()
            time.sleep(0.1)
            access_point_tick_var += 0.1
            device_tick_var += 0.1
            list_update_tick_var += 0.1
            min_tick += 0.1

        print('Exit')
        return


if __name__ == '__main__':
    logger.warning('path: ' + app_path)
    daemon = MyDaemon('/tmp/zeus.pid', stderr='/tmp/zeus-error.log')
    if len(sys.argv) == 2:
        if sys.argv[1] == 'start':
            daemon.start()
        elif sys.argv[1] == 'run':
            daemon.start(os_start=True)
        elif sys.argv[1] == 'stop':
            daemon.stop()
        elif sys.argv[1] == 'restart':
            daemon.restart()
        elif sys.argv[1] == 'manual':
            try:
                daemon.run()
            except (KeyboardInterrupt, SystemExit):
                daemon.exit()

        else:
            print('Unknown command')
            sys.exit(2)
        sys.exit(0)
    else:
        print('usage: %s start|stop|restart|manual|run' % sys.argv[0])
        sys.exit(2)
# okay decompiling /home/a/Desktop/app/__main__.pyc
