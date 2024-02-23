# uncompyle6 version 3.4.0
# Python bytecode 2.7 (62211)
# Decompiled from: Python 2.7.15+ (default, Jul  9 2019, 16:51:35) 
# [GCC 7.4.0]
# Embedded file name: /home/user/zeus/Barcode.py
# Compiled at: 2018-05-28 13:44:40
import threading, logging, usb.core, usb.util, usb.backend.libusb1, time, struct, subprocess, sys, os, Queue
from DebugImport import debug_message
from CardHolder import CardHolder
from multiprocessing import Queue as qe
from Models import QueueData
logger = logging.getLogger('zeus')
VENDOR_ID = 1504
PRODUCT_ID = 6400
PRODUCT_ID_KEYBOARD = 4608
DISABLE_READ_PARAMS_BARCODE = '\xec\x00'
DISABLE_SCANNER = '\x06\x00'
ENABLE_SCANNER = '\x06\x01'
SNAPI_BARCODE_REQ = '\x01"\x01\x00'
SNAPI_SETUP = '\x80\x02\x00\x01'
SNAPI_PARAMS_DEFAULT = '\t\x00'
SNAPI_PULL_TRIGGER = '\n\x01'
SNAPI_RELEASE_TRIGGER = '\n\x00'
SNAPI_STATE_READ = 0
SNAPI_STATE_COMMAND = 1
SNAPI_STATE_DATA = 2
SNAPI_PARAMS_DEFAULT_SET = '\x01$\x01\x00'
SNAPI_POWER_MODE = '\x0b\x81\x02\x00\x80\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
SNAPI_TRIGGER_MODE = '\x0b\x81\x02\x00\x8a\x00\x07\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
SNAPI_2OF5_ENABLE = '\x0b\x81\x02\x00\x16\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
SNAPI_2OF5L_ENABLE = '\x0b\x81\x02\x00\x17\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
SNAPI_READ_BEEP_OFF = '\x0b\x81\x02\x008\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
SNAPI_SCANNING_PARAMS_OFF = '\x0b\x81\x02\x00\xec\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
SNAPI_SCANNING_PARAMS_OFF1 = '\x06\x01\x02\x008\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
SNAPI_MOBILE_READ_ON = '\x0b\x81\x02\x00\xf1\xcc\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
SNAPI_MOBILE_READ_ON1 = '\x0b\x81\x02\x00\xcc\x02\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
SNAPI_BEEP = '\r@\x00\t\x00\t\x05\x00\x17pX\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
SNAPI_IMAGE_JPG = '\x0b\x01\x02\x000\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
SNAPI_RET0 = "\x01'\x01\x00"
SNAPI_COMMAND_1 = '\r@\x00\x06\x00\x06\x02\x00N$\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
SNAPI_COMMAND_N = '\r@\x00\x04\x00\x04\x10\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
SNAPI_INIT_1 = '\r@\x00\x06\x00\x06 \x00\x04\xb0\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'

class Barcode(object):

    def __init__(self, app_path, inputqe, outputqe, readeq):
        self.port = None
        self.app_path = app_path
        self.client = None
        self.online = True
        self.is_connect = False
        self.thread_w = None
        self.endpoint = None
        self.device = None
        self.state = SNAPI_STATE_READ
        self.first_run = True
        self.run_once = False
        self.thread_w = None
        self.error_count = 0
        self.error_count_dio = 0
        self.inputqe = inputqe
        self.outputqe = outputqe
        self.readeq = readeq
        self.is_active_change = False
        self.barcode_type = {6: 0, 3: 0}
        self.prev_state = True
        self.options = {}
        return

    def usb_send(self, _bm_request_type, _b_request, _value, _index, _data_length, _timeout=100, _exception=True):
        if not self.is_connected():
            debug_message.print_message("Device is't connected")
            return False
        try:
            _ret = self.device.ctrl_transfer(bmRequestType=_bm_request_type, bRequest=_b_request, wValue=_value, wIndex=_index, data_or_wLength=_data_length, timeout=_timeout)
        except usb.core.USBError as e:
            debug_message.print_message(e)
            if _exception:
                self.close_connection()
            return False
        except Exception as e1:
            debug_message.print_message(e1)
            return False

        if _ret:
            debug_message.print_message(_ret)
            if isinstance(_ret, int):
                if isinstance(_data_length, int):
                    debug_message.print_message('Command (without data) status received')
                elif len(_data_length) == _ret:
                    debug_message.print_message('Command status received')
            else:
                debug_message.print_message('Command data received')
                try:
                    for _x in _ret:
                        debug_message.print_message(('{0:3} | {1:4} | {2:3}').format(str(_x), str(hex(ord(chr(_x)))), str(chr(_x))))

                except Exception as e:
                    debug_message.print_message('Exception:')
                    debug_message.print_message(e)

        return _ret

    def decrypt_data(self, _data):
        data_decode = ''
        try:
            if _data and len(_data) == 32 and _data[0] == 34 and _data[1] == 1:
                debug_message.print_message('Barcode HEX data: %s' % ('').join([ hex(ord(chr(x))) + ' ' for x in _data ]))
                debug_message.print_message('-----------------Barcode received-----------------')
                self.code_received()
                debug_message.print_message('-----------------!Barcode received-----------------')
                data_decode = ('').join(map(chr, _data[6:_data[3] + 6]))
                debug_message.print_message('Barcode data decode: %s' % data_decode)
                _barcode_length = {k:v for k, v in self.barcode_type.items() if v > 0}
                _barcode_type = _data[4]
                if _barcode_length:
                    if self.get_barcode_length(_barcode_type) is None or len(data_decode) != self.get_barcode_length(_barcode_type):
                        debug_message.print_message('Barcode length not much with: ' + str(self.get_barcode_length(_barcode_type)))
                        data_decode = ''
            elif _data:
                debug_message.print_message('----------------------------------------------------------')
                debug_message.print_message('Read: (%d bytes)' % len(_data))
                debug_message.print_message('Barcode HEX: %s' % ('').join([ hex(ord(chr(x))) + ' ' for x in _data ]))
                debug_message.print_message('!---------------------------------------------------------')
        except Exception as e:
            debug_message.print_message(e)
            data_decode = ''

        return data_decode

    def device_read(self, _timeout=200, _repeat=0):
        if not self.is_connected():
            debug_message.print_message("Device is't connected")
            return ''
        try:
            _data = self.device.read(self.endpoint.bEndpointAddress, self.endpoint.wMaxPacketSize, _timeout)
            _data = self.decrypt_data(_data)
        except usb.core.USBError as e:
            _data = ''
            if e.errno != 110:
                debug_message.print_message(e)
                self.close_connection()
            elif _repeat:
                debug_message.print_message('\tRepeat device read')
                if _repeat > 0:
                    _repeat -= 1
                self.device_read(_timeout=_timeout, _repeat=_repeat)
        except Exception as e1:
            _data = ''
            debug_message.print_message(e1)

        return _data

    def get_queue(self):
        if not self.inputqe.empty():
            try:
                _data = self.inputqe.get(False)
            except Queue.Empty as queue_error:
                _data = None

            if isinstance(_data, QueueData):
                debug_message.print_message('-----------Barcode receive data-------------')
                debug_message.print_message('\t' + _data.command)
                debug_message.print_message(_data.value)
                if _data.command == 'options' and isinstance(_data.value, dict) and _data.value:
                    if 'key' in _data.value and 'value' in _data.value:
                        debug_message.print_message('Set barcode key: ' + _data.value['key'])
                        debug_message.print_message(_data.value['value'])
                        self.set_option_vcheck(_data.value['key'], _data.value['value'])
                elif _data.command == 'exit':
                    self.exit()
        return

    def read_data(self):
        while self.online:
            self.get_queue()
            if self.get_status():
                self.outputqe.put(QueueData('barcode', {'status': self.is_online()}))
            if self.is_snapi_connected():
                _data = self.device_read()
                if self.first_run:
                    self.first_run = False
                    if self.get_active():
                        self.enable()
                    else:
                        self.disable()
                if self.is_active_change:
                    self.is_active_change = False
                    if self.get_active():
                        self.enable()
                    else:
                        self.disable()
                if len(_data) > 7 and self.can_send_data():
                    debug_message.print_message('-------------------------IN BARCODE READ LOOP--------------------------')
                    if self.can_send_data():
                        self.set_send_data(False)
                        self.readeq.put(QueueData('barcode', _data))
                    debug_message.print_message('-------------------------!IN BARCODE READ LOOP-------------------------')
                time.sleep(0.05)
            else:
                self.first_run = True
                self.connect()
                self.init_reader()

        debug_message.print_message('Out from read_data circle')

    def code_received(self):
        self.set_param(SNAPI_BARCODE_REQ)

    def get_interface(self):
        self.usb_send(161, 1, 768, 0, 9)

    def set_snapi_interface(self):
        self.usb_send(33, 9, 768, 0, SNAPI_SETUP)
        time.sleep(10)

    def disable_params_read(self):
        self.set_param(DISABLE_READ_PARAMS_BARCODE)

    def set_snapi_params_default(self):
        """
        First step of barcode initialize process
        """
        debug_message.print_message('----------Set default params--------')
        self.change_state(SNAPI_STATE_COMMAND)
        self.set_param(SNAPI_PARAMS_DEFAULT, 300)
        self.device_read()
        self.set_param(SNAPI_PARAMS_DEFAULT_SET, 300)
        self.set_param(SNAPI_PARAMS_DEFAULT_SET, 300)
        self.set_param(SNAPI_PARAMS_DEFAULT_SET, 300)
        self.set_param(SNAPI_PARAMS_DEFAULT_SET, 300)
        self.set_param(ENABLE_SCANNER)
        self.change_state(SNAPI_STATE_READ)
        time.sleep(10)
        debug_message.print_message('----------!Set default params-------')

    def set_snapi_power_mode(self):
        """
        Second step of barcode initialize process
        """
        debug_message.print_message('----------Set power mode------------')
        self.change_state(SNAPI_STATE_COMMAND)
        self.set_param(SNAPI_POWER_MODE, 300)
        self.set_param(ENABLE_SCANNER, 300)
        self.change_state(SNAPI_STATE_READ)
        time.sleep(3)
        debug_message.print_message('----------!Set power mode-----------')

    def set_snapi_trigger_mode(self):
        """
        Third step of barcode initialize process
        """
        debug_message.print_message('----------Set trigger mode----------')
        self.change_state(SNAPI_STATE_COMMAND)
        self.set_param(SNAPI_TRIGGER_MODE, 300)
        self.set_param(ENABLE_SCANNER, 300)
        self.change_state(SNAPI_STATE_READ)
        time.sleep(3)
        debug_message.print_message('----------!Set trigger mode---------')

    def set_snapi_pull_trigger(self):
        """
        Fourth step of barcode initialize process
        """
        debug_message.print_message('----------Set pull trigger mode-----')
        self.change_state(SNAPI_STATE_COMMAND)
        self.set_param(SNAPI_PULL_TRIGGER, 300)
        self.set_param(ENABLE_SCANNER, 300)
        self.change_state(SNAPI_STATE_READ)
        time.sleep(3)
        debug_message.print_message('----------!Set pull trigger mode----')

    def set_snapi_2of5(self):
        """
        Five step of barcode initialize process
        """
        debug_message.print_message('----------Set read 2of5 barcode-----')
        self.change_state(SNAPI_STATE_COMMAND)
        self.set_param(SNAPI_2OF5_ENABLE, 300)
        self.set_param(ENABLE_SCANNER, 300)
        self.change_state(SNAPI_STATE_READ)
        time.sleep(3)
        debug_message.print_message('----------!Set read 2of5 barcode----')

    def set_snapi_2of5_long(self):
        """
        six step of barcode initialize process
        """
        debug_message.print_message('----------Set read 2of5 long barcode-----')
        self.change_state(SNAPI_STATE_COMMAND)
        self.set_param(SNAPI_2OF5L_ENABLE, 300)
        self.set_param(ENABLE_SCANNER, 300)
        self.change_state(SNAPI_STATE_READ)
        time.sleep(3)
        debug_message.print_message('----------!Set read 2of5 long barcode----')

    def set_snapi_beep_off(self):
        """
        seven step of barcode initialize process
        """
        debug_message.print_message('----------Set beep off--------------')
        self.change_state(SNAPI_STATE_COMMAND)
        self.set_param(SNAPI_READ_BEEP_OFF, 300)
        self.set_param(ENABLE_SCANNER, 300)
        self.change_state(SNAPI_STATE_READ)
        time.sleep(3)
        debug_message.print_message('----------!Set beep off-------------')

    def set_snapi_scanning_params_off(self):
        """
        eight step of barcode initialize process
        """
        debug_message.print_message('----------Set scanning params off---')
        self.change_state(SNAPI_STATE_COMMAND)
        self.set_param(SNAPI_SCANNING_PARAMS_OFF, 300)
        self.set_param(ENABLE_SCANNER, 300)
        self.change_state(SNAPI_STATE_READ)
        time.sleep(3)
        debug_message.print_message('----------!Set scanning params off--')

    def set_snapi_mobile_read_on(self):
        """
        nine step of barcode initialize process
        """
        debug_message.print_message('----------Set mobile read-----------')
        self.change_state(SNAPI_STATE_COMMAND)
        self.set_param(SNAPI_MOBILE_READ_ON1, 300)
        self.set_param(ENABLE_SCANNER, 300)
        self.change_state(SNAPI_STATE_READ)
        time.sleep(3)
        debug_message.print_message('----------!Set mobile read----------')

    def init_snapi_params_default(self):
        self.set_snapi_power_mode()
        self.set_snapi_trigger_mode()
        self.set_snapi_pull_trigger()
        self.set_snapi_2of5()
        self.set_snapi_2of5_long()
        self.set_snapi_beep_off()
        self.set_snapi_scanning_params_off()
        self.set_snapi_mobile_read_on()

    def change_state(self, _state):
        if self.state != _state:
            self.state = _state
            time.sleep(0.01)

    def pull_trigger(self):
        self.change_state(SNAPI_STATE_COMMAND)
        self.set_param(SNAPI_PULL_TRIGGER, 300)
        self.device_read()
        self.change_state(SNAPI_STATE_READ)

    def set_param(self, _data, _timeout=100, _exception=True):
        byte_array = bytearray()
        parameter = _data[0]
        byte_array.append(2)
        byte_array.append(parameter)
        send_value = ('').join(map(chr, byte_array))
        send_value = struct.unpack('>H', send_value)[0]
        self.usb_send(33, 9, send_value, 0, _data.__str__(), _timeout, _exception)

    def beep(self):
        _count_tmp = 0
        if not self.is_connected():
            debug_message.print_message('--Barcode reader not connected---')
            return
        self.change_state(SNAPI_STATE_COMMAND)
        self.set_param(SNAPI_BEEP, 300, _exception=False)
        self.device_read()
        self.device_read()
        self.set_param(SNAPI_RET0, _exception=False)
        self.device_read()
        self.change_state(SNAPI_STATE_READ)

    def init_command_1(self):
        debug_message.print_message('---------Init command 1------')
        self.change_state(SNAPI_STATE_COMMAND)
        self.set_param(SNAPI_COMMAND_1, 300)
        self.device_read()
        self.device_read()
        self.set_param(SNAPI_RET0)
        self.device_read()
        self.set_param(SNAPI_RET0)
        self.change_state(SNAPI_STATE_READ)
        debug_message.print_message('---------!Init command 1-----')

    def init_command_n(self):
        self.change_state(SNAPI_STATE_COMMAND)
        self.set_param(SNAPI_COMMAND_N, 300)
        self.device_read()
        self.device_read()
        self.set_param(SNAPI_RET0)
        self.change_state(SNAPI_STATE_READ)

    def init_usb(self):
        self.init_usb_0()
        self.init_usb_1()
        self.init_command_1()

    def init_usb_0(self):
        debug_message.print_message('--------Init usb--------------')
        self.change_state(SNAPI_STATE_COMMAND)
        self.usb_send(33, 10, 0, 0, 0, 300)
        self.device_read()
        self.change_state(SNAPI_STATE_READ)
        time.sleep(2)
        debug_message.print_message('--------!Init usb-------------')

    def init_usb_1(self):
        debug_message.print_message('--------Init usb 1------------')
        self.change_state(SNAPI_STATE_COMMAND)
        self.set_param(SNAPI_INIT_1, 300)
        self.device_read()
        self.device_read()
        self.set_param(SNAPI_RET0, 300)
        self.set_param(ENABLE_SCANNER, 300)
        self.device_read()
        self.change_state(SNAPI_STATE_READ)
        time.sleep(2)
        debug_message.print_message('--------!Init usb 1-----------')

    def enable(self):
        debug_message.print_message('=====BARCODE USB ENABLE==========')
        _count_tmp = 0
        if not self.is_connected():
            debug_message.print_message('--Barcode reader not connected---')
            debug_message.print_message('=====!BARCODE USB ENABLE=========')
            return
        self.change_state(SNAPI_STATE_COMMAND)
        self.change_state(SNAPI_STATE_COMMAND)
        self.device_read()
        self.device_read()
        self.set_param(ENABLE_SCANNER, 300)
        self.device_read()
        self.device_read()
        self.device_read()
        self.change_state(SNAPI_STATE_READ)
        debug_message.print_message('=====!BARCODE USB ENABLE=========')

    def disable(self):
        _count_tmp = 0
        debug_message.print_message('======BARCODE USB DISABLE=========')
        if not self.is_connected():
            debug_message.print_message('--Barcode reader not connected---')
            debug_message.print_message('=====!BARCODE USB DISABLE=========')
            return
        self.change_state(SNAPI_STATE_COMMAND)
        self.change_state(SNAPI_STATE_COMMAND)
        self.device_read()
        self.device_read()
        self.set_param(DISABLE_SCANNER, 300)
        self.device_read()
        self.device_read()
        self.device_read()
        self.device_read()
        self.device_read()
        self.device_read()
        self.device_read()
        self.device_read()
        self.device_read()
        self.change_state(SNAPI_STATE_READ)
        debug_message.print_message('=====!BARCODE USB DISABLE=========')

    def run(self):
        debug_message.print_message('Barcode usb run')
        self.set_active(True)
        self.set_send_data(True)
        self.read_data()

    def to_snapi(self):
        if self.device and self.device.idProduct != PRODUCT_ID:
            self.get_interface()
            self.set_snapi_interface()
            return True
        else:
            return False

    def is_snapi(self):
        if self.device and self.device.idProduct == PRODUCT_ID:
            return True
        else:
            return False

    def is_usbhid(self):
        if self.device and self.device.idProduct == PRODUCT_ID_KEYBOARD:
            return True
        else:
            return False

    def is_snapi_connected(self):
        return self.is_connect and self.is_snapi()

    def is_connected(self):
        return self.is_connect and self.device

    def is_online(self):
        if self.device is None:
            return False
        else:
            return self.is_snapi_connected()

    def get_status(self):
        if self.prev_state != self.is_online():
            self.prev_state = self.is_online()
            return True
        return Falseis_snapi_connected

    def connect(self):
        debug_message.print_message('BarcodeUSB connecting...')
        time.sleep(2)
        try:
            _is_snapi = False
            backend = usb.backend.libusb1.get_backend(find_library=lambda x: '/usr/lib/libusb-1.0.so')
            barcode_scanners = usb.core.find(find_all=1, idVendor=VENDOR_ID, backend=backend)
            for barcode in barcode_scanners:
                if barcode.idProduct != PRODUCT_ID:
                    debug_message.print_message('Device in USB HID mode')
                else:
                    _is_snapi = True

            if _is_snapi:
                self.device = usb.core.find(idVendor=VENDOR_ID, idProduct=PRODUCT_ID, backend=backend)
                if self.device:
                    debug_message.print_message('Device SNAPI found')
                    self.run_once = False
                    debug_message.print_message('Device initialized')
            else:
                self.device = usb.core.find(idVendor=VENDOR_ID, idProduct=PRODUCT_ID_KEYBOARD, backend=backend)
                if self.device:
                    debug_message.print_message('Device USB HID found')
            if self.device:
                self.device.set_configuration()
                self.device.reset()
                self.endpoint = self.device[0][(0, 0)][0]
                self.is_connect = True
                self.error_count = 0
                self.enable()
                debug_message.print_message('Device initialized')
            else:
                self.init_dio()
        except usb.core.USBError as e:
            debug_message.print_message(e)
            self.close_dio()

    def init_reader(self):
        if not self.run_once and self.is_connected():
            if self.is_snapi():
                debug_message.print_message('In snapi mode')
                self.init_usb()
            self.run_once = True

    def init_dio(self):
        open_time_start = time.time()
        cmd = 'echo 111 > /sys/class/gpio/export'
        debug_message.print_message('Init DIO 111 and on: ')
        os.system(cmd)
        cmd = 'echo out > /sys/class/gpio/gpio111/direction'
        debug_message.print_message('Init DIO 111 and on: ')
        os.system(cmd)
        cmd = 'echo 1 > /sys/class/gpio/gpio111/value'
        debug_message.print_message('Init DIO 111 and on: ')
        os.system(cmd)
        time.sleep(4)
        debug_message.print_message('Init barcode dio --- %s seconds ---' % (time.time() - open_time_start))

    def on_dio(self):
        open_time_start = time.time()
        cmd = 'echo 1 > /sys/class/gpio/gpio111/value'
        debug_message.print_message('DIO 111 on: ')
        os.system(cmd)
        time.sleep(4)
        debug_message.print_message('Off barcode dio --- %s seconds ---' % (time.time() - open_time_start))

    def close_dio(self):
        if self.error_count_dio < 3:
            self.error_count_dio += 1
            return
        else:
            self.error_count_dio = 0
            self.is_connect = False
            self.run_once = False
            self.device = None
            open_time_start = time.time()
            cmd = 'echo 0 > /sys/class/gpio/gpio111/value'
            debug_message.print_message('DIO 111 off: ')
            os.system(cmd)
            time.sleep(4)
            debug_message.print_message('Off barcode dio --- %s seconds ---' % (time.time() - open_time_start))
            self.on_dio()
            return

    def close_connection(self):
        debug_message.print_message('---------------Get USB Error-----------------')
        if self.error_count < 3:
            self.error_count += 1
            self.is_connect = False
            self.device = None
        else:
            self.close_usb()
            self.is_connect = False
            self.error_count = 0
        return

    def close_usb(self):
        try:
            self.device.reset()
            usb.util.dispose_resources(self.device)
        except Exception as e:
            debug_message.print_message('-----------Close Usb device error------------')
            debug_message.print_message(e)
            debug_message.print_message('-----------!Close Usb device error-----------')

    def exit(self):
        if self.online:
            self.online = False
        self.close_usb()
        debug_message.print_message('Barcode usb stopped')

    def get_active(self):
        return self.get_option('active', False)

    def set_active(self, active):
        if self.get_active() != active:
            self.set_option('active', active)
            self.is_active_change = True
        if active:
            self.set_send_data(True)

    def get_send_data(self):
        return self.get_option('is_data', False)

    def set_send_data(self, value):
        if self.get_send_data() != value:
            self.set_option('is_data', value)

    def can_send_data(self):
        return self.get_active() and self.get_send_data()

    def get_option(self, _key, _default=None):
        if _key in self.options:
            return self.options[_key]
        else:
            return _default

    def get_barcode_length(self, _type):
        if _type in self.barcode_type:
            return self.barcode_type[_type]
        else:
            return

    def set_barcode_length(self, _type, _value):
        if self.get_barcode_length(_type) is not None and self.get_barcode_length(_type) != _value:
            self.barcode_type[_type] = _value
        else:
            self.barcode_type[_type] = _value
        return

    def set_option_vcheck(self, _key, _value):
        if _key == 'active':
            self.set_active(_value)
        elif _key == 'barcode_length_128':
            self.set_barcode_length(3, _value)
        elif _key == 'barcode_length_2of5':
            self.set_barcode_length(6, _value)
        elif _key == 'is_data':
            self.set_send_data(_value)

    def set_option(self, _key, _value):
        try:
            if _key == 'ff_date':
                _set_value = []
                if _value is not None:
                    debug_message.print_message('Set ff_date: ' + _value)
                    if _value:
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
# okay decompiling /home/a/Desktop/app/Barcode.pyc
Dev (bus 1, device 2): Symbol Technologies, Inc, 2008 - Symbol Bar Code Scanner
  - Serial Number: S/N:Motorola Scanner************
  Configuration:
    wTotalLength:         67
    bNumInterfaces:       2
    bConfigurationValue:  1
    iConfiguration:       8
    bmAttributes:         a0h
    MaxPower:             250
    Interface:
      bInterfaceNumber:   0
      bAlternateSetting:  0
      bNumEndpoints:      1
      bInterfaceClass:    2
      bInterfaceSubClass: 2
      bInterfaceProtocol: 1
      iInterface:         0
      Endpoint:
        bEndpointAddress: 81h
        bmAttributes:     03h
        wMaxPacketSize:   64
        bInterval:        1
        bRefresh:         0
        bSynchAddress:    0
    Interface:
      bInterfaceNumber:   1
      bAlternateSetting:  0
      bNumEndpoints:      2
      bInterfaceClass:    10
      bInterfaceSubClass: 0
      bInterfaceProtocol: 0
      iInterface:         0
      Endpoint:
        bEndpointAddress: 02h
        bmAttributes:     02h
        wMaxPacketSize:   64
        bInterval:        255
        bRefresh:         0
        bSynchAddress:    0
      Endpoint:
        bEndpointAddress: 83h
        bmAttributes:     02h
        wMaxPacketSize:   64
        bInterval:        255
        bRefresh:         0
        bSynchAddress:    0


snapi mode!

- Serial Number: S/N:B684DF6ED09CF7419E392F53AE16D1D9 Rev:PAADOS00-002-R069
  Configuration:
    wTotalLength:         64
    bNumInterfaces:       2
    bConfigurationValue:  1
    iConfiguration:       8
    bmAttributes:         a0h
    MaxPower:             250
    Interface:
      bInterfaceNumber:   0
      bAlternateSetting:  0
      bNumEndpoints:      1
      bInterfaceClass:    3
      bInterfaceSubClass: 0
      bInterfaceProtocol: 0
      iInterface:         5
      Endpoint:
        bEndpointAddress: 81h
        bmAttributes:     03h
        wMaxPacketSize:   64
        bInterval:        3
        bRefresh:         0
        bSynchAddress:    0
    Interface:
      bInterfaceNumber:   1
      bAlternateSetting:  0
      bNumEndpoints:      3
      bInterfaceClass:    255
      bInterfaceSubClass: 1
      bInterfaceProtocol: 0
      iInterface:         6
      Endpoint:
        bEndpointAddress: 82h
        bmAttributes:     02h
        wMaxPacketSize:   64
        bInterval:        255
        bRefresh:         0
        bSynchAddress:    0
      Endpoint:
        bEndpointAddress: 83h
        bmAttributes:     02h
        wMaxPacketSize:   64
        bInterval:        255
        bRefresh:         0
        bSynchAddress:    0
      Endpoint:
        bEndpointAddress: 04h
        bmAttributes:     02h
        wMaxPacketSize:   64
        bInterval:        255
        bRefresh:         0
        bSynchAddress:    0


