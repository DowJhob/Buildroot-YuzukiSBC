# uncompyle6 version 3.4.0
# Python bytecode 2.7 (62211)
# Decompiled from: Python 2.7.15+ (default, Oct  7 2019, 17:39:04) 
# [GCC 7.4.0]
# Embedded file name: /home/user/zeus/rfid_nfc.py
# Compiled at: 2018-06-13 18:42:28
from __future__ import print_function
import time, serial, binascii, logging, threading
from lib import requests, singleton
import json
from frame import Pn532Frame
from constants import *
from arjo import ArjoLink
from DebugImport import debug_message
import datetime, Queue
from Models import QueueData
logger = logging.getLogger('zeus')
RFID_STATE_READ = 0
RFID_STATE_COMMAND = 1
RFID_STATE_DATA = 2

class PN532Error(Exception):
    """General Exception"""
    pass


class PN532ReceiveError(PN532Error):
    """Serial input out of synch.  Try waiting a few seconds, flush input stream, and reissue command"""
    pass


class RfidNfc(object):

    def __init__(self, app_path, inputqe, outputqe, readeq, unix_socket='/dev/ttySP0'):
        self.unix_socket = unix_socket
        self.port = None
        self.app_path = app_path
        self.client = None
        self.online = True
        self.is_connect = False
        self.thread_w = None
        self.state = RFID_STATE_READ
        self.data = ''
        self.version = ''
        self.frame = ''
        self.uid = ''
        self.auth = False
        self.options = {}
        self.inputqe = inputqe
        self.outputqe = outputqe
        self.readeq = readeq
        self.prev_state = True
        return

    def print_package(self):
        debug_message.print_message('package: ' + binascii.hexlify(self.frame.to_tuple()))

    def frame_sam_configure(self):
        self.frame = Pn532Frame(frame_type=PN532_FRAME_INIT, data=bytearray([PN532_COMMAND_SAMCONFIGURATION, PN532_SAMCONFIGURATION_MODE_NORMAL, PN532_SAMCONFIGURATION_TIMEOUT_1S, PN532_SAMCONFIGURATION_IRQ_ON]))
        self.print_package()
        return self.frame

    def frame_max_retries(self):
        self.frame = Pn532Frame(frame_type=PN532_FRAME_TYPE_DATA, data=bytearray([PN532_COMMAND_RFCONFIGURATION, 5,
         2, 1, 8]))
        self.print_package()
        return self.frame

    def frame_get_firmware(self):
        self.frame = Pn532Frame(frame_type=PN532_FRAME_TYPE_DATA, data=bytearray([PN532_COMMAND_GETFIRMWAREVERSION]))
        self.print_package()
        return self.frame

    def frame_get_status(self):
        self.frame = Pn532Frame(frame_type=PN532_FRAME_TYPE_DATA, data=bytearray([PN532_COMMAND_GETGENERALSTATUS]))
        self.print_package()
        return self.frame

    def frame_read_card(self):
        self.frame = Pn532Frame(frame_type=PN532_FRAME_TYPE_DATA, data=bytearray([PN532_COMMAND_INLISTPASSIVETARGET,
         1, 0]))
        return self.frame

    def frame_ask(self):
        self.frame = Pn532Frame(frame_type=PN532_FRAME_TYPE_ACK)
        self.print_package()
        return self.frame

    def frame_read_data(self, addr=0):
        self.frame = Pn532Frame(frame_type=PN532_FRAME_TYPE_DATA, data=bytearray([PN532_COMMAND_INDATAEXCHANGE, 1,
         NFC_READ, addr]))
        self.print_package()
        return self.frame

    def frame_pwd_auth(self, pwd=bytearray([255, 255, 255, 255])):
        self.frame = Pn532Frame(frame_type=PN532_FRAME_TYPE_DATA, data=bytearray([PN532_COMMAND_INCOMMUNICATETHRU,
         NFC_EV1_PWD_AUTH]) + pwd)
        self.print_package()
        return self.frame

    def get_pwd_local(self, uid):
        pwd_data = bytearray()
        try:
            arjo_link = ArjoLink()
            date = self.get_match_date()
            debug_message.print_message('  Date: ' + binascii.hexlify(date))
            sac = self.get_sac()
            sac_ba = bytearray.fromhex(sac)
            uid_ba = bytearray.fromhex(uid)
            match_id = self.get_match_id()
            if match_id > 0 and sac_ba:
                _pack_pwd = arjo_link.get_packpwd(('').join(map(chr, sac_ba)), ('').join(map(chr, uid_ba)), ('').join(map(chr, date)), match_id)
                if _pack_pwd and hasattr(_pack_pwd, 'contents') and len(_pack_pwd.contents) == 6:
                    pwd_data = bytearray(_pack_pwd.contents)
                    _pwd = pwd_data[:4]
                    _pack = pwd_data[4:6]
                    debug_message.print_message('  password: ' + binascii.hexlify(_pwd))
                    debug_message.print_message('  pack: ' + binascii.hexlify(_pack))
        except Exception as e:
            debug_message.print_message('---------------get pwd local----------------')
            debug_message.print_message(e)
            debug_message.print_message('---------------get pwd local----------------')

        return pwd_data

    def get_ticket_decrypt_local(self, uid, crypto):
        _decrypt = bytearray()
        try:
            arjo_link = ArjoLink()
            sac = self.get_sac()
            sac_ba = bytearray.fromhex(sac)
            uid_ba = bytearray.fromhex(uid)
            crypt_ba = bytearray.fromhex(crypto)
            match_id = self.get_match_id()
            if match_id > 0 and sac_ba:
                decrypt = arjo_link.get_decrypt_data(('').join(map(chr, sac_ba)), ('').join(map(chr, crypt_ba)), ('').join(map(chr, uid_ba)), match_id)
                if decrypt and hasattr(decrypt, 'contents') and len(decrypt.contents) == 16:
                    decrypt_data = bytearray(decrypt.contents)
                    _uid = decrypt_data[:8]
                    _decrypt = binascii.hexlify(decrypt_data)
                    debug_message.print_message('  decrypt: ' + _decrypt)
                    _decrypt = _uid
        except Exception as e:
            debug_message.print_message('---------------get pwd local----------------')
            debug_message.print_message(e)
            debug_message.print_message('---------------get pwd local----------------')

        return _decrypt

    def is_check_crypt_data(self):
        sac = self.get_sac()
        match_id = self.get_match_id()
        if match_id > 0 and sac:
            return True
        return False

    def write(self, _data):
        try:
            self.port.write(_data)
        except serial.SerialTimeoutException:
            self.is_connect = False
            debug_message.print_message('RFID1356 Read Error')
        except serial.SerialException:
            self.is_connect = False
            debug_message.print_message('RFID1356 SerialException Error')
        except ValueError as e:
            self.is_connect = False
            debug_message.print_message(e)
            debug_message.print_message('RFID1356 ValueError Error')

    def ReadStartByte(self):
        start = '\xff'
        timeouts_waited = 0
        while timeouts_waited < 5:
            start = self.port.read()
            if start == '\x00':
                break
            timeouts_waited += 1
            time.sleep(0.01)

        return start

    def get_response(self, timeout, _debug=True):
        data_raw = ''
        try:
            _is_response = False
            _is_ask = False
            data_raw = self.ReadStartByte()
            if data_raw == '\x00':
                _data = self.port.read(2)
                if len(_data) != 2 or _data != '\x00\xff':
                    raise PN532ReceiveError('Error in read data 1.')
                data_raw += _data
                _data = self.port.read(2)
                if len(_data) != 2:
                    raise PN532ReceiveError('Error in read data 2.')
                if _data == '\x00\xff':
                    _is_ask = True
                data_raw += _data
                if _is_ask:
                    _data = self.port.read()
                    if len(_data) != 1 or _data != '\x00':
                        raise PN532ReceiveError('Error in read data 3.')
                    data_raw += _data
                _is_response = True
            if _is_response:
                if _is_ask:
                    data_raw = self.ReadStartByte()
                if data_raw[0] == '\x00':
                    if _is_ask:
                        _data = self.port.read(2)
                        if len(_data) != 2 or _data != '\x00\xff':
                            raise PN532ReceiveError('Error in read data 4.')
                        data_raw += _data
                        _data = self.port.read()
                        if len(_data) != 1 or _data == '\x00':
                            raise PN532ReceiveError('Error in read data 5.')
                        data_raw += _data
                        _data = self.port.read()
                        if len(_data) != 1:
                            raise PN532ReceiveError('Error in read data 6.')
                        data_raw += _data
                    _data = self.port.read(ord(data_raw[3]))
                    if len(_data) != ord(data_raw[3]):
                        raise PN532ReceiveError('Error in read data 8.')
                    data_raw += _data
                    _data = self.port.read()
                    if len(_data) != 1:
                        raise PN532ReceiveError('Error in read data 9.')
                    data_raw += _data
                    _data = self.port.read()
                    if len(_data) != 1 or _data != '\x00':
                        raise PN532ReceiveError('Error in read data 10.')
                    data_raw += _data
        except serial.SerialTimeoutException:
            debug_message.print_message('RFID1356 Read Error')
            time.sleep(2)
            self.port.flushInput()
        except serial.SerialException:
            debug_message.print_message('RFID1356 SerialException Error')
            time.sleep(2)
            self.port.flushInput()
        except ValueError as e:
            debug_message.print_message(e)
            debug_message.print_message('RFID1356 ValueError Error')
        except PN532ReceiveError as e:
            debug_message.print_message('========M5e handle error==============')
            debug_message.print_message(e)
            debug_message.print_message('========M5e handle error==============')

        return data_raw

    def init_reader(self):
        if self.is_connected():
            frame = self.frame_sam_configure()
            self.write(frame.to_tuple())
            answer = self.get_response(0.04)
            frame = self.frame_max_retries()
            self.write(frame.to_tuple())
            answer = self.get_response(0.04)
            self.device_version()

    def get_queue(self):
        if not self.inputqe.empty():
            try:
                _data = self.inputqe.get(False)
            except Queue.Empty as queue_error:
                _data = None

            if isinstance(_data, QueueData):
                debug_message.print_message('-----------RFID1356 receive data-------------')
                debug_message.print_message('\t' + _data.command)
                debug_message.print_message(_data.value)
                if _data.command == 'exit':
                    self.exit()
                elif _data.command == 'read':
                    if self.state == RFID_STATE_DATA:
                        self.state = RFID_STATE_READ
                elif _data.command == 'options' and isinstance(_data.value, dict) and _data.value:
                    if 'key' in _data.value and 'value' in _data.value:
                        debug_message.print_message('Set rfid1356 key: ' + _data.value['key'])
                        debug_message.print_message(_data.value['value'])
                        self.set_option_vcheck(_data.value['key'], _data.value['value'])
        return

    def read_data(self):
        while self.online:
            self.get_queue()
            if self.get_status():
                self.outputqe.put(QueueData('rfid1356', {'status': self.is_online()}))
            if not self.is_connected() or not self.version:
                time.sleep(5)
                self.connect()
                self.init_reader()
                continue
            if self.state == RFID_STATE_READ:
                self.device_read()
                self.send_data()
            else:
                time.sleep(0.03)

        debug_message.print_message('Out from read_data circle')

    def send_data(self):
        if not self.uid:
            return
        try:
            self.readeq.put(QueueData('rfid1356', {'uid': self.uid, 'pwdpack': self.auth}))
            self.state = RFID_STATE_DATA
            self.uid = ''
        except Exception as e:
            debug_message.print_message('RFID1356 exp in circle')
            debug_message.print_message(e)

    def device_version(self):
        frame = self.frame_get_firmware()
        self.write(frame.to_tuple())
        _data = binascii.hexlify(self.get_response(0.05))
        if _data:
            self.version = _data[8:10]
            debug_message.print_message('IC: ' + _data[6:8])
            debug_message.print_message('Ver: ' + _data[8:10])
            debug_message.print_message('Rev: ' + _data[10:12])
            debug_message.print_message('Support: ' + _data[12:14])

    def device_status(self):
        frame = self.frame_get_status()
        self.write(frame.to_tuple())
        _data = binascii.hexlify(self.get_response(0.05))
        return _data

    def device_read(self):
        if self.uid:
            self.uid = ''
        self.auth = False
        nfc_time = time.time()
        frame = self.frame_read_card()
        self.write(frame.to_tuple())
        _response = self.get_response(0.01, False)
        _tmp_frame = Pn532Frame.from_response(_response)
        _data = _tmp_frame.get_data()
        if not _data or _data[0] != PN532_COMMAND_INLISTPASSIVETARGET_RET:
            return
        data_string = binascii.hexlify(_response)
        if data_string[15:16] == '0':
            return
        debug_message.time_message(_prefix='--v0')
        debug_message.print_message('  tag version length: ' + data_string[25:26])
        if data_string[25:26] == '4':
            _uid = data_string[26:34]
        else:
            _uid = data_string[26:40]
        debug_message.print_message('tag UID: ' + _uid)
        self.uid = _uid
        if not self.get_ff_mode():
            return
        if not self.get_nfc_enable():
            self.auth = True
            return
        if not self.is_check_crypt_data():
            debug_message.print_message('\tRFID NFC check only uid. Match id or SAC is empty')
            return
        debug_message.time_message(_prefix='--v1')
        pwd_data = self.get_pwd_local(_uid)
        debug_message.time_message(_prefix='--v1')
        if len(pwd_data) == 6:
            _pwd = pwd_data[:4]
            _pack = pwd_data[4:6]
            debug_message.print_message('  password: ' + binascii.hexlify(_pwd))
            debug_message.print_message('  pack: ' + binascii.hexlify(_pack))
            debug_message.print_message('=============pwd auth======================')
            debug_message.time_message(_prefix='--v21')
            frame = self.frame_pwd_auth(_pwd)
            self.write(frame.to_tuple())
            debug_message.time_message(_prefix='--v21')
            answer = self.get_response(0.01)
            debug_message.time_message(_prefix='--v21')
            _tmp_frame = Pn532Frame.from_response(answer)
            _data = _tmp_frame.get_data()
            debug_message.print_message('  data: ' + binascii.hexlify(_data))
            if _tmp_frame.get_length() != 5 or _data[0] != PN532_COMMAND_INCOMMUNICATETHRU_RET:
                debug_message.print_message('  incorrect response')
                return
            if _data[2] != _pack[0] or _data[3] != _pack[1]:
                debug_message.print_message('  incorrect auth')
                return
            debug_message.print_message('=============!pwd auth=====================')
            self.auth = True
            debug_message.print_message('=============read banks data================')
            debug_message.time_message(_prefix='--v31')
            frame = self.frame_read_data(addr=8)
            self.write(frame.to_tuple())
            debug_message.time_message(_prefix='--v31')
            answer = self.get_response(0.01)
            debug_message.time_message(_prefix='--v31')
            _tmp_frame = Pn532Frame.from_response(answer)
            _data = _tmp_frame.get_data()
            debug_message.print_message('  data: ' + binascii.hexlify(_data))
            if _tmp_frame.get_length() != 19 or _data[0] != PN532_COMMAND_INDATAEXCHANGE_RET:
                debug_message.print_message(' incorrect data')
                return
            debug_message.print_message('=============!read banks data===============')
            _crypto = _data[2:18]
            debug_message.print_message('  crypto: ' + binascii.hexlify(_crypto))
            debug_message.time_message(_prefix='--v4')
            _decrypt_data = self.get_ticket_decrypt_local(_uid, binascii.hexlify(_crypto))
            if not _decrypt_data:
                self.auth = False
            else:
                self.uid = binascii.hexlify(_decrypt_data)
            debug_message.time_message(_prefix='--v4')
            if _decrypt_data:
                debug_message.print_message('received: ' + binascii.hexlify(_decrypt_data))
            else:
                debug_message.print_message('received: empty')
            debug_message.time_message(_prefix='--!v0')
        else:
            debug_message.print_message('Incorrect pwd data')
        debug_message.time_message('NFC read time --- %s seconds ---' % (time.time() - nfc_time))
        debug_message.time_message()

    def is_connected(self):
        if self.port is None or not self.port.is_open:
            return False
        return self.is_connect

    def is_online(self):
        if self.port is None or not self.port.is_open:
            return False
        return self.is_connect

    def get_status(self):
        if self.prev_state != self.is_online():
            self.prev_state = self.is_online()
            return True
        return False

    def connect(self):
        time.sleep(10)
        debug_message.print_message('RFID1356 connecting...')
        try:
            self.version = ''
            if self.port and self.port.is_open:
                self.port.close()
            self.is_connect = False
            if not self.port:
                self.port = serial.Serial()
            self.port.port = self.unix_socket
            self.port.baudrate = 115200
            self.port.parity = serial.PARITY_NONE
            self.port.stopbits = serial.STOPBITS_ONE
            self.port.bytesize = serial.EIGHTBITS
            self.port.timeout = 1.0
            self.port.write_timeout = 1.0
            self.port.open()
            if self.port and self.port.is_open:
                self.is_connect = True
                debug_message.print_message('RFID1365 port opened')
        except serial.SerialException:
            debug_message.print_message('RFID1356 SerialException Error')
            self.is_connect = False
        except ValueError as e:
            debug_message.print_message(e)
            debug_message.print_message('RFID1356 ValueError Error')
            self.is_connect = False

    def run(self):
        debug_message.print_message('RFID1356 run')
        self.set_match_date('19-06-18')
        self.set_active(True)
        self.set_ff_mode(True)
        self.set_match_id(80)
        self.set_nfc_enable(True)
        self.set_sac('D0B9373CBF1D929D')
        self.read_data()

    def exit(self):
        if self.online:
            self.online = False
        try:
            if self.port.is_open:
                self.port.close()
        except ValueError as e:
            debug_message.print_message('=========RFID1356 port close error===========')
            debug_message.print_message(e)
            debug_message.print_message('=========!RFID1356 port close error==========')

    def set_match_date(self, match_date):
        _tmp = ''
        if isinstance(self.get_option('ff_date'), list) and len(self.get_option('ff_date')) == 3:
            _tmp = ('-').join(self.get_option('ff_date'))
        if _tmp != match_date:
            self.set_option('ff_date', match_date)

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

    def get_option(self, _key, _default=None):
        if _key in self.options:
            return self.options[_key]
        else:
            return _default

    def set_option_vcheck(self, _key, _value):
        if _key == 'ff_date':
            self.set_match_date(_value)
        elif _key == 'match_n':
            self.set_match_id(_value)
        elif _key == 'active':
            self.set_active(_value)
        elif _key == 'ff_mode':
            self.set_ff_mode(_value)
        elif _key == 'nfc_enable':
            self.set_nfc_enable(_value)
        elif _key == 'fifa_sac':
            self.set_sac(_value)

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

    def get_match_id(self):
        return self.get_option('match_id', 0)

    def set_match_id(self, match_id):
        if self.get_match_id() != match_id:
            self.set_option('match_id', match_id)

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

    def get_active(self):
        return self.get_option('active', False)

    def set_active(self, active):
        if self.get_active() != active:
            self.set_option('active', active)
        if active:
            self.state = RFID_STATE_READ

    def get_ff_mode(self):
        return self.get_option('ff_mode', False)

    def set_ff_mode(self, ff_mode):
        if self.get_ff_mode() != ff_mode:
            self.set_option('ff_mode', ff_mode)

    def get_nfc_enable(self):
        return self.get_option('nfc_enable', False)

    def set_nfc_enable(self, nfc_enable):
        if self.get_nfc_enable() != nfc_enable:
            self.set_option('nfc_enable', nfc_enable)