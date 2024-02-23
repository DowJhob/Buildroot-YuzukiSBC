# uncompyle6 version 3.4.0
# Python bytecode 2.7 (62211)
# Decompiled from: Python 2.7.15+ (default, Jul  9 2019, 16:51:35) 
# [GCC 7.4.0]
# Embedded file name: /home/user/zeus/ManagmentBoard.py
# Compiled at: 2018-05-28 21:51:22
import serial, time, threading, ConfigParser
from config import DirectionTypes, StateTypes, mb_lock, waiting_lock, add_lock, cards_lock, common_lock, mb_write_lock
import os, re
from DebugImport import debug_message

class ManagmentBoardDaemon(threading.Thread):

    def __init__(self, app_path, point_direction, is_master):
        threading.Thread.__init__(self)
        self.app_path = app_path
        self.server = None
        self.online = True
        self.point_direction = point_direction
        self.is_master = is_master
        self.ready = False
        self.mb_ready = False
        self.error = False
        self.passed = False
        self.passed_local = False
        self.is_config = False
        self.is_connect = False
        self.options = {}
        self.ready_set = 'PIN4 1'
        self.reset_device = 'HARDRST 1'
        self.ready_unset = 'PIN4 0'
        self.passed_set = 'PIN5 0'
        self.ready_passed_set = 'PIN5 1'
        self.error_set = 'PIN6 1'
        self.error_unset = 'PIN6 0'
        self.alarm_set = 'ALARM 1'
        self.alarm_unset = 'ALARM 0'
        self.temp_set = 'TEMP '
        self.version = 'VER '
        self.current_version = ''
        self.state_init = False
        self.thread_w = None
        self.state = True
        self.temperature = 0
        self.turnstile = False
        self.is_alarm = False
        self.is_open_sensor = False
        self.reset_pher = False
        self.pin_data = '-----'
        self.in_waiting = False
        self.mb_init_state = False
        self.mb_init_state_count = 0
        self.direction_state = StateTypes.INIT
        self.cur_open_sensor_state = False
        return

    def run(self):
        if self.is_master:
            self.error = True
        else:
            self.turnstile = True
        self.state = StateTypes.INIT
        self.state_init = True
        self.read_config()
        debug_message.print_message('----------MB config readed----------')
        self.open_port()
        debug_message.print_message('----------MB port open end----------')
        self.init_connect()
        debug_message.print_message('----------MB init commands sended----------')
        if self.state == StateTypes.INIT:
            self.state = StateTypes.READING
        self.read_data()

    def open_port(self):
        if self.is_config:
            try:
                if self.is_connect:
                    self.server.close()
                self.is_connect = False
                self.mb_ready = False
                if not self.server:
                    self.server = serial.Serial()
                self.server.port = self.options['port']
                self.server.baudrate = int(self.options['baudrate'])
                self.server.timeout = 1.0
                self.server.write_timeout = 1.0
                self.server.open()
                if self.server and self.server.is_open:
                    self.is_connect = True
                    self.state = StateTypes.CONNECT
                    debug_message.print_message('port opened')
            except serial.SerialException:
                debug_message.print_message('MB SerialException Error')
                self.is_connect = False
                self.state = StateTypes.ERROR
            except ValueError as e:
                debug_message.print_message(e)
                debug_message.print_message('ValueError Error')
                self.is_connect = False
                self.state = StateTypes.ERROR

    def close_port(self):
        self.online = False
        time.sleep(4)
        if self.is_connect:
            self.server.close()
        self.join(10)
        if self.isAlive():
            debug_message.print_message("Can't stop ManagmentBoard service")
        else:
            debug_message.print_message('ManagmentBoard service stopped')

    def init_connect(self):
        if self.is_connect:
            self.server.reset_output_buffer()
            self.state_init = False
            if self.options['state_init_enable']:
                self.state_init = True
            self.write_data('WAKE')
            self.server.reset_input_buffer()
            self.write_data('PHER_ON')
            if self.options['wdt_enable']:
                self.write_data('WDT_ON')
            else:
                self.write_data('WDT_OFF')
            if self.options['open_sensor_enable']:
                self.write_data('DV_EN')
            else:
                self.write_data('DV_DIS')
            self.write_data('LIGHT_ON')
            self.write_data('RED')
            if self.options['enter_level'] == 'high':
                self.write_data('SPIN1=1')
            else:
                self.write_data('SPIN1=0')
            if self.options['exit_level'] == 'high':
                self.write_data('SPIN2=1')
            else:
                self.write_data('SPIN2=0')
            if self.options['unblock_level'] == 'high':
                self.write_data('SPIN3=1')
            else:
                self.write_data('SPIN3=0')
            self.ready_set = 'PIN4 0'
            self.ready_unset = 'PIN4 1'
            if self.options['ready_level'] == 'high':
                self.ready_set = 'PIN4 1'
                self.ready_unset = 'PIN4 0'
            self.passed_set = 'PIN5 0'
            if self.options['pass_level'] == 'high':
                self.passed_set = 'PIN5 1'
            self.error_set = 'PIN6 0'
            self.error_unset = 'PIN6 1'
            if self.options['error_level'] == 'high':
                self.error_set = 'PIN6 1'
                self.error_unset = 'PIN6 0'
            self.write_data('PIN1_OFF')
            self.write_data('PIN2_OFF')
            self.write_data('PIN3_OFF')
            if self.is_master:
                if not self.options['ready_enable']:
                    self.write_data('PIN4_DIS')
                    self.ready = True
                    self.turnstile = True
                else:
                    self.write_data('PIN4_EN')
                    self.mb_init_state = True
                if not self.options['error_enable']:
                    self.error = False
                    self.write_data('PIN6_DIS')
                else:
                    self.write_data('PIN6_EN')
                if self.options['error_enable'] and self.options['error_pass']:
                    self.error = False
            else:
                self.write_data('PIN4_DIS')
                self.write_data('PIN5_DIS')
                self.write_data('PIN6_DIS')
                self.error = False
                self.ready = True
                self.turnstile = True
                self.mb_init_state = False

    def read_config(self):
        debug_message.print_message('Application path: ' + self.app_path)
        config = ConfigParser.ConfigParser()
        config.read(self.app_path + '/mb.ini')
        options = config.options('AccessPointSection')
        config_options = [
         'output', 'enter', 'enter_level', 'exit', 'exit_level', 'unblock', 'unblock_level',
         'ready', 'ready_level', 'pass', 'pass_level', 'error', 'error_level', 'time_period',
         'time_tick', 'port', 'baudrate', 'port_timeout', 'repeat', 'type', 'mode', 'ready_enable',
         'error_enable', 'wdt_enable', 'open_sensor_enable', 'error_pass', 'state_init_enable', 'unblock_ab']
        for option in options:
            if option == 'repeat':
                self.options[option] = config.getboolean('AccessPointSection', option)
            elif option == 'ready_enable':
                self.options[option] = config.getboolean('AccessPointSection', option)
            elif option == 'error_enable':
                self.options[option] = config.getboolean('AccessPointSection', option)
            elif option == 'wdt_enable':
                self.options[option] = config.getboolean('AccessPointSection', option)
            elif option == 'open_sensor_enable':
                self.options[option] = config.getboolean('AccessPointSection', option)
            elif option == 'beep_enable':
                self.options[option] = config.getboolean('AccessPointSection', option)
            elif option == 'beep_usb':
                self.options[option] = config.getboolean('AccessPointSection', option)
            elif option == 'time_period':
                self.options[option] = config.getfloat('AccessPointSection', option)
            elif option == 'time_tick':
                self.options[option] = config.getint('AccessPointSection', option)
            elif option == 'error_pass':
                self.options[option] = config.getboolean('AccessPointSection', option)
            elif option == 'state_init_enable':
                self.options[option] = config.getboolean('AccessPointSection', option)
            elif option == 'unblock_ab':
                self.options[option] = config.getboolean('AccessPointSection', option)
            else:
                self.options[option] = config.get('AccessPointSection', option)

        debug_message.print_message(self.options)
        self.is_config = True
        for candidate in config_options:
            if candidate not in self.options:
                self.is_config = False

    def init_state(self):
        if not self.mb_init_state:
            return
        debug_message.print_message('============Init state===============')
        if self.is_master:
            if not self.online or not self.mb_ready or self.error:
                debug_message.print_message('\tMB not ready')
            elif self.ready:
                debug_message.print_message('\tMB ready')
                self.write_data('TL_OFF')
                self.mb_init_state = False
            else:
                self.get_state()
                if self.options['type'] == 'servo':
                    debug_message.print_message('\ttype servo waiting 20 seconds')
                    time.sleep(20)
                self.get_state()
                self.normal_mode()
                self.mb_init_state_count += 1
                if self.mb_init_state_count == 5:
                    self.mb_init_state = False
                    debug_message.print_message('\tMB 5 resetting turnstile limits ending')
                if self.ready:
                    debug_message.print_message('\tMB ready')
                    self.write_data('TL_OFF')
                    self.mb_init_state = False
        else:
            debug_message.print_message('\tMB ready')
            self.write_data('TL_OFF')
            self.mb_init_state = False
        debug_message.print_message('============!Init state==============')

    def free_mode(self):
        if self.is_connect:
            if self.ready:
                self.exec_command('UNBLOCK')
            else:
                debug_message.print_message('AP already in the free mode now')

    def normal_mode(self):
        if self.is_connect:
            debug_message.print_message('\tGoing to normal mode')
            if not self.ready or not self.options['ready_enable']:
                self.exec_command('BLOCK')
            elif self.ready and self.direction_state == StateTypes.OPEN:
                self.exec_command('BLOCK')
            else:
                debug_message.print_message('AP already in the normal mode now')

    def enter_mode(self):
        debug_message.print_message('=============MB in enter mode===============')
        self.exec_command('ENTER')
        debug_message.print_message('=============!MB in enter mode==============')

    def exit_mode(self):
        debug_message.print_message('=============MB in exit mode===============')
        self.exec_command('EXIT')
        debug_message.print_message('=============!MB in exit mode==============')

    def get_state(self):
        if self.is_connect:
            _time_start = time.time()
            self.exec_command('STATE')
            time.sleep(self.options['time_period'])
            debug_message.print_message('STATE COMMAND --- %s seconds ---' % (time.time() - _time_start))

    def check_state(self):
        pass

    def update_config(self):
        self.read_config()
        if self.is_connect:
            self.server.close()

    def parse_data(self, _data):
        if self.reset_device in _data:
            self.init_reset_device()
        elif _data.startswith(self.version):
            split_data = _data.split(' ')
            if len(split_data) == 2 and isinstance(split_data[1], basestring):
                self.current_version = split_data[1]
        elif _data.startswith(self.temp_set):
            split_data = _data.split(' ')
            if len(split_data) == 2 and isinstance(split_data[1], basestring):
                self.temperature = split_data[1]
        if self.is_master:
            if _data.startswith('PIN4 '):
                split_data = _data.strip().split(' ')
                if len(split_data) == 2 and isinstance(split_data[1], str):
                    _tmp = list(self.pin_data)
                    _tmp[1] = '0'
                    if split_data[1] == '1':
                        _tmp[1] = '1'
                    self.pin_data = ('').join(_tmp)
            elif _data.startswith('PIN5 '):
                split_data = _data.strip().split(' ')
                if len(split_data) == 2 and isinstance(split_data[1], str):
                    _tmp = list(self.pin_data)
                    _tmp[2] = '0'
                    if split_data[1] == '1':
                        _tmp[2] = '1'
                    self.pin_data = ('').join(_tmp)
            elif _data.startswith('PIN6 '):
                split_data = _data.strip().split(' ')
                if len(split_data) == 2 and isinstance(split_data[1], str):
                    _tmp = list(self.pin_data)
                    _tmp[3] = '0'
                    if split_data[1] == '1':
                        _tmp[3] = '1'
                    self.pin_data = ('').join(_tmp)
            if self.options['error_pass']:
                if self.error_set in _data:
                    _data = _data.replace('PIN6', 'PIN5')
                elif self.error_unset in _data:
                    _data = _data.replace('PIN6', 'PIN5')
            if self.passed_set in _data:
                if self.state_init:
                    self.passed = False
                    self.state_init = False
                else:
                    self.passed = True
            if self.ready_unset in _data:
                if self.options['ready_enable'] and self.direction_state != StateTypes.OPEN:
                    self.ready = False
            elif self.ready_set in _data:
                self.ready = True
                self.turnstile = True
                if self.mb_init_state:
                    self.mb_init_state = False
            elif self.error_unset in _data:
                self.error = False
            elif self.error_set in _data:
                if self.options['error_enable'] and not self.options['error_pass']:
                    self.error = True
            elif self.alarm_unset in _data:
                if self.cur_open_sensor_state:
                    self.cur_open_sensor_state = False
                    self.is_alarm = False
                    self.is_open_sensor = False
            elif self.alarm_set in _data:
                if not self.cur_open_sensor_state:
                    self.cur_open_sensor_state = True
                    self.is_open_sensor = True
                    self.beep()
                    if self.options['open_sensor_enable']:
                        self.is_alarm = True
        elif self.alarm_unset in _data:
            if self.cur_open_sensor_state:
                self.cur_open_sensor_state = False
                self.is_alarm = False
                self.is_open_sensor = False
        elif self.alarm_set in _data:
            if not self.cur_open_sensor_state:
                self.cur_open_sensor_state = True
                self.is_open_sensor = True
                self.beep()
                if self.options['open_sensor_enable']:
                    self.is_alarm = True

    def read_data(self):
        _data = ''
        self.passed = False
        self.passed_local = False
        while self.online:
            if self.is_config:
                try:
                    if self.server and self.server.is_open:
                        if mb_write_lock.locked():
                            time.sleep(0.03)
                            continue
                        while self.server.in_waiting > 0:
                            _data = self.server.read(self.server.in_waiting)

                        if _data:
                            debug_message.print_message('-------------------MB DATA-----------------------')
                            debug_message.print_message(_data)
                            debug_message.print_message(_data.splitlines())
                            _data_list = _data.splitlines()
                            debug_message.print_message('-------------------!MB DATA----------------------')
                            if not self.mb_ready:
                                self.mb_ready = True
                            if isinstance(_data_list, list) and _data_list:
                                for _rec in _data_list:
                                    self.parse_data(_rec)

                            _data = ''
                    else:
                        debug_message.print_message('Is open ' + str(self.server.is_open))
                        debug_message.print_message('No server or port is not open')
                        self.reconnect()
                except serial.SerialException as se:
                    debug_message.print_message(se)
                    debug_message.print_message('Serial Exception0')
                    self.reconnect()
                except Exception as ex:
                    debug_message.print_message(ex)
                    debug_message.print_message('MB Exception in read data')

            time.sleep(0.03)

    def reconnect(self):
        debug_message.print_message('trying to reconnect to MB')
        self.state = StateTypes.INIT
        time.sleep(10)
        if not mb_lock.locked():
            self.open_port()
            self.init_connect()
        if self.state == StateTypes.INIT:
            self.state = StateTypes.READING

    def is_ready(self):
        return self.is_config and self.ready and not self.error

    def is_online(self):
        if not self.is_connect or not self.mb_ready:
            return False
        return True

    def is_main_online(self):
        if not self.is_connect or not self.mb_ready or self.error:
            return False
        return True

    def is_turnstile(self):
        return self.turnstile

    def is_turnstile_monitor(self):
        return self.turnstile and not self.error and self.is_ready_monitor()

    def is_ready_monitor(self):
        return self.ready or self.direction_state == StateTypes.OPEN

    def get_pin_data(self):
        return self.pin_data

    def get_lock(self):
        return add_lock.locked() or waiting_lock.locked() or cards_lock.locked() or common_lock.locked()

    def start_read_barcode(self):
        pass

    def stop_read_barcode(self):
        pass

    def start_warming(self):
        self.exec_command('HEATER_ON')

    def is_usb_beep(self):
        return self.options['beep_enable'] and self.options['beep_usb']

    def beep(self):
        if self.options['beep_enable'] and not self.options['beep_usb']:
            self.exec_command('BEEP')

    def reset_open_sensor(self):
        self.exec_command('A_RST')

    def stop_warming(self):
        self.exec_command('HEATER_OFF')

    def reboot_device(self):
        self.exec_command('RESET')

    def reboot_pher(self):
        self.exec_command('WDT_ON')
        self.reset_pher = True

    def exec_command(self, command):
        if self.reset_pher:
            return
        if self.state == StateTypes.INIT:
            return
        if mb_lock.locked() and (command == 'TEMP' or command == 'STATE'):
            return
        while mb_lock.locked():
            time.sleep(0.05)

        debug_message.print_message('Command: ' + command)
        if not self.is_connect:
            debug_message.print_message('----------MB not ready--------------')
            return
        with mb_lock:
            if command == 'ENTER':
                if self.is_ready():
                    self.direction_state = StateTypes.OPEN
                    self.in_waiting = True
                    if self.point_direction == DirectionTypes.ENTER:
                        self.write_data('GREEN')
                    if self.is_master:
                        if self.options['mode'] == 'normal':
                            self.write_data('PIN1_ON')
                        else:
                            self.write_data('PIN2_ON')
                        if self.options['output'] == 'pulsed':
                            time.sleep(self.options['time_period'])
                            if self.options['mode'] == 'normal':
                                self.write_data('PIN1_OFF')
                            else:
                                self.write_data('PIN2_OFF')
                    self.wait_pass()
                    self.write_data('TL_OFF')
                    if self.is_master:
                        if self.options['output'] == 'potential':
                            if self.options['mode'] == 'normal':
                                self.write_data('PIN1_OFF')
                            else:
                                self.write_data('PIN2_OFF')
                        if self.options['repeat'] and self.options['output'] == 'pulsed':
                            if self.options['mode'] == 'normal':
                                self.write_data('PIN1_ON')
                            else:
                                self.write_data('PIN2_ON')
                            time.sleep(self.options['time_period'])
                            if self.options['mode'] == 'normal':
                                self.write_data('PIN1_OFF')
                            else:
                                self.write_data('PIN2_OFF')
                    self.in_waiting = False
                    self.direction_state = StateTypes.BLOCK
            elif command == 'EXIT':
                if self.is_ready():
                    self.direction_state = StateTypes.OPEN
                    self.in_waiting = True
                    if self.point_direction == DirectionTypes.EXIT:
                        self.write_data('GREEN')
                    if self.is_master:
                        if self.options['mode'] == 'normal':
                            self.write_data('PIN2_ON')
                        else:
                            self.write_data('PIN1_ON')
                        if self.options['output'] == 'pulsed':
                            time.sleep(self.options['time_period'])
                            if self.options['mode'] == 'normal':
                                self.write_data('PIN2_OFF')
                            else:
                                self.write_data('PIN1_OFF')
                    self.wait_pass()
                    self.write_data('TL_OFF')
                    if self.is_master:
                        if self.options['output'] == 'potential':
                            if self.options['mode'] == 'normal':
                                self.write_data('PIN2_OFF')
                            else:
                                self.write_data('PIN1_OFF')
                        if self.options['repeat'] and self.options['output'] == 'pulsed':
                            if self.options['mode'] == 'normal':
                                self.write_data('PIN2_ON')
                            else:
                                self.write_data('PIN1_ON')
                            time.sleep(self.options['time_period'])
                            if self.options['mode'] == 'normal':
                                self.write_data('PIN2_OFF')
                            else:
                                self.write_data('PIN1_OFF')
                    self.in_waiting = False
                    self.direction_state = StateTypes.BLOCK
            elif command == 'UNBLOCK':
                if not self.error:
                    self.direction_state = StateTypes.OPEN
                    self.in_waiting = True
                    if self.is_master:
                        if self.options['output'] == 'potential':
                            if self.options['unblock_ab']:
                                self.write_data('PIN1_ON')
                                self.write_data('PIN2_ON')
                            else:
                                self.write_data('PIN3_ON')
                        elif self.options['output'] == 'pulsed':
                            if self.options['unblock_ab']:
                                self.write_data('PIN1_ON')
                                self.write_data('PIN2_ON')
                                time.sleep(self.options['time_period'])
                                self.write_data('PIN1_OFF')
                                self.write_data('PIN2_OFF')
                            else:
                                self.write_data('PIN3_ON')
                                time.sleep(self.options['time_period'])
                                self.write_data('PIN3_OFF')
                    self.in_waiting = False
            elif command == 'BLOCK':
                if not self.error:
                    self.direction_state = StateTypes.BLOCK
                    self.in_waiting = True
                    if self.is_master:
                        if self.options['output'] == 'potential':
                            if self.options['unblock_ab']:
                                self.write_data('PIN1_OFF')
                                self.write_data('PIN2_OFF')
                            else:
                                self.write_data('PIN3_OFF')
                        elif self.options['output'] == 'pulsed':
                            if self.options['unblock_ab']:
                                self.write_data('PIN1_ON')
                                self.write_data('PIN2_ON')
                                time.sleep(self.options['time_period'])
                                self.write_data('PIN1_OFF')
                                self.write_data('PIN2_OFF')
                            else:
                                self.write_data('PIN3_ON')
                                time.sleep(self.options['time_period'])
                                self.write_data('PIN3_OFF')
                        if self.options['type'] == 'servo':
                            self.write_data('STATE')
                            time.sleep(20)
                            self.write_data('STATE')
                    self.in_waiting = False
            elif command == 'STATE':
                self.write_data('STATE')
            elif command == 'TL_OFF':
                self.write_data('TL_OFF')
            elif command == 'RED':
                self.write_data('RED')
            elif command == 'GREEN':
                self.write_data('GREEN')
            elif command == 'TEMP':
                self.write_data('TEMP')
            elif command == 'TRIG_ON':
                self.write_data('TRIG_ON')
            elif command == 'TRIG_OFF':
                self.write_data('TRIG_OFF')
            elif command == 'HEATER_ON':
                self.write_data('HEATER_ON')
            elif command == 'HEATER_OFF':
                self.write_data('HEATER_OFF')
            elif command == 'RESET':
                self.write_data('RESET')
            elif command == 'A_RST':
                self.write_data('A_RST')
            elif command == 'WDT_ON':
                self.write_data('WDT_ON')
            elif command == 'WDT_OFF':
                self.write_data('WDT_OFF')
            elif command == 'DV_EN':
                self.write_data('DV_EN')
            elif command == 'DV_DIS':
                self.write_data('DV_DIS')
            elif command == 'BEEP':
                self.write_data('BEEP100')
            elif command == 'TRIG_CIRCLE':
                self.write_data('TRIG_OFF')
                self.write_data('TRIG_ON')

    def write_data(self, data):
        if self.is_connect:
            while mb_write_lock.locked():
                time.sleep(0.05)

            with mb_write_lock:
                if data != 'TEMP' and data != 'STATE':
                    com_time_start = time.time()
                    debug_message.print_message('----------------Execute command: ' + data + '-----------------')
                try:
                    self.server.write(data + '\r')
                    if data == 'PHER_ON':
                        time.sleep(5)
                    else:
                        time.sleep(0.05)
                except serial.SerialException as se:
                    debug_message.print_message(se)
                    debug_message.print_message('Serial Exception1')

                if data != 'TEMP' and data != 'STATE':
                    debug_message.print_message('--- %s seconds ---' % (time.time() - com_time_start))
                    debug_message.print_message('----------------!Execute command: ' + data + '----------------')

    def wait_pass(self):
        debug_message.print_message('=========Mb Going to pass circle===============')
        debug_message.print_message('time to wait is: ' + str(self.options['time_tick']))
        self.passed = False
        self.passed_local = False
        time_tick = 0
        while True:
            if self.passed:
                self.passed_local = True
                debug_message.print_message('======Passed caught up==========')
                break
            if time_tick >= self.options['time_tick']:
                break
            time.sleep(0.1)
            time_tick += 0.1

        self.passed = False
        debug_message.print_message('=========Mb Out from pass circle===============')

    def init_reset_device(self):
        debug_message.print_message('-------Resetting interface------------')
        def_config = os.path.join(self.app_path, 'defaults', 'rc.conf')
        sys_config = os.path.join('/etc/rc.d', 'rc.conf')
        def_zeus_ini = os.path.join(self.app_path, 'defaults', 'zeus.ini')
        sys_zeus_ini = os.path.join(self.app_path, 'zeus.ini')
        if not os.path.isfile(def_config) or not os.path.isfile(def_zeus_ini):
            return False
        with open(def_config, 'rb') as (_fp):
            f_data = _fp.read()
            with open(sys_config, 'wb') as (_fpw):
                _fpw.write(f_data)
            os.chmod(sys_config, 420)
        with open(def_zeus_ini, 'rb') as (_fp):
            f_data = _fp.read()
            with open(sys_zeus_ini, 'wb') as (_fpw):
                _fpw.write(f_data)
            os.chmod(sys_zeus_ini, 420)
        os.system('sync')
        self.reboot_pher()
        debug_message.print_message('--------!Resetting interface------------')

    def get_version(self):
        return self.current_version

    def get_temperature(self):
        return self.temperature

    def get_alarm(self):
        return self.is_alarm

    def get_open_sensor(self):
        return self.is_open_sensor

    def get_options(self):
        return self.options

    def save_options(self, params):
        params_options = [
         'output', 'type', 'mode', 'enter_level', 'exit_level', 'unblock_level', 'unblock_ab',
         'ready_level', 'ready_enable', 'pass_level', 'error_level', 'error_enable', 'error_pass',
         'wdt_enable', 'open_sensor_enable', 'beep_enable', 'beep_usb', 'state_init_enable',
         'time_tick']
        for _option in params_options:
            if _option not in params:
                return False

        config = ConfigParser.ConfigParser()
        config.read(self.app_path + '/mb.ini')
        _output = 'pulsed'
        _type = 'servo'
        _mode = 'normal'
        _enter_level = 'high'
        _exit_level = 'high'
        _unblock_level = 'high'
        _unblock_ab = False
        _ready_level = 'high'
        _ready_enable = False
        _pass_level = 'high'
        _error_level = 'high'
        _error_enable = False
        _error_pass = False
        _wdt_enable = False
        _open_sensor_enable = False
        _beep_enable = False
        _beep_usb = False
        _state_init_enable = False
        if params['output'][0] == '2':
            _output = 'potential'
        if params['type'][0] == '2':
            _type = 'mech'
        if params['mode'][0] == '2':
            _mode = 'reverse'
        if params['enter_level'][0] == '1':
            _enter_level = 'low'
        if params['exit_level'][0] == '1':
            _exit_level = 'low'
        if params['unblock_level'][0] == '1':
            _unblock_level = 'low'
        if params['unblock_ab'][0] == 'true':
            _unblock_ab = True
        if params['ready_level'][0] == '1':
            _ready_level = 'low'
        if params['ready_enable'][0] == 'true':
            _ready_enable = True
        if params['pass_level'][0] == '1':
            _pass_level = 'low'
        if params['error_level'][0] == '1':
            _error_level = 'low'
        if params['error_enable'][0] == 'true':
            _error_enable = True
        if params['error_pass'][0] == 'true':
            _error_pass = True
        if params['wdt_enable'][0] == 'true':
            _wdt_enable = True
        if params['open_sensor_enable'][0] == 'true':
            _open_sensor_enable = True
        if params['beep_enable'][0] == 'true':
            _beep_enable = True
        if params['beep_usb'][0] == 'true':
            _beep_usb = True
            _beep_enable = True
        if params['state_init_enable'][0] == 'true':
            _state_init_enable = True
        config.set('AccessPointSection', 'output', _output)
        config.set('AccessPointSection', 'type', _type)
        config.set('AccessPointSection', 'mode', _mode)
        config.set('AccessPointSection', 'enter_level', _enter_level)
        config.set('AccessPointSection', 'exit_level', _exit_level)
        config.set('AccessPointSection', 'unblock_level', _unblock_level)
        config.set('AccessPointSection', 'unblock_ab', _unblock_ab)
        config.set('AccessPointSection', 'ready_enable', _ready_enable)
        config.set('AccessPointSection', 'ready_level', _ready_level)
        config.set('AccessPointSection', 'pass_level', _pass_level)
        config.set('AccessPointSection', 'error_level', _error_level)
        config.set('AccessPointSection', 'error_enable', _error_enable)
        config.set('AccessPointSection', 'error_pass', _error_pass)
        config.set('AccessPointSection', 'time_tick', params['time_tick'][0])
        config.set('AccessPointSection', 'wdt_enable', _wdt_enable)
        config.set('AccessPointSection', 'open_sensor_enable', _open_sensor_enable)
        config.set('AccessPointSection', 'beep_enable', _beep_enable)
        config.set('AccessPointSection', 'beep_usb', _beep_usb)
        config.set('AccessPointSection', 'state_init_enable', _state_init_enable)
        with open(self.app_path + '/mb.ini', 'wb') as (configfile):
            config.write(configfile)
        os.system('sync')
        self.reboot_pher()
        return True

    def get_option(self, _key, _default=None):
        if _key in self.options:
            return self.options[_key]
        else:
            return _default

    def set_option(self, _key, _value):
        try:
            self.options[_key] = _value
        except Exception as e:
            debug_message.print_message('--------MB set option ' + _key + ' error--------')
            debug_message.print_message(e)
            debug_message.print_message('--------!MB set option ' + _key + ' error-------')
# okay decompiling /home/a/Desktop/app/ManagmentBoard.pyc
