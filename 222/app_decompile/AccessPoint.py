# uncompyle6 version 3.4.0
# Python bytecode 2.7 (62211)
# Decompiled from: Python 2.7.15+ (default, Jul  9 2019, 16:51:35) 
# [GCC 7.4.0]
# Embedded file name: /home/user/zeus/AccessPoint.py
# Compiled at: 2019-02-27 18:08:48
from lib import singleton, requests
from config import DirectionTypes, CardTypes, AccessPointTypes, PassTypes, StatusTypes, EventTypes
import ConfigParser, json, datetime
from ManagmentBoard import ManagmentBoardDaemon
import Display, threading, time, copy
from urllib import urlencode
from config import add_lock, waiting_lock, cards_lock, common_lock, archive_lock
import logging, os
from ssh_wrapper import SshWrapper
from multiprocessing import Process, Lock, Queue
import subprocess, sys
from DebugImport import debug_message
from binascii import hexlify
from Models import QueueData
ssh_wrapper = SshWrapper()
logger = logging.getLogger(__name__)
http_lock = threading.Lock()
http_params_lock = threading.Lock()
get_list_lock = Lock()

@singleton
class AccessPoint:

    def __init__(self):
        self.server = ''
        self.ip = ''
        self.slave_ip = ''
        self.point_id = 0
        self.venue_enter_id = 0
        self.venue_enter_name = ''
        self.venue_exit_id = 0
        self.venue_exit_name = ''
        self.type_id = AccessPointTypes.SP
        self.point_code = ''
        self.name = ''
        self.card_wait_time = 10
        self.pass_wait_time = 10
        self.show_wait_time = 3
        self.direction = DirectionTypes.ENTEREXIT
        self.point_direction = DirectionTypes.ENTER
        self.direction_prev = self.direction
        self.mode = 0
        self.power_rfid_enter = 2000
        self.power_rfid_exit = 2000
        self.barcode_length_128 = 13
        self.barcode_length_2of5 = 24
        self.check_tid = True
        self.check_pass = True
        self.rfid_ticket = True
        self.online = False
        self.app_path = ''
        self.display = None
        self.mb = None
        self.socket_timeout = 3.0
        self.card_socket_timeout = 4.0
        self.num_requests = 1
        self.latest_init = ''
        self.latest_params = ''
        self.point_mode = ''
        self.latest_time_index = 0
        self.archive = {}
        self.master_ip = ''
        self.os_ip = ''
        self.online_tick = 0
        self.online_tick_max = 1
        self.params_prev = {}
        self.slave_update_params = False
        self.env = 'production'
        self.third_step = False
        self.test_mode = False
        self.version = '6.08K'
        self.card_local_time = 0
        self.slave_local_time = 0
        self.is_slave_conn = None
        self.is_slave_ping = False
        self.is_monitor = None
        self.monitor_local_time = 0
        self.is_reader_866 = False
        self.reader_866_reconnects = 0
        self.is_reader_1356 = False
        self.reader_1356_reconnects = 0
        self.is_reader_barcode = False
        self.reader_barcode_reconnects = 0
        self.cur_open_sensor = False
        self.monitor_ip = ''
        self.options = {}
        self.attention_mode = True
        self.monitor_check_idx = 0
        self.pid = 0
        self.thread_mb_init = None
        self.updating = False
        self.in_group = False
        self.archive_thread = None
        self.params_thread = None
        self.match_keys_thread = None
        self.startup_time = '----'
        self.is_new_match = False
        self.barcodeqe = None
        self.rfid1356qe = None
        self.memory_usage = 0
        self.cpu_usage = 0
        self.set_params_status = False
        return

    def init_point(self, app_path, _options, barcodeqe, rfid1356qe):
        self.point_direction = DirectionTypes.ENTER
        self.point_mode = 'production'
        self.master_ip = '11.11.0.112'
        self.env = 'production'
        display_rotate = 90
        self.os_ip = '11.11.0.112'
        self.monitor_ip = '11.11.0.113'
        self.barcodeqe = barcodeqe
        self.rfid1356qe = rfid1356qe
        if 'osdb_server' in _options:
            self.server = _options['osdb_server']
        if 'point_direction' in _options:
            self.point_direction = _options['point_direction']
        if 'point_mode' in _options:
            self.point_mode = _options['point_mode']
        if 'master_ip' in _options:
            self.master_ip = _options['master_ip']
        if 'point_ip' in _options:
            self.ip = _options['point_ip']
        if 'display' in _options:
            display_rotate = _options['display']
        if 'os_ip' in _options:
            self.os_ip = _options['os_ip']
        if 'monitor_ip' in _options:
            self.monitor_ip = _options['monitor_ip']
        if 'env' in _options:
            self.env = _options['env']
        if 'rfid866_enable' in _options:
            self.set_option('rfid866_enable', _options['rfid866_enable'])
        if 'rfid1356_enable' in _options:
            self.set_option('rfid1356_enable', _options['rfid1356_enable'])
        if app_path is not None:
            self.app_path = app_path
        self.read_db_config()
        self.set_startup_time()
        if self.point_mode != 'test':
            self.get_id()
            self.display = Display.Display('/mnt/ramdisk', display_rotate)
            self.display.start()
            self.show_wait()
            debug_message.print_message('--------MB START------------')
            self.init_mb()
            debug_message.print_message('--------!MB START-----------')
            if self.is_master():
                debug_message.print_message('--------Monitor init------------')
                ssh_wrapper.set_host(self.monitor_ip)
                debug_message.print_message('--------!Monitor init-----------')
        return

    def get_lock(self):
        return add_lock.locked() or waiting_lock.locked() or cards_lock.locked()

    def get_global_lock(self):
        return self.get_lock() or http_lock.locked()

    def get_id(self):
        try:
            params = {'IP': self.ip}
            self.latest_init = requests(urls=self.get_server() + '/AccessPointInit/', params=params, timeouts=self.socket_timeout)
            if self.latest_init is not None:
                data = json.loads(self.latest_init)
                if data is not None and 'PointID' in data:
                    debug_message.print_message(data)
                    self.point_id = data['PointID']
                    self.venue_enter_id = data['VenueEnterID']
                    self.venue_enter_name = data['VenueEnterName']
                    self.venue_exit_id = data['VenueExitID']
                    self.venue_exit_name = data['VenueExitName']
                    if 'ServerTime' in data:
                        self.set_sys_time(data['ServerTime'])
                    if 'Name' in data:
                        self.name = data['Name']
                    if 'Code' in data:
                        self.point_code = data['Code']
                    if data['TypeID'] == 2:
                        self.type_id = AccessPointTypes.SP
                    elif data['TypeID'] == 3:
                        self.type_id = AccessPointTypes.AT
                    else:
                        self.type_id = AccessPointTypes.P
                    if not self.online:
                        self.online_tick = 0
                        self.latest_time_index = time.time()
                        self.online = True
                    self.show_addition_message()
                else:
                    self.set_offline()
                    debug_message.print_message('Get ID incorrect data')
                    debug_message.print_message(self.latest_init)
            else:
                self.set_offline()
        except Exception as e:
            self.set_offline()
            debug_message.print_message('-------------Get point by ID-----------------')
            debug_message.print_message(e)
            debug_message.print_message('-------------!Get point by ID----------------')

        return

    def init_mb(self):
        self.mb = ManagmentBoardDaemon(self.app_path, self.point_direction, self.is_master())
        self.mb.start()

    def exit(self):
        if self.display is not None:
            self.display.exit()
        if self.mb is not None:
            self.mb.close_port()
        return

    def set_test_mode(self):
        self.show_wait()
        time.sleep(5)
        self.reset_display()
        self.test_mode = True

    def set_test_mode_off(self):
        self.test_mode = False

    def is_test_mode(self):
        return self.test_mode

    def enter_mb(self):
        if self.is_master():
            _ths = False
            if cards_lock.locked():
                if self.mb is not None:
                    self.mb.write_data('RED')
                self.show_stop()
            if self.is_test_mode() and self.third_step:
                debug_message.print_message('-In test mode alert step')
                self.third_step = False
                _ths = True
                self.mb.write_data('GREEN')
                self.show_go(prefix=self.get_go_prefix())
                self.free_mb()
                time.sleep(10)
                self.normal_mb()
            else:
                debug_message.print_message('-In normal mode enter step')
                self.mb.enter_mode()
            if cards_lock.locked():
                if self.is_active():
                    self.show_passport()
                else:
                    self.set_light()
            if self.is_test_mode() and not _ths:
                debug_message.print_message('-In test mode set to exit direction')
                self.point_direction = DirectionTypes.EXIT
            if self.third_step:
                debug_message.print_message('-set third step to false')
                self.third_step = False
        else:
            self.slave_enter_mode()
        return

    def exit_mb(self):
        if self.is_master():
            if cards_lock.locked():
                if self.mb is not None:
                    self.mb.write_data('RED')
                self.show_stop()
            debug_message.print_message('-In normal mode exit step')
            if self.mb is not None:
                self.mb.exit_mode()
            if cards_lock.locked():
                if self.is_active():
                    self.show_passport()
                else:
                    self.set_light()
            if self.is_test_mode():
                debug_message.print_message('-In test mode set to enter direction')
                self.point_direction = DirectionTypes.ENTER
                self.third_step = True
        else:
            self.slave_exit_mode()
        return

    def start_warming(self):
        self.mb.start_warming()

    def stop_warming(self):
        self.mb.stop_warming()

    def normal_mb(self):
        self.mb.normal_mode()

    def set_rfid_clear(self):
        self.mb.rfid_1356 = ''

    def free_mb(self):
        if self.mb is not None:
            self.mb.free_mode()
        return

    def is_ready_mb(self):
        if self.mb is None:
            return False
        else:
            return self.mb.ready

    def is_passed_mb(self):
        if self.mb is None:
            return False
        else:
            return self.mb.passed_local

    def set_passed(self):
        if self.mb is None:
            return
        else:
            self.mb.passed_local = False
            return

    def set_slave_passed(self, value):
        if self.mb is None:
            return
        else:
            self.mb.passed = value
            return

    def show_passport(self):
        if self.type_id == AccessPointTypes.SP and not self.check_pass:
            self.show_ticket()
        elif self.display is not None:
            self.display.show_passport()
        self.show_tl()
        return

    def show_addition(self):
        if self.display is not None:
            self.display.show_addition()
        return

    def show_ticket(self):
        if self.display is not None:
            self.display.show_ticket()
        return

    def show_addition_ticket(self):
        if self.display is not None:
            self.display.show_addition_ticket()
        return

    def show_go(self, prefix=''):
        if self.display is not None:
            self.display.show_go(prefix=prefix)
        return

    def show_stop(self, prefix=''):
        if self.mb is not None:
            self.mb.write_data('RED')
        if self.display is not None:
            self.display.show_stop(prefix=prefix)
        return

    def show_tl(self):
        if self.mb is not None:
            self.mb.write_data('TL_OFF')
        return

    def get_online(self):
        return self.online

    def set_online(self, _val):
        self.online = _val

    def show_red(self):
        if self.mb is not None:
            self.mb.write_data('RED')
        return

    def show_green(self):
        if self.mb is not None:
            self.mb.write_data('GREEN')
        return

    def show_wait(self):
        if self.display is not None:
            self.display.show_wait()
        return

    def check_state(self):
        self.mb_state_init()
        self.send_archive_thread()
        if self.is_master() and cards_lock.locked():
            debug_message.print_message('------------Cards is locked by slave-------------------')
            if self.card_local_time > 0 and time.time() - self.card_local_time > 12:
                try:
                    if cards_lock.locked():
                        cards_lock.release()
                except Exception as e:
                    debug_message.print_message('-------------Cards lock release error---------')
                    debug_message.print_message(e)
                    debug_message.print_message('-------------Cards lock release error---------')

                self.reset_display()
                self.stop_card_lock_time()

    def is_development(self):
        return self.env == 'development'

    def is_production(self):
        return not self.is_development()

    def get_state(self):
        if self.get_lock():
            return
        else:
            if self.mb is not None:
                self.mb.exec_command('STATE')
            return

    def start_read_barcode(self):
        self.mb.start_read_barcode()

    def stop_read_barcode(self):
        self.mb.stop_read_barcode()

    def get_params_thread(self):
        if self.params_thread is None or not self.params_thread.is_alive():
            self.params_thread = threading.Thread(target=self.get_params)
            self.params_thread.start()
        return

    def get_params(self):
        if self.is_turnstile_monitor() is None or not self.is_turnstile_monitor():
            return
        check_pass_changed = False
        if self.get_lock() or http_lock.locked():
            return
        if not http_params_lock.acquire(False):
            debug_message.print_message('--------Params thread is locked-------------')
        else:
            try:
                if self.point_id > 0:
                    self.latest_params = self._get_params()
                    if self.latest_params is not None:
                        data = json.loads(self.latest_params)
                        if data is not None and 'TypeID' in data:
                            if not self.compare_params(data):
                                debug_message.print_message('---------Params not equals----------------')
                                debug_message.print_message(data)
                                debug_message.print_message('---------!Params not equals---------------')
                                if self.check_pass != data['CheckPass']:
                                    check_pass_changed = True
                                if self.type_id.value != int(data['TypeID']):
                                    check_pass_changed = True
                                self.set_params(data)
                                self.show_addition_message()
                            if not self.online:
                                self.online_tick = 0
                                self.online = True
                                self.latest_time_index = time.time()
                        else:
                            debug_message.print_message('============Get access point params from OSDB 1===========')
                            debug_message.print_message('Incorrect data')
                            debug_message.print_message(self.latest_params)
                            self.set_offline()
                            debug_message.print_message('============!Get access point params from OSDB 1==========')
                    else:
                        debug_message.print_message('\t-----------Set OFFLINE MODE---------------')
                        self.set_offline()
                else:
                    self.get_id()
            except Exception as e:
                debug_message.print_message('=================Get access point params from OSDB 2===================')
                self.set_offline()
                debug_message.print_message(e)
                debug_message.print_message('=================!Get access point params from OSDB 2==================')

            if check_pass_changed and self.is_active():
                while self.get_lock() or http_lock.locked():
                    pass

                __is_self_lock = False
                if not common_lock.acquire(False):
                    pass
                else:
                    __is_self_lock = True
                self.show_passport()
                if __is_self_lock:
                    common_lock.release()
            if self.direction != self.direction_prev:
                while self.get_lock() or http_lock.locked():
                    pass

                __is_self_lock = False
                if not common_lock.acquire(False):
                    pass
                else:
                    __is_self_lock = True
                self.set_direction()
                if __is_self_lock:
                    common_lock.release()
            http_params_lock.release()
        return

    def _get_params(self, param_num_request=0):
        while self.get_lock() or http_lock.locked():
            pass

        params = {'PointID': self.point_id}
        _timeout = param_num_request + 1
        if param_num_request > 0:
            time.sleep(_timeout)
        _request = requests(urls=self.get_server() + '/AccessPointParams/', params=params, timeouts=self.socket_timeout)
        if _request is None:
            if param_num_request < 3:
                debug_message.print_message('\t--------Request params again ' + str(param_num_request) + '------------')
                param_num_request += 1
                _request = self._get_params(param_num_request)
        return _request

    def set_offline(self):
        if self.online:
            self.online = False
            self.latest_time_index = time.time()

    def set_params(self, data):
        _is_error = False
        try:
            try:
                self.card_wait_time = int(data['CardWaitTime'])
                self.pass_wait_time = int(data['PassWaitTime'])
                self.show_wait_time = int(data['ShowWaitTime'])
                if self.mb is not None:
                    self.mb.set_option('time_tick', self.pass_wait_time)
            except Exception as e:
                _is_error = True
                debug_message.print_message(e)
                debug_message.print_message('Params Times is incorrect')
            else:
                try:
                    if int(data['Direction']) == 0:
                        self.direction = DirectionTypes.ENTER
                    elif int(data['Direction']) == 1:
                        self.direction = DirectionTypes.EXIT
                    elif int(data['Direction']) == 2:
                        self.direction = DirectionTypes.ENTEREXIT
                    elif int(data['Direction']) == 3:
                        self.direction = DirectionTypes.BLOCKED
                    elif int(data['Direction']) == 4:
                        self.direction = DirectionTypes.UNBLOCKED
                except Exception as e:
                    _is_error = True
                    debug_message.print_message(e)
                    debug_message.print_message('Param Direction is incorrect')

                self.mode = data['Mode']
                try:
                    if int(data['TypeID']) == 2:
                        self.type_id = AccessPointTypes.SP
                    elif int(data['TypeID']) == 3:
                        self.type_id = AccessPointTypes.AT
                    else:
                        self.type_id = AccessPointTypes.P
                except Exception as e:
                    _is_error = True
                    debug_message.print_message(e)
                    debug_message.print_message('Param TypeID is incorrect')

            self.power_rfid_enter = data['PowerRfidEnter']
            self.power_rfid_exit = data['PowerRfidExit']
            if 'Length128' in data:
                self.barcode_length_128 = data['Length128']
                self.set_option('barcode_length_128', data['Length128'])
            if 'Length2of5' in data:
                self.barcode_length_2of5 = data['Length2of5']
                self.set_option('barcode_length_2of5', data['Length2of5'])
            self.check_tid = data['CheckTid']
            self.check_pass = data['CheckPass']
            if 'RfidTicket' in data:
                self.rfid_ticket = data['RfidTicket']
            if 'AttentionMode' in data:
                self.attention_mode = data['AttentionMode']
            if 'RfidReader1356' in data:
                self.set_option('rfid_1356_reader', data['RfidReader1356'])
            if 'RfidReader866' in data:
                self.set_option('rfid_866_reader', data['RfidReader866'])
            if 'BarcodeReader' in data:
                self.set_option('barcode_reader', data['BarcodeReader'])
            if 'Groups' in data:
                if data['Groups'] is not None:
                    self.set_option('groups', data['Groups'])
                else:
                    self.set_option('groups', '')
            if 'MatchN' in data:
                if data['MatchN'] is not None:
                    _new_match_id = int(data['MatchN'])
                    if _new_match_id != self.get_current_match_id():
                        self.set_option('match_n', _new_match_id)
                        self.set_is_new_match(True)
                else:
                    self.set_option('match_n', 0)
            if 'FfMode' in data:
                self.set_option('ff_mode', data['FfMode'])
            if 'NfcEnable' in data:
                self.set_option('nfc_enable', data['NfcEnable'])
            if 'FfDate' in data:
                self.set_option('ff_date', data['FfDate'])
            self.save_options_database()
        except Exception as e:
            _is_error = True
            debug_message.print_message('=========SET PARAMS ERROR===========')
            debug_message.print_message(e)
            debug_message.print_message('=========!SET PARAMS ERROR==========')

        if _is_error:
            self.set_params_status = False
        else:
            self.set_params_status = True
        return

    def get_param_status(self):
        return self.set_params_status

    def check_card(self, direction, card_type='', code='', _rf1356=False, _pwdpack=False):
        if self.mb is not None:
            self.mb.write_data('STATE')
        card = None
        if not self.online:
            debug_message.print_message('===================Get card offline======================')
            _pass_type = PassTypes.IC
            _let_go = StatusTypes.ALLOW
            _flag = 1
            _message = u'\u041f\u0440\u043e\u0445\u043e\u0434 \u0440\u0430\u0437\u0440\u0435\u0448\u0435\u043d'
            if card_type == CardTypes.BARCODE:
                _pass_type = PassTypes.TC
                _ret = self.check_offline_access(code, _pwdpack)
                if not _ret:
                    _let_go = StatusTypes.DECLINED
                    _flag = EventTypes.REE.value
                    _message = u'\u041f\u0440\u043e\u0445\u043e\u0434 \u0437\u0430\u043f\u0440\u0435\u0449\u0435\u043d'
                    if self.in_group:
                        self.in_group = False
                        _flag = EventTypes.NRC.value
                        _message = u'\u0414\u0430\u043d\u043d\u044b\u0439 \u0442\u0438\u043f \u043a\u0430\u0440\u0442 \u043e\u0442\u043a\u043b\u044e\u0447\u0435\u043d'
                    if not _pwdpack:
                        _flag = EventTypes.WRFID.value
            if card_type == CardTypes.RFID and self.type_id == AccessPointTypes.SP and self.is_barcode_active():
                _let_go = StatusTypes.NOACCESS
                _flag = 0
                _message = u'\u041e\u0442\u0441\u0443\u0442\u0441\u0442\u0432\u0443\u044e\u0442 \u043f\u0440\u0430\u0432\u0430'
            card = {'PassID': 0, 'Message': _message, 'LetGo': _let_go, 'Flag': _flag, 'PassType': _pass_type, 'NameOnPass': None, 'Photo': None, 'IsLocal': True}
            debug_message.print_message('===================Get card offline======================')
            self.beep()
            return card
        else:
            if _rf1356:
                _ret = self.in_mastercards(code)
                if _ret:
                    _pass_type = PassTypes.TC
                    _let_go = StatusTypes.ALLOW
                    _flag = 1
                    _message = u'\u041f\u0440\u043e\u0445\u043e\u0434 \u0440\u0430\u0437\u0440\u0435\u0448\u0435\u043d'
                    card = {'PassID': 0, 'Message': _message, 'LetGo': _let_go, 'Flag': _flag, 'PassType': _pass_type, 'NameOnPass': None, 
                       'Photo': None, 'IsLocal': True}
                    self.beep()
                    return card
                if self.get_option('ff_mode', False) and not _pwdpack:
                    _pass_type = PassTypes.TC
                    _let_go = StatusTypes.DECLINED
                    _message = u'\u041f\u0440\u043e\u0445\u043e\u0434 \u0437\u0430\u043f\u0440\u0435\u0449\u0435\u043d'
                    _flag = EventTypes.WRFID.value
                    card = {'PassID': 0, 'Message': _message, 'LetGo': _let_go, 'Flag': _flag, 'PassType': _pass_type, 'NameOnPass': None, 
                       'Photo': None, 'IsLocal': True}
                    self.beep()
                    return card
            with http_lock:
                debug_message.print_message('===================Get card from OSDB======================')
                try:
                    venue_id = self.venue_enter_id
                    if direction == DirectionTypes.EXIT:
                        venue_id = self.venue_exit_id
                    params = {'VenueID': venue_id, 'PointID': self.point_id, 'Rfid': '', 'Barcode': ''}
                    if self.get_option('ff_mode', False) and _rf1356:
                        params['Rfid'] = code
                    elif card_type == CardTypes.RFID or _rf1356:
                        params['Rfid'] = code
                    else:
                        params['Barcode'] = code
                    debug_message.print_message('Card code ' + code)
                    card = self.get_card(params)
                    self.beep()
                except Exception as e:
                    debug_message.print_message(e)

                debug_message.print_message('===================!Get card from OSDB=====================')
            return card

    def beep(self):
        if self.mb is not None:
            self.mb.beep()
        return

    def get_card(self, params, num_request=0):
        card = None
        _data = requests(urls=self.get_server() + '/CheckCard/', params=params, timeouts=self.card_socket_timeout)
        if _data is not None:
            data = json.loads(_data)
            if data is not None and 'PassType' in data:
                debug_message.print_message('Pass id: ' + str(data['PassID']) + ' Message: ' + data['Message'].encode('utf-8') + ' letgo: ' + str(data['LetGo']) + ' Flag: ' + str(data['Flag']))
                card = data
            else:
                debug_message.print_message('Get Card Incorrect data')
                debug_message.print_message(_data)
        if card is None and num_request < self.num_requests:
            next_request = num_request + 1
            card = self.get_card(params, next_request)
        return card

    def write_log(self, direction, entry_type, card1, card2, proxy=False):
        ret = False
        debug_message.print_message('===================WriteLog to OSDB======================')
        if self.mb is not None:
            self.mb.write_data('STATE')
        if not self.online:
            debug_message.print_message('\t\t-----offline mode--------')
            self.write_log_offline(direction, entry_type, card1, card2)
            ret = True
        else:
            try:
                venue_enter_id = self.venue_enter_id
                venue_exit_id = self.venue_exit_id
                if direction == DirectionTypes.EXIT:
                    venue_enter_id = self.venue_exit_id
                    venue_exit_id = self.venue_enter_id
                params = {'VenueEnterID': venue_enter_id, 'VenueExitID': venue_exit_id, 'PointID': self.point_id, 'EntryType': entry_type, 'PassID1': card1.pass_id}
                if card2 is not None:
                    params['PassID2'] = card2.pass_id
                data = requests(urls=self.get_server() + '/WriteLog/', params=params, timeouts=self.socket_timeout)
                if proxy:
                    return data
                if data is not None:
                    debug_message.print_message('from server:' + data)
                    ret = True
                else:
                    debug_message.print_message('\t\t-----offline mode--------')
                    self.write_log_offline(direction, entry_type, card1, card2)
                    ret = True
            except Exception as e:
                debug_message.print_message(e)

        debug_message.print_message('===================!WriteLog to OSDB=====================')
        return ret

    def write_log_offline(self, direction, entry_type, card1, card2, proxy=False, to_archive=False):
        ret = False
        debug_message.print_message('===================WriteLogOffline to OSDB======================')
        if self.mb is not None:
            self.mb.write_data('STATE')
        if not self.online or to_archive:
            debug_message.print_message('\t\t-----offline mode--------')
            d = datetime.datetime.fromtimestamp(card1.time)
            date1 = d.date().isoformat()
            time1 = d.time().strftime('%H:%M:%S')
            params = {'EntryType': entry_type, 'LogDate': date1, 'LogTime': time1}
            _code_1 = card1.code
            _code_2 = ''
            if card1.card_type == CardTypes.RFID:
                params['Rfid1'] = card1.code
            else:
                params['Barcode1'] = card1.code
            if card2 is not None:
                if card2.card_type == CardTypes.RFID:
                    params['Rfid2'] = card2.code
                else:
                    params['Barcode2'] = card2.code
                _code_2 = card2.code
            _off_url = urlencode(params)
            with archive_lock:
                self.archive[str(time.mktime(d.now().timetuple()))] = {'url': _off_url, 'direction': direction, 'code_1': _code_1, 'code_2': _code_2, 'enter': entry_type}
            ret = True
        else:
            try:
                venue_enter_id = self.venue_enter_id
                venue_exit_id = self.venue_exit_id
                if direction == DirectionTypes.EXIT:
                    venue_enter_id = self.venue_exit_id
                    venue_exit_id = self.venue_enter_id
                d = datetime.datetime.fromtimestamp(card1.time)
                date1 = d.date().isoformat()
                time1 = d.time().strftime('%H:%M:%S')
                params = {'VenueEnterID': venue_enter_id, 'VenueExitID': venue_exit_id, 'PointID': self.point_id, 'EntryType': entry_type, 
                   'LogDate': date1, 'LogTime': time1}
                if card1.card_type == CardTypes.RFID:
                    params['Rfid1'] = card1.code
                else:
                    params['Barcode1'] = card1.code
                if card2 is not None:
                    if card2.card_type == CardTypes.RFID:
                        params['Rfid2'] = card2.code
                    else:
                        params['Barcode2'] = card2.code
                data = requests(urls=self.get_server() + '/WriteOfflineLog/', params=params, timeouts=self.socket_timeout)
                if proxy:
                    return data
                if data is not None:
                    debug_message.print_message(data)
                    ret = True
                else:
                    self.write_log_offline(direction, entry_type, card1, card2, False, True)
            except Exception as e:
                debug_message.print_message(e)

        debug_message.print_message('===================!WriteLogOffline to OSDB=====================')
        return ret

    def write_log_archive(self, rec_id, url_obj):
        debug_message.print_message('===================Write archive to OSDB======================')
        if self.online and not archive_lock.locked():
            _url = url_obj['url']
            direction = url_obj['direction']
            debug_message.print_message(_url)
            debug_message.print_message(str(direction))
            venue_enter_id = self.venue_enter_id
            venue_exit_id = self.venue_exit_id
            if direction == DirectionTypes.EXIT:
                venue_enter_id = self.venue_exit_id
                venue_exit_id = self.venue_enter_id
            params = {'VenueEnterID': venue_enter_id, 'VenueExitID': venue_exit_id, 'PointID': self.point_id}
            _url += '&' + urlencode(params)
            data = requests(urls=self.get_server() + '/WriteOfflineLog/?' + _url, timeouts=self.socket_timeout)
            if data is not None:
                del self.archive[rec_id]
        debug_message.print_message('===================!Write archive to OSDB=====================')
        return True

    def proxy(self, url, timeouts=1):
        data = ''
        with http_lock:
            debug_message.print_message('===================Get proxy from Slave======================')
            debug_message.print_message(self.get_server() + url)
            data = requests(urls=self.get_server() + url, timeouts=timeouts)
            if data is None:
                data = ''
            debug_message.print_message('===================!Get proxy from Slave=====================')
        return data

    def slave_enter_mode(self):
        data = None
        with http_lock:
            debug_message.print_message('===================Get open MB to Master======================')
            debug_message.print_message(time.time())
            if self.point_direction == DirectionTypes.ENTER:
                self.mb.exec_command('GREEN')
            data = requests(urls=self.get_master_server() + '/OpenMb/', timeouts=13)
            debug_message.print_message(data)
            try:
                if data is not None:
                    data = json.loads(data)
                    if data is not None and 'passed' in data:
                        self.mb.passed_local = data['passed']
            except Exception as e:
                debug_message.print_message(e)

            self.mb.exec_command('TL_OFF')
            debug_message.print_message(time.time())
            debug_message.print_message('===================!Get open MB to Master=====================')
        return data

    def slave_exit_mode(self):
        data = None
        with http_lock:
            debug_message.print_message('===================Get open MB to Master======================')
            debug_message.print_message(time.time())
            if self.point_direction == DirectionTypes.EXIT:
                self.mb.exec_command('GREEN')
            data = requests(urls=self.get_master_server() + '/OpenMb/', timeouts=13)
            debug_message.print_message(data)
            try:
                if data is not None:
                    data = json.loads(data)
                    if data is not None and 'passed' in data:
                        self.mb.passed_local = data['passed']
            except Exception as e:
                debug_message.print_message(e)

            self.mb.exec_command('TL_OFF')
            debug_message.print_message(time.time())
            debug_message.print_message('===================!Get open MB to Master=====================')
        return data

    def lock_master(self):
        debug_message.print_message('===================Lock MB on Master======================')
        debug_message.print_message(time.time())
        data = requests(urls=self.get_master_server() + '/LockCard/', timeouts=2)
        debug_message.print_message(data)
        try:
            if data is not None:
                data = json.loads(data)
                if data is not None and 'locked' in data:
                    return data['locked']
        except Exception as e:
            debug_message.print_message(e)

        debug_message.print_message(time.time())
        debug_message.print_message('===================!Lock MB on Master=====================')
        return False

    def unlock_master(self):
        debug_message.print_message('===================Unlock MB on Master======================')
        debug_message.print_message(time.time())
        data = requests(urls=self.get_master_server() + '/UnlockCard/', timeouts=2)
        debug_message.print_message(data)
        try:
            if data is not None:
                data = json.loads(data)
                if data is not None and 'locked' in data:
                    return data['locked']
        except Exception as e:
            debug_message.print_message(e)

        debug_message.print_message(time.time())
        debug_message.print_message('===================!Unlock MB on Master=====================')
        return False

    def is_active(self):
        if self.direction == DirectionTypes.BLOCKED:
            return False
        if self.direction == DirectionTypes.UNBLOCKED:
            return False
        if self.direction == DirectionTypes.ENTEREXIT or self.point_direction == self.direction:
            return True

    def is_master(self):
        return self.os_ip == self.master_ip

    def is_slave(self):
        return self.os_ip != self.master_ip

    def get_server(self):
        return 'http://' + self.server

    def get_master_server(self):
        return 'http://' + self.master_ip

    def get_slave_server(self):
        if self.is_slave():
            return 'http://' + self.os_ip
        else:
            return 'http://' + self.slave_ip

    def get_latest_params(self):
        if self.latest_params is not None:
            return self.latest_params
        else:
            return ''
            return

    def get_latest_init(self):
        if self.latest_init is not None:
            return self.latest_init
        else:
            return ''
            return

    def compare_params(self, data):
        _params_equal = True
        try:
            for k, v in data.items():
                if k in self.params_prev:
                    if v != self.params_prev[k]:
                        _params_equal = False
                        break
                else:
                    _params_equal = False
                    break

            self.params_prev = copy.deepcopy(data)
        except Exception as e:
            pass

        return _params_equal

    def reset_display(self):
        if self.direction != DirectionTypes.ENTEREXIT and self.point_direction != self.direction:
            self.show_stop()
        else:
            self.show_passport()

    def is_online(self):
        if self.point_mode == 'test':
            return True
        else:
            if self.mb is None:
                return
            return self.mb.is_main_online()

    def is_turnstile(self):
        if self.mb is None:
            return
        else:
            return self.mb.is_turnstile_monitor()

    def is_turnstile_monitor(self):
        if self.point_mode == 'test':
            return True
        else:
            if self.mb is None:
                return
            return self.mb.is_turnstile_monitor()

    def get_pin_data(self):
        if self.mb is None:
            return '-----'
        else:
            return self.mb.get_pin_data()

    def setup_interface(self, params):
        params_options = ['IP', 'NETMASK', 'GATEWAY', 'HTTP_OSBD', 'OSBD_HOSTNAME', 'HTTP_SDE', 'SDE_HOSTNAME',
         'MASTER_IP', 'DIRECTION', 'POINT_IP', 'MONITOR_IP']
        for _option in params_options:
            if _option not in params:
                return False

        def_config = os.path.join(self.app_path, 'defaults', '_rc.conf')
        sys_config = os.path.join('/etc/rc.d', 'rc.tst')
        def_hosts = os.path.join(self.app_path, 'defaults', '_hosts.conf')
        sys_hosts = os.path.join('/etc', 'hosts.tst')
        def_zeus_ini = os.path.join(self.app_path, 'defaults', '_zeus.ini')
        sys_zeus_ini = os.path.join(self.app_path, 'zeus.ini.tst')
        if self.is_production():
            def_config = os.path.join(self.app_path, 'defaults', '_rc.conf')
            sys_config = os.path.join('/etc/rc.d', 'rc.conf')
            def_hosts = os.path.join(self.app_path, 'defaults', '_hosts.conf')
            sys_hosts = os.path.join('/etc', 'hosts')
            def_zeus_ini = os.path.join(self.app_path, 'defaults', '_zeus.ini')
            sys_zeus_ini = os.path.join(self.app_path, 'zeus.ini')
        if not os.path.isfile(def_config) or not os.path.isfile(def_hosts) or not os.path.isfile(def_zeus_ini):
            return False
        with open(def_config, 'rb') as (_fp):
            f_data = _fp.read()
            for _option in params_options:
                f_data = f_data.replace('__' + _option + '__', params[_option][0])

            with open(sys_config, 'wb') as (_fpw):
                _fpw.write(f_data)
            os.chmod(sys_config, 420)
        with open(def_hosts, 'rb') as (_fp):
            f_data = _fp.read()
            for _option in params_options:
                f_data = f_data.replace('__' + _option + '__', params[_option][0])

            with open(sys_hosts, 'wb') as (_fpw):
                _fpw.write(f_data)
            os.chmod(sys_hosts, 420)
        with open(def_zeus_ini, 'rb') as (_fp):
            f_data = _fp.read()
            for _option in params_options:
                f_data = f_data.replace('__' + _option + '__', params[_option][0])

            with open(sys_zeus_ini, 'wb') as (_fpw):
                _fpw.write(f_data)
            os.chmod(sys_zeus_ini, 420)
        if self.is_production():
            os.system('sync')
            self.reboot_pher()
        return True

    def reboot_device(self):
        if not self.mb.is_online():
            return False
        self.mb.reboot_device()
        return True

    def reboot_pher(self):
        if not self.mb.is_online():
            return False
        self.mb.reboot_pher()
        return True

    def get_version(self):
        return self.version

    def get_mb_version(self):
        if self.mb is None:
            return ''
        else:
            return self.mb.get_version()

    def get_temperature(self):
        if self.mb is None:
            return ''
        else:
            return self.mb.get_temperature()

    def reset_open_sensor(self):
        if not self.mb.is_online():
            return False
        self.mb.reset_open_sensor()
        return True

    def check_master_point(self):
        if self.is_master():
            return
        else:
            if self.get_lock() or http_lock.locked():
                return
            data = requests(urls=self.get_master_server() + '/PingSlave/', timeouts=3)
            try:
                if data is not None:
                    data = json.loads(data)
                    if data is not None and 'status' in data:
                        if self.is_slave_conn is None or not self.is_slave_conn:
                            self.is_slave_conn = True
                        return
            except Exception as e:
                pass

            if self.is_slave_conn is not None and self.is_slave_conn:
                self.is_slave_conn = False
            return

    def check_slave_point(self):
        if self.is_slave() or not self.is_slave_ping:
            return
        if self.slave_local_time > 0 and time.time() - self.slave_local_time > 40:
            self.slave_local_time = 0
            self.is_slave_conn = False

    def get_osbd_status(self):
        return self.online

    def start_card_lock_time(self):
        self.card_local_time = time.time()
        self.mb.write_data('STATE')

    def stop_card_lock_time(self):
        self.mb.write_data('STATE')
        self.card_local_time = 0

    def set_slave_ping(self, ip=''):
        if not self.is_slave_ping:
            self.is_slave_ping = True
            self.slave_ip = ip
        self.slave_local_time = time.time()
        self.is_slave_conn = True

    def get_slave_status(self):
        return self.is_slave_conn

    def get_alarm(self):
        return not self.mb.get_alarm()

    def check_monitor(self):
        if self.is_master():
            if self.is_monitor is None:
                if self.monitor_check_idx != 4:
                    debug_message.print_message('Count to reset monitor...' + str(self.monitor_check_idx))
                    if self.monitor_check_idx == 3:
                        debug_message.print_message('Rebooting monitor...')
                        self.reboot_monitor()
                    self.monitor_check_idx += 1
                return
            if self.monitor_local_time > 0 and time.time() - self.monitor_local_time > 20:
                self.monitor_local_time = 0
                self.is_monitor = False
        return

    def set_monitor_ping(self):
        self.monitor_local_time = time.time()
        self.is_monitor = True

    def get_monitor_status(self):
        return self.is_monitor

    def get_reader_866_state(self):
        return self.is_reader_866

    def get_reader_1356_state(self):
        return self.is_reader_1356

    def get_reader_barcode_state(self):
        return self.is_reader_barcode

    def get_reader_866_reconnects(self):
        return self.reader_866_reconnects

    def get_reader_1356_reconnects(self):
        return self.reader_1356_reconnects

    def get_reader_barcode_reconnects(self):
        return self.reader_barcode_reconnects

    def set_reader_866_state(self, value):
        if self.is_reader_866 != value:
            self.is_reader_866 = value
            self.reader_866_reconnects += 1

    def set_reader_1356_state(self, value):
        if self.is_reader_1356 != value:
            self.is_reader_1356 = value
            self.reader_1356_reconnects += 1

    def set_reader_barcode_state(self, value):
        if self.is_reader_barcode != value:
            self.is_reader_barcode = value
            self.reader_barcode_reconnects += 1

    def get_access_point_mode(self):
        if self.type_id == AccessPointTypes.SP:
            return 'SP'
        if self.type_id == AccessPointTypes.AT:
            return 'AT'
        return '-'

    def get_access_point_type(self):
        if self.direction == DirectionTypes.ENTEREXIT:
            return 'EnEx'
        if self.direction == DirectionTypes.ENTER:
            return 'En'
        if self.direction == DirectionTypes.EXIT:
            return 'Ex'
        if self.direction == DirectionTypes.UNBLOCKED:
            return 'Un'
        if self.direction == DirectionTypes.BLOCKED:
            return 'Bl'
        return '-'

    def set_free_mode(self):
        self.mb.write_data('GREEN')
        self.show_go(prefix=self.get_go_prefix())
        self.free_mb()

    def set_normal_mode(self):
        self.normal_mb()
        self.show_passport()

    def get_mb_options(self):
        return self.mb.get_options()

    def set_mb_options(self, params):
        return self.mb.save_options(params)

    def get_options(self):
        _options = self.options.copy()
        _tmp = {'osbd_server': self.server, 'point_direction': self.point_direction, 'master_ip': self.master_ip, 
           'point_ip': self.ip, 'os_ip': self.os_ip, 'monitor_ip': self.monitor_ip, 
           'env': self.env}
        _options.update(_tmp)
        return _options

    def get_option(self, _key, _default=None):
        if _key in self.options:
            return self.options[_key]
        else:
            return _default

    def set_option(self, _key, _value):
        try:
            if _key == 'rfid_1356_reader':
                self.send_queue_option('rfid1356', _key, _value)
            elif _key == 'match_n':
                self.send_queue_option('rfid1356', _key, _value)
            elif _key == 'ff_date':
                self.send_queue_option('rfid1356', _key, _value)
            elif _key == 'ff_mode':
                self.send_queue_option('rfid1356', _key, _value)
            elif _key == 'nfc_enable':
                self.send_queue_option('rfid1356', _key, _value)
            elif _key == 'fifa_sac':
                self.send_queue_option('rfid1356', _key, _value)
            elif _key == 'barcode_length_128':
                self.send_queue_option('barcode', _key, _value)
            elif _key == 'barcode_length_2of5':
                self.send_queue_option('barcode', _key, _value)
            elif _key == 'barcode_reader':
                self.send_queue_option('barcode', _key, _value)
            if _key == 'groups':
                if _value is not None:
                    _tmp = _value
                    if len(_tmp) == 0 or _tmp == '0':
                        _value = []
                    else:
                        _value = _tmp.split(',')
                else:
                    _value = []
            elif _key == 'ff_date':
                _set_value = []
                if _value is not None:
                    debug_message.print_message('Set ff_date: ' + _value)
                    if len(_value) > 0:
                        _tmp = _value.split('-')
                        if len(_tmp) == 3:
                            _set_value = _tmp
                _value = _set_value
            self.options[_key] = _value
        except Exception as e:
            debug_message.print_message('--------Set option ' + _key + ' error--------')
            debug_message.print_message(e)
            debug_message.print_message('--------!Set option ' + _key + ' error-------')

        return

    def read_db_config(self):
        debug_message.print_message('-Reading db config')
        _config = ConfigParser.ConfigParser()
        _config.read(self.app_path + '/db.ini')
        _options = _config.options('DatabaseSection')
        _params = ['type_id', 'check_pass', 'rfid_ticket', 'direction']
        for _option in _params:
            if _option not in _options:
                return

        for option in _options:
            if option == 'type_id':
                self.options[option] = _config.getint('DatabaseSection', option)
            elif option == 'check_pass':
                self.options[option] = _config.getboolean('DatabaseSection', option)
            elif option == 'rfid_ticket':
                self.options[option] = _config.getboolean('DatabaseSection', option)
            elif option == 'attention_mode':
                self.options[option] = _config.getboolean('DatabaseSection', option)
            elif option == 'direction':
                self.options[option] = _config.getint('DatabaseSection', option)
            elif option == 'barcode_length_2of5':
                _tmp = _config.getint('DatabaseSection', option)
                self.set_option(option, _tmp)
            elif option == 'barcode_length_128':
                _tmp = _config.getint('DatabaseSection', option)
                self.set_option(option, _tmp)
            elif option == 'barcode_reader':
                _tmp = _config.getboolean('DatabaseSection', option)
                self.set_option(option, _tmp)
            elif option == 'rfid_1356_reader':
                self.options[option] = _config.getboolean('DatabaseSection', option)
            elif option == 'rfid_866_reader':
                self.options[option] = _config.getboolean('DatabaseSection', option)
            elif option == 'groups':
                self.set_option('groups', _config.get('DatabaseSection', option))
            elif option == 'ff_mode':
                self.options[option] = _config.getboolean('DatabaseSection', option)
            elif option == 'nfc_enable':
                self.options[option] = _config.getboolean('DatabaseSection', option)
            elif option == 'key_server_ip':
                self.set_option('key_server_ip', _config.get('DatabaseSection', option))
            elif option == 'key_server_port':
                self.set_option('key_server_port', _config.get('DatabaseSection', option))
            elif option == 'card_wait_time':
                self.set_option('card_wait_time', _config.getint('DatabaseSection', option))
            elif option == 'pass_wait_time':
                self.set_option('pass_wait_time', _config.getint('DatabaseSection', option))
            elif option == 'show_wait_time':
                self.set_option('show_wait_time', _config.getint('DatabaseSection', option))
            elif option == 'ff_date':
                self.set_option('ff_date', _config.get('DatabaseSection', option))
            elif option == 'num_requests':
                self.set_option('num_requests', _config.getint('DatabaseSection', option))
            elif option == 'mb_timeout':
                self.set_option('mb_timeout', _config.getfloat('DatabaseSection', option))

        debug_message.print_message(self.options)
        try:
            if 'type_id' in self.options:
                if self.options['type_id'] == 2:
                    self.type_id = AccessPointTypes.SP
                elif self.options['type_id'] == 3:
                    self.type_id = AccessPointTypes.AT
                else:
                    self.type_id = AccessPointTypes.P
            if 'direction' in self.options:
                if self.options['direction'] == 0:
                    self.direction = DirectionTypes.ENTER
                elif self.options['direction'] == 1:
                    self.direction = DirectionTypes.EXIT
                elif self.options['direction'] == 2:
                    self.direction = DirectionTypes.ENTEREXIT
                elif self.options['direction'] == 3:
                    self.direction = DirectionTypes.BLOCKED
                elif self.options['direction'] == 4:
                    self.direction = DirectionTypes.UNBLOCKED
            if 'check_pass' in self.options:
                self.check_pass = self.options['check_pass']
            if 'rfid_ticket' in self.options:
                self.rfid_ticket = self.options['rfid_ticket']
            if 'attention_mode' in self.options:
                self.attention_mode = self.options['attention_mode']
            if 'groups' not in self.options:
                self.options['groups'] = []
            if 'card_wait_time' in self.options:
                self.card_wait_time = self.options['card_wait_time']
            if 'pass_wait_time' in self.options:
                self.pass_wait_time = self.options['pass_wait_time']
            if 'show_wait_time' in self.options:
                self.show_wait_time = self.options['show_wait_time']
            if 'num_requests' in self.options:
                self.num_requests = self.options['num_requests']
        except Exception as e:
            debug_message.print_message('--------Read db config error--------')
            debug_message.print_message(e)
            debug_message.print_message('--------Read db config error--------')

        debug_message.print_message(self.options)

    def save_options(self, params):
        params_options = [
         'type_id', 'check_pass', 'rfid_ticket', 'direction']
        for _option in params_options:
            if _option not in params:
                return False

        config = ConfigParser.ConfigParser()
        config.read(self.app_path + '/db.ini')
        _check_pass = False
        _rfid_ticket = False
        if params['check_pass'][0] == 'true':
            _check_pass = True
        if params['rfid_ticket'][0] == 'true':
            _rfid_ticket = True
        config.set('DatabaseSection', 'type_id', params['type_id'][0])
        config.set('DatabaseSection', 'check_pass', _check_pass)
        config.set('DatabaseSection', 'rfid_ticket', _rfid_ticket)
        config.set('DatabaseSection', 'direction', params['direction'][0])
        with open(self.app_path + '/db.ini', 'wb') as (configfile):
            config.write(configfile)
        os.system('sync')
        self.reboot_pher()
        return True

    def save_options_database(self):
        config = ConfigParser.ConfigParser()
        config.read(self.app_path + '/db.ini')
        if self.type_id == AccessPointTypes.SP:
            _type_id = 2
        elif self.type_id == AccessPointTypes.AT:
            _type_id = 3
        else:
            _type_id = 1
        _direction = 2
        if self.direction == DirectionTypes.ENTER:
            _direction = 0
        elif self.direction == DirectionTypes.EXIT:
            _direction = 1
        elif self.direction == DirectionTypes.ENTEREXIT:
            _direction = 2
        elif self.direction == DirectionTypes.BLOCKED:
            _direction = 3
        elif self.direction == DirectionTypes.UNBLOCKED:
            _direction = 4
        _groups = '0'
        if self.get_option('groups') is not None and len(self.get_option('groups')) > 0:
            _groups = (',').join(self.get_option('groups'))
        config.set('DatabaseSection', 'type_id', _type_id)
        config.set('DatabaseSection', 'check_pass', self.check_pass)
        config.set('DatabaseSection', 'rfid_ticket', self.rfid_ticket)
        config.set('DatabaseSection', 'direction', _direction)
        config.set('DatabaseSection', 'barcode_reader', self.is_barcode_active())
        config.set('DatabaseSection', 'rfid_1356_reader', self.is_rfid_1356_active())
        config.set('DatabaseSection', 'rfid_866_reader', self.is_rfid_866_active())
        config.set('DatabaseSection', 'groups', _groups)
        config.set('DatabaseSection', 'card_wait_time', self.card_wait_time)
        config.set('DatabaseSection', 'pass_wait_time', self.pass_wait_time)
        config.set('DatabaseSection', 'show_wait_time', self.show_wait_time)
        config.set('DatabaseSection', 'barcode_length_2of5', self.barcode_length_2of5)
        config.set('DatabaseSection', 'barcode_length_128', self.barcode_length_128)
        config.set('DatabaseSection', 'ff_mode', self.get_option('ff_mode', False))
        config.set('DatabaseSection', 'nfc_enable', self.get_option('nfc_enable', False))
        _date = self.get_option('ff_date', '')
        _tmp = ''
        if isinstance(_date, list) and len(_date) == 3:
            _tmp = ('-').join(_date)
        config.set('DatabaseSection', 'ff_date', _tmp)
        with open(self.app_path + '/db.ini', 'wb') as (configfile):
            config.write(configfile)
        os.system('sync')
        return True

    def set_direction(self):
        if self.direction_prev == DirectionTypes.UNBLOCKED:
            debug_message.print_message('====================Access point prev is ublocked========================')
            self.normal_mb()
        if self.direction == DirectionTypes.BLOCKED:
            debug_message.print_message('====================Access point is blocked==============================')
            self.show_stop()
        elif self.direction == DirectionTypes.UNBLOCKED:
            debug_message.print_message('====================Access point is unblocked==============================')
            self.free_mb()
            self.show_go(prefix=self.get_go_prefix())
            self.mb.exec_command('GREEN')
        elif self.direction != DirectionTypes.ENTEREXIT and self.point_direction != self.direction:
            debug_message.print_message('====================Access point is closed===============================')
            self.show_stop()
        elif self.direction == DirectionTypes.ENTEREXIT or self.point_direction == self.direction:
            debug_message.print_message('====================Access point is open=================================')
            self.show_passport()
        self.direction_prev = self.direction

    def set_light(self):
        if self.direction == DirectionTypes.BLOCKED:
            self.mb.exec_command('RED')
        elif self.direction == DirectionTypes.UNBLOCKED:
            self.mb.exec_command('GREEN')
        elif self.direction != DirectionTypes.ENTEREXIT and self.point_direction != self.direction:
            self.mb.exec_command('RED')
        elif self.direction == DirectionTypes.ENTEREXIT or self.point_direction == self.direction:
            self.mb.exec_command('TL_OFF')

    def attention_in_offline_mode(self):
        if self.online or not self.attention_mode:
            return
        if self.direction == DirectionTypes.ENTEREXIT or self.point_direction == self.direction:
            if self.get_lock() or http_lock.locked():
                return
            self.mb.exec_command('RED')
            time.sleep(0.1)
            if self.get_lock() or http_lock.locked():
                return
            self.set_light()

    def reboot_monitor(self):
        if self.is_master():
            debug_message.print_message('--------Monitor reset------------')
            thread_monitor = threading.Thread(target=ssh_wrapper.reboot_monitor)
            thread_monitor.start()
            debug_message.print_message('--------!Monitor reset-----------')
            return True
        return False

    def is_barcode_active(self):
        _ret = self.get_option('barcode_reader')
        if _ret is None:
            _ret = True
        return _ret

    def is_rfid_1356_active(self):
        _ret = self.get_option('rfid_1356_reader')
        if _ret is None:
            _ret = True
        return _ret

    def is_rfid_866_active(self):
        _ret = self.get_option('rfid_866_reader')
        if _ret is None:
            _ret = True
        return _ret

    def in_blacklist(self, _code):
        debug_message.print_message('\tCheck code in blacklist')
        _ret = False
        try:
            _filename = '/mnt/ramdisk/tmp/blacklist.txt'
            if os.path.isfile(_filename):
                with open(_filename, 'r') as (_file):
                    for _line in _file:
                        if ';' + _code + ';' in ';' + _line:
                            _ret = True
                            break

            debug_message.print_message(str(_ret))
        except Exception as e:
            pass

        debug_message.print_message('\t!Check code in blacklist')
        return _ret

    def in_whitelist(self, _code):
        _filename = '/mnt/ramdisk/tmp/whitelist.txt'
        _ret = None
        debug_message.print_message('\tCheck code in whitelist')
        try:
            if os.path.isfile(_filename):
                with open(_filename, 'r') as (_file):
                    debug_message.print_message('\tchecking ' + _code)
                    for _line in _file:
                        if ';' + _code + ';' in ';' + _line:
                            _record = _line.strip()
                            _ret = True
                            break

            if _ret:
                debug_message.print_message('\tFound record: ' + str(_record))
                if ';1;' in _record + ';':
                    debug_message.print_message('\talready passed')
                    _ret = False
                else:
                    _ret = True
                    _ids = self.get_option('groups')
                    if _ids is not None and len(_ids) > 0:
                        for _id in _ids:
                            debug_message.print_message('\tchecking group: ' + _id)
                            if ';' + _id + ';' in _record:
                                debug_message.print_message('\t\tin group')
                                self.in_group = True
                                _ret = False

            debug_message.print_message(str(_ret))
        except Exception as e:
            pass

        debug_message.print_message('\t!Check code in whitelist')
        return _ret

    def in_mastercards(self, _code):
        _option = self.get_option('ff_mode', False)
        if not _option:
            return False
        debug_message.print_message('\tCheck code in mastercard list')
        try:
            _code = _code.upper()
            _filename = '/mnt/ramdisk/tmp/mastercards.txt'
            _ret = False
            if os.path.isfile(_filename):
                with open(_filename, 'r') as (_file):
                    for _line in _file:
                        _record = _line.strip()
                        if _code == _record:
                            _ret = True
                            break

        except Exception as e:
            pass

        debug_message.print_message('\t!Check code in mastercard list')
        return _ret

    def check_offline_access(self, _code, _decrypt=False):
        _option = self.get_option('ff_mode', False)
        if not _option:
            return True
        else:
            _code = _code.upper()
            debug_message.print_message('Checking code: ' + _code)
            _ret = self.in_mastercards(_code)
            if _ret:
                debug_message.print_message('\tcode in mastercard')
                return True
            if not _decrypt:
                return False
            _ret = self.in_archive(_code)
            if _ret:
                debug_message.print_message('\tcode in archive')
                return False
            _ret = self.in_blacklist(_code)
            if not _ret:
                _ret = self.in_whitelist(_code)
                if _ret is None:
                    _ret = _decrypt
            else:
                _ret = False
            return _ret

    def get_lists(self):
        if not self.online:
            return
        _option = self.get_option('ff_mode', False)
        if _option and self.point_id:
            self.get_match_keys_thread()
            Process(target=self.get_lists_thread, args=(get_list_lock,)).start()

    def get_lists_thread(self, _lock):
        if not self.online:
            return
        if not _lock.acquire(False):
            return
        debug_message.print_message('===================Get lists update======================')
        debug_message.print_message('Get lists from ' + self.server + ' for ' + str(self.point_id))
        self.get_cmd_out('sh -e /home/user/get_lists.sh ' + self.server + ' ' + str(self.point_id))
        debug_message.print_message('===================!Get lists update====================')
        _lock.release()

    def in_archive(self, _code):
        _ret = False
        try:
            if len(self.archive):
                debug_message.print_message('---------------In archive--------------')
                for k, v in self.archive.items():
                    debug_message.print_message(v['code_1'].upper())
                    debug_message.print_message(v['code_2'].upper())
                    debug_message.print_message(v['enter'])
                    if v['code_1'].upper() == _code or v['code_2'].upper() == _code:
                        if v['enter'] == 1:
                            _ret = True

                debug_message.print_message('---------------In archive--------------')
        except Exception as e:
            debug_message.print_message(e)

        return _ret

    def get_key_server_ip(self):
        _ret = self.get_option('key_server_ip')
        if _ret is None:
            _ret = ''
        return _ret

    def get_key_server_port(self):
        _ret = self.get_option('key_server_port')
        if _ret is None:
            _ret = ''
        return _ret

    def set_pid(self, _value):
        self.pid = _value

    def get_cmd_out(self, _cmd=''):
        out = ''
        debug_message.print_message(_cmd)
        try:
            p = subprocess.Popen(_cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = p.communicate()
            p.stdout.close()
            sys.stdout.flush()
        except Exception as e:
            debug_message.print_message(e)

        return out

    def get_process_memory(self, _pid):
        _memory = 0
        try:
            if self.pid > 0:
                _file = '/proc/' + str(_pid) + '/status'
                if os.path.isfile(_file):
                    with open(_file) as (_file):
                        for _line in _file:
                            if 'VmRSS' in _line.strip():
                                _record = _line.strip()
                                _memory = ('').join(x for x in _record if x.isdigit())
                                if len(_memory):
                                    _memory = int(_memory)

        except Exception as e:
            debug_message.print_message('----------------memory get error-----------------')
            debug_message.print_message(e)
            debug_message.print_message('----------------!memory get error----------------')

        return _memory

    def get_system_usage(self):
        _cpu = 0
        _mem = 0
        try:
            _out = self.get_cmd_out("ps aux | grep python | grep -v grep | awk '{print $2,$3,$4}'")
            _out = _out.strip()
            _records = _out.split('\n')
            if _records:
                for _rec in _records:
                    _values = _rec.split(' ')
                    if len(_values) == 3:
                        _cpu += float(_values[1])
                        _mem += self.get_process_memory(_values[0])

            self.memory_usage = _mem
            self.cpu_usage = int(_cpu)
        except Exception as e:
            debug_message.print_message('----------------cpu get error-----------------')
            debug_message.print_message(e)
            debug_message.print_message('----------------!cpu get error----------------')

    def get_cpu_usage(self):
        return self.cpu_usage

    def get_memory_usage(self):
        return self.memory_usage

    def get_time_decline(self):
        return self.show_wait_time

    def get_time_wait_pass(self):
        return self.pass_wait_time

    def get_time_wait_card(self):
        return self.card_wait_time

    def mb_state_init(self):
        if self.mb is None:
            return
        else:
            if not self.mb.mb_init_state:
                debug_message.print_message('==========No need to make MN INIT==================')
                return
            if self.thread_mb_init is None or not self.thread_mb_init.is_alive():
                self.thread_mb_init = threading.Thread(target=self.mb.init_state)
                self.thread_mb_init.start()
            return

    def get_current_match_id(self):
        return self.get_option('match_n', 0)

    def get_sac(self):
        return self.get_option('fifa_sac', '')

    def set_sac(self, sac):
        if self.get_sac() != sac:
            self.set_option('fifa_sac', sac)

    def get_sam(self):
        return self.get_option('fifa_sam', '')

    def set_sam(self, sam=''):
        if self.get_sam() != sam:
            self.set_option('fifa_sam', sam)

    def get_match_name(self):
        return self.get_option('fifa_match_name', '')

    def set_match_name(self, match=''):
        if self.get_match_name() != match:
            debug_message.print_message('match name is: ' + match)
            self.set_option('fifa_match_name', match)

    def get_match_keys_thread(self):
        if not self.online:
            return
        else:
            if self.match_keys_thread is None or not self.match_keys_thread.is_alive():
                self.match_keys_thread = threading.Thread(target=self.get_match_keys)
                self.match_keys_thread.start()
            return

    def get_match_keys(self):
        if not self.online:
            return
        else:
            debug_message.print_message('===================Get match key======================')
            _match_id = self.get_current_match_id()
            debug_message.print_message('match is: ' + str(_match_id))
            if _match_id == 0:
                return
            debug_message.print_message('Get GetMatches: ' + str(self.point_id))
            params = {'PointID': self.point_id}
            _request = requests(urls=self.get_server() + '/GetMatches/', params=params, timeouts=10)
            try:
                if _request is not None and len(_request) > 10:
                    data = json.loads(_request)
                    _found = False
                    if data is not None and isinstance(data, list) and len(data) > 0:
                        for _rec in data:
                            if _rec is not None and isinstance(_rec, dict) and 'ExternEventID' in _rec:
                                if _rec['ExternEventID'] is None:
                                    self.set_option('fifa_sac', '')
                                elif 'FIFA_SAC' in _rec and 'FIFA_SAM' in _rec:
                                    if int(_rec['ExternEventID']) == _match_id:
                                        _found = True
                                        _sac = _rec['FIFA_SAC']
                                        _sac_tmp = self.get_sac()
                                        if _sac_tmp != _sac:
                                            debug_message.print_message('\tMatch keys not mach')
                                            self.set_sac(_sac)
                                            debug_message.print_message('FF SAC: ' + self.get_sac())
                                        _sam = _rec['FIFA_SAM']
                                        _sam_curr = self.get_sam()
                                        if _sam_curr != _sam:
                                            debug_message.print_message('\tMatch sam new data')
                                            self.set_sam(_sam)
                                            if 'Name' in _rec:
                                                self.set_match_name(_rec['Name'])
                                            _filename = '/usr/AWS_FIFA/Virtual_SAM_M' + str(_match_id) + '.txt'
                                            with open(_filename, 'wb') as (_fpw):
                                                _fpw.write(_sam)
                                            self.show_addition_message()

                    if not _found:
                        self.set_sac('')
                        self.set_sam('')
                        self.set_match_name('')
            except Exception as e:
                debug_message.print_message('----------------Get march keys-----------------')
                debug_message.print_message(e)
                debug_message.print_message('----------------!Get march keys----------------')

            return

    def check_update(self):
        if self.get_lock() or http_lock.locked():
            return
        _filename = '/mnt/ramdisk/app_new.zip'
        if os.path.isfile(_filename):
            self.updating = True
            self.direction = DirectionTypes.BLOCKED
            self.show_wait()
            debug_message.print_message('===============New update found===============')
            debug_message.print_message('\tUpdating...')
            self.mb.exec_command('STATE')
            self.get_cmd_out('cp -R /mnt/ramdisk/app_new.zip /home/user/app.zip')
            self.get_cmd_out('rm -fr /mnt/ramdisk/app_new.zip')
            self.restart_program()
            debug_message.print_message('===============!New update found==============')

    def is_updating(self):
        return self.updating

    def restart_program(self):
        _cmd = '/etc/rc.d/init.d/zeusd restart'
        subprocess.Popen(_cmd, shell=True)

    def set_sys_time(self, _datetime):
        debug_message.print_message('================SET NEW DATETIME====================')
        _tmp = _datetime.replace('-', '').replace('T', '')
        _records = _tmp.split(':')
        if len(_records) == 3:
            _sec_mil = _records[2].split('.')
            if len(_sec_mil) == 2:
                _datetime = _records[0] + _records[1] + '.' + _sec_mil[0]
            else:
                _datetime = ''
        debug_message.print_message('Datetime: ' + _datetime)
        debug_message.print_message(type(_datetime))
        if isinstance(_datetime, unicode):
            try:
                _datetime = _datetime.encode('utf-8')
            except Exception as e:
                debug_message.print_message(e)

        if isinstance(_datetime, str):
            debug_message.print_message('date is a string')
        if isinstance(_datetime, str) and len(_datetime) == 15:
            debug_message.print_message('\tsystem date is correct')
            self.get_cmd_out('date -s ' + _datetime)
            self.get_cmd_out('busybox hwclock --systohc')
        else:
            debug_message.print_message('\tsystem date is incorrect')
        debug_message.print_message('================SET NEW DATETIME====================')

    def get_match_date(self):
        _date = self.get_option('ff_date', '')
        if isinstance(_date, list) and len(_date) == 3:
            debug_message.print_message('\tMatch date from config')
            _tmp = bytearray()
            _tmp.append(int(_date[0]))
            _tmp.append(int(_date[1]))
            _tmp.append(int(_date[2]))
            return _tmp
        else:
            debug_message.print_message('\tMatch date from today')
            d = datetime.datetime.now()
            _y = d.date().strftime('%y')
            _m = d.date().strftime('%m')
            _d = d.date().strftime('%d')
            _tmp = bytearray()
            _tmp.append(int(_d))
            _tmp.append(int(_m))
            _tmp.append(int(_y))
            return _tmp

    def send_archive_thread(self):
        if self.online:
            if self.archive_thread is None or not self.archive_thread.is_alive():
                self.archive_thread = threading.Thread(target=self.send_archive)
                self.archive_thread.start()
        return

    def send_archive(self):
        try:
            if len(self.archive):
                for k, v in self.archive.items():
                    self.write_log_archive(k, v)

        except Exception as e:
            debug_message.print_message('----------Send archive error------------')
            debug_message.print_message(e)
            debug_message.print_message('----------Send archive error------------')

    def set_startup_time(self):
        d = datetime.datetime.now()
        self.startup_time = d.date().strftime('%Y.%m.%d') + d.time().strftime(' %H:%M:%S')

    def get_start_time(self):
        return self.startup_time

    def get_nfc_enable(self):
        return self.get_option('nfc_enable', False)

    def check_debug_message(self):
        debug_message.check_web_mode()
        _cur_open_sensor = self.mb.get_open_sensor()
        if _cur_open_sensor and _cur_open_sensor != self.cur_open_sensor:
            debug_message.print_message('----------Opensensor change to true------------')
            self.cur_open_sensor = True
            self.show_debug_message()
        elif not _cur_open_sensor and _cur_open_sensor != self.cur_open_sensor:
            debug_message.print_message('----------Opensensor change to false------------')
            self.cur_open_sensor = False
            self.hide_debug_message()

    def show_debug_message(self):
        _dmsg = self.perform_debug_message()
        self.set_debug_layer(_dmsg)

    def hide_debug_message(self):
        self.hide_debug_layer()

    def set_display_message(self, message):
        if self.display is not None:
            self.display.set_message(message)
        return

    def set_debug_layer(self, message):
        if self.display is not None:
            self.display.set_debug_layer(message)
        return

    def show_debug_layer(self):
        if self.display is not None:
            self.display.show_debug_layer()
        return

    def hide_debug_layer(self):
        if self.display is not None:
            self.display.hide_debug_layer()
        return

    def set_addition_layer(self, message):
        if self.get_option('ff_mode', False) and self.display is not None:
            self.display.set_addition_layer(message)
        return

    def show_addition_layer(self):
        if self.get_option('ff_mode', False) and self.display is not None:
            self.display.show_addition_layer()
        return

    def show_addition_message(self):
        _dmsg = self.perform_addition_message()
        debug_message.print_message(_dmsg)
        self.set_addition_layer(_dmsg)
        self.show_addition_layer()

    def hide_addition_layer(self):
        if self.display is not None:
            self.display.hide_addition_layer()
        return

    def show_debug_mode(self):
        if self.display is not None:
            self.display.show_debug_mode()
        return

    def get_ipaddr(self):
        _out = self.get_cmd_out("ifconfig eth0 | grep 'inet addr' | cut -d: -f2 | awk '{print $1}'")
        _out = _out.strip()
        if not _out:
            _out = self.get_cmd_out("ifconfig eth1 | grep 'inet addr' | cut -d: -f2 | awk '{print $1}'")
            _out = _out.strip()
        if _out:
            return _out
        return ''

    def get_netmask(self):
        _out = self.get_cmd_out("ifconfig eth0 | grep ' Mask' | cut -d: -f4 | awk '{print $0}'")
        _out = _out.strip()
        if not _out:
            _out = self.get_cmd_out("ifconfig eth1 | grep ' Mask' | cut -d: -f4 | awk '{print $0}'")
            _out = _out.strip()
        if _out:
            return _out
        return ''

    def display_reload_config(self):
        if self.display is not None:
            self.display.reload_config()
        return

    def display_close(self):
        if self.display is not None:
            self.display.close_app()
        return

    def perform_debug_message(self):
        _version = self.get_version()
        _version_mb = self.get_mb_version()
        _temperature = self.get_temperature()
        _osbd = self.get_osbd_status()
        _slave = self.get_slave_status()
        _turnstile = self.is_turnstile_monitor()
        _mb = self.is_online()
        _monitor = self.get_monitor_status()
        _reader1 = self.get_reader_866_state()
        _reader2 = self.get_reader_1356_state()
        _reader3 = self.get_reader_barcode_state()
        _cpu = self.get_cpu_usage()
        _memory = self.get_memory_usage()
        _pin_data = self.get_pin_data()
        _startup_time = self.get_start_time()
        _access_mode = self.get_access_point_mode()
        _point_type = self.get_access_point_type()
        _tmp = self.get_match_date()
        _match_date = hexlify(_tmp)
        _sac = self.get_sac()
        if len(_sac) > 4:
            _sac = _sac[-4:]
        _data = {'vap': _version, 'vmb': _version_mb, 'r1': _reader1, 'r2': _reader2, 
           'r3': _reader3, 'ts': _turnstile, 'bd': _osbd, 'mb': _mb, 
           'mo': _monitor, 'sl': _slave, 'c': _temperature, 'am': _access_mode, 
           'pt': _point_type, 'mem': _memory, 
           'cpu': _cpu, 'pin': _pin_data, 'fdate': _match_date, 'sac': _sac}
        _out = self.get_ipaddr() + '=' + self.get_netmask()
        _out += '=' + self.point_code
        _has_new_line = False
        for _key in _data:
            if isinstance(_data[_key], bool) and _data[_key] == True:
                continue
            if len(_out) >= 65 and not _has_new_line:
                _out += '|'
                _has_new_line = True
            else:
                _out += '='
            _out += _key + '_' + str(_data[_key])

        debug_message.print_message(_out)
        return _out

    def perform_addition_message(self):
        _out = self.point_code
        _out = ''
        if len(self.get_match_name()) > 0:
            _out += ' ' + self.get_match_name()
        _out += ' %date% %time%'
        debug_message.print_message(_out)
        return _out

    def get_is_new_match(self):
        return self.is_new_match

    def set_is_new_match(self, _val):
        if self.is_new_match != _val:
            self.is_new_match = _val

    def send_queue(self):
        if self.is_rfid_1356_active() and self.get_option('rfid1356_enable', False):
            debug_message.print_message('Send read to rfid1356 queue')
            if self.rfid1356qe is not None:
                self.rfid1356qe.put(QueueData('read', True))
        if self.barcodeqe is not None and self.is_barcode_active():
            debug_message.print_message('Send read to barcode queue')
            if self.barcodeqe is not None:
                self.barcodeqe.put(QueueData('options', {'key': 'is_data', 'value': True}))
        return

    def send_queue_option(self, _type, _key, _value):
        if _type == 'rfid1356' and self.get_option('rfid1356_enable', False):
            debug_message.print_message('Put data to rfid1356 queue')
            if _key == 'rfid_1356_reader':
                _key = 'active'
            if self.rfid1356qe is not None:
                self.rfid1356qe.put(QueueData('options', {'key': _key, 'value': _value}))
        elif _type == 'barcode':
            debug_message.print_message('Put data to barcode queue')
            if _key == 'barcode_reader':
                _key = 'active'
            if self.barcodeqe is not None:
                self.barcodeqe.put(QueueData('options', {'key': _key, 'value': _value}))
        return

    def set_light_barcode_on(self):
        self.mb.write_data('LIGHT_ON')

    def set_light_barcode_off(self):
        self.mb.write_data('LIGHT_OFF')

    def set_light_barcode_blink_on(self):
        self.mb.write_data('LIGHT_PWM_ON')

    def set_light_barcode_blink_off(self):
        self.mb.write_data('LIGHT_PWM_OFF')

    def set_debug_on(self):
        debug_message.set_mode(env='development')

    def set_debug_off(self):
        debug_message.set_mode(env='production')

    def get_os_ip(self):
        return self.os_ip

    def get_access_point_init(self):
        data = {}
        try:
            params = {'IP': self.ip}
            _request = requests(urls=self.get_server() + '/AccessPointInit/', params=params, timeouts=self.socket_timeout)
            if _request is not None:
                data = json.loads(_request)
            else:
                data['message'] = 'Data is empty'
        except Exception as e:
            data['message'] = 'Data exception'
            data['exception'] = e
            debug_message.print_message('-------------Get point by ID-----------------')
            debug_message.print_message(e)
            debug_message.print_message('-------------!Get point by ID----------------')

        return data

    def get_access_point_params(self):
        data = {}
        if not self.point_id:
            data['message'] = 'PointID is 0'
        try:
            params = {'PointID': self.point_id}
            _request = requests(urls=self.get_server() + '/AccessPointParams/', params=params, timeouts=self.socket_timeout)
            if _request is not None:
                data = json.loads(_request)
            else:
                data['message'] = 'Data is empty'
        except Exception as e:
            data['message'] = 'Data exception'
            data['exception'] = e
            debug_message.print_message('-------------Get point by ID-----------------')
            debug_message.print_message(e)
            debug_message.print_message('-------------!Get point by ID----------------')

        return data

    def set_access_point_init(self):
        self.point_id = 0
        return {'message': 'PointID set to 0. Please wating 10 seconds...'}

    def get_list_count(self):
        data = {}
        if not self.point_id:
            data['message'] = 'PointID is 0'
            return
        else:
            if not self.get_option('ff_mode', False):
                data['message'] = 'FfMode is not set'
                return
            if not self.get_current_match_id():
                data['message'] = 'MatchId is 0'
                return
            data = {'LocalLastUpdateTime': 'is empty', 'RemoteLastUpdateTime': 'is empty', 'MasterCards': 0, 'WhiteList': 0, 'BlackList': 0}
            try:
                _filename = '/mnt/ramdisk/tmp/cur_date.txt'
                if os.path.isfile(_filename):
                    with open(_filename, 'r') as (_file):
                        for _line in _file:
                            _record = _line.strip()
                            if _record:
                                data['LocalLastUpdateTime'] = _record
                                break

                _filename = '/mnt/ramdisk/tmp/mastercards.txt'
                _count = 0
                if os.path.isfile(_filename):
                    with open(_filename, 'r') as (_file):
                        for _line in _file:
                            _record = _line.strip()
                            if _record:
                                _count += 1

                data['MasterCards'] = _count
                _filename = '/mnt/ramdisk/tmp/whitelist.txt'
                _count = 0
                if os.path.isfile(_filename):
                    with open(_filename, 'r') as (_file):
                        for _line in _file:
                            _record = _line.strip()
                            if _record:
                                _count += 1

                data['WhiteList'] = _count
                _filename = '/mnt/ramdisk/tmp/blacklist.txt'
                _count = 0
                if os.path.isfile(_filename):
                    with open(_filename, 'r') as (_file):
                        for _line in _file:
                            _record = _line.strip()
                            if _record:
                                _count += 1

                data['BlackList'] = _count
                params = {'PointID': self.point_id}
                _request = requests(urls=self.get_server() + '/GetTicketList/GetLastUpdate/', params=params, timeouts=self.socket_timeout)
                if _request is not None:
                    data['RemoteLastUpdateTime'] = _request
            except Exception as e:
                data['message'] = 'Data exception'
                data['exception'] = e
                debug_message.print_message('-------------Get point by ID-----------------')
                debug_message.print_message(e)
                debug_message.print_message('-------------!Get point by ID----------------')

            return data

    def set_update_mode(self):
        self.direction = DirectionTypes.BLOCKED
        self.show_wait()

    def get_go_prefix(self):
        if not self.get_option('ff_mode', False):
            return ''
        _prefix = ''
        if self.point_direction == DirectionTypes.ENTER:
            _prefix = '_en'
        elif self.point_direction == DirectionTypes.EXIT:
            _prefix = '_ex'
        debug_message.print_message('--------Go prefix is ' + _prefix)
        return _prefix
# okay decompiling /home/a/Desktop/app/AccessPoint.pyc
