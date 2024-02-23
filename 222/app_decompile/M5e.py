# uncompyle6 version 3.4.0
# Python bytecode 2.7 (62211)
# Decompiled from: Python 2.7.15+ (default, Oct  7 2019, 17:39:04) 
# [GCC 7.4.0]
# Embedded file name: /home/user/zeus/M5e.py
# Compiled at: 2019-02-27 18:08:16
from threading import Thread
import binascii, time, serial
from DebugImport import debug_message

class M5eError(Exception):
    """General Exception"""
    pass


class M5ePortError(M5eError):
    """If pyserial throws error"""
    pass


class M5eCrcError(M5eError):
    """If CRC check from Mercury packet is incorrect (data corruption)"""
    pass


class M5eCommandStatusError(M5eError):
    """If return response from Mercury is non-zero (error status)"""
    pass


class M5eTransmitTimeoutExceeded(M5eError):
    """Something happened (probably power failure) to disable serial transmission"""
    pass


class M5eReceiveError(M5eError):
    """Serial input out of synch.  Try waiting a few seconds, flush input stream, and reissue command"""
    pass


class M5ePoller(Thread):
    """Create read thread"""
    QUERY_MODE = 'query'
    TRACK_MODE = 'track'

    def __init__(self, M5e, antfuncs=[], callbacks=[]):
        Thread.__init__(self)
        self.M5e = M5e
        self.antfuncs = antfuncs
        self.callbacks = callbacks
        self.mode = ''
        self.should_run = True
        self.tag_to_track = ''
        self.broadcaster = None
        debug_message.set_mode('development')
        debug_message.print_message('Creating M5e Polling Thread')
        self.start()
        return

    def pause_poller(self):
        self.mode = ''

    def query_mode(self):
        self.mode = self.QUERY_MODE

    def track_mode(self, tag_id):
        self.mode = self.TRACK_MODE
        self.tag_to_track = tag_id

    def is_online(self):
        return self.M5e.is_online()

    def run(self):
        while self.should_run:
            if self.M5e.ser is None:
                self.M5e.connect()
                if self.M5e.is_connected():
                    self.M5e.send_boot()
                    self.M5e.set_parameters()
            elif self.mode == self.QUERY_MODE:
                antenna_name = 'Ant1'
                results = self.M5e.query_environment()
                for tag_id, rssi in results:
                    datum = [
                     antenna_name, tag_id, rssi]
                    [ cF(datum) for cF in self.callbacks ]

                time.sleep(0.3)
            else:
                time.sleep(0.05)

        return

    def stop(self):
        self.should_run = False
        time.sleep(4)
        if self.M5e.is_connected():
            self.M5e.ser.close()
        self.join(30)
        if self.isAlive():
            debug_message.print_message("Can't stop M5E service")
        else:
            debug_message.print_message('M5E service is stopped')


class M5e:
    """
    Interface to Mercury M5e and M5e-Compact
    """

    def __init__(self, portINT=-1, portSTR='/dev/RFIDreader', baudrate=9600, TXport=1, RXport=1, readPwr=2300, protocol='GEN2', compact=True, verbosity=1):
        if portINT != -1:
            self.port = portINT
        else:
            self.port = portSTR
        self.baudrate = baudrate
        self.TXport = TXport
        self.RXport = RXport
        self.readPwr = readPwr
        self.protocol = protocol
        self.compact = compact
        self.verbosity = verbosity
        self.ser = None
        self.connect_errors = 0
        self.send_errors = 0
        if verbosity > 0:
            debug_message.print_message('Initializing M5e (or M5e-Compact)')
        return

    def is_connected(self):
        if self.ser is not None and self.ser.is_open:
            return True
        else:
            return False
            return

    def is_online(self):
        return self.is_connected()

    def open_port(self, baudrate=9600):
        time.sleep(5)
        debug_message.print_message('\tAttempting ' + str(baudrate) + ' bps')
        try:
            if self.is_connected():
                self.ser.close()
            self.ser = serial.Serial()
            self.ser.port = self.port
            self.ser.baudrate = baudrate
            self.ser.timeout = 0.3
            self.ser.write_timeout = 2
            self.ser.open()
            if self.ser and self.ser.is_open:
                if self.connect_errors > 0:
                    time.sleep(5)
                    self.ser.flushInput()
                self.send_get_version()
                self.connect_errors = 0
                if self.ser is not None:
                    debug_message.print_message('\tSuccessful at ' + str(baudrate) + ' bps')
        except serial.SerialException:
            debug_message.print_message('========M5e connect error=============')
            debug_message.print_message('SerialException')
            debug_message.print_message('========!M5e connect error============')
            if self.is_connected():
                self.ser.close()
                self.ser = None
            self.connect_errors += 1
            debug_message.print_message('\tFailed at ' + str(baudrate) + ' bps')
        except ValueError as e:
            debug_message.print_message('========M5e connect error=============')
            debug_message.print_message(e)
            debug_message.print_message('========!M5e connect error============')
            if self.is_connected():
                self.ser.close()
                self.ser = None
            self.connect_errors += 1
            debug_message.print_message('\tFailed at ' + str(baudrate) + ' bps')

        return

    def handle_error(self):
        if self.is_connected():
            time.sleep(5)
            self.ser.flushInput()
            self.ser.close()
        self.ser = None
        return

    def connect(self):
        debug_message.print_message('Connecting to RFID...')
        self.open_port(115200)
        if not self.is_connected():
            self.open_port()
            if self.is_connected():
                debug_message.print_message('\tSwitching to 115200 bps')
                self.TransmitCommand('\x04\x06\x00\x01\xc2\x00')
                start, length, command, status, data, CRC = self.ReceiveResponse()
                if status != '\x00\x00':
                    debug_message.print_message('========M5e handle error==============')
                    debug_message.print_message('M5e not ready')
                    debug_message.print_message('========M5e handle error==============')
                    self.handle_error()
                else:
                    self.open_port(115200)
        if self.ser is None:
            debug_message.print_message("Could't open serial port %s at baudrate %d or %d." % (self.port, 115200, 9600))
        return

    def send_get_version(self):
        self.TransmitCommandWithRepeat('\x00\x03')

    def send_boot(self):
        self.TransmitCommandWithRepeat('\x00\x04')

    def set_parameters(self):
        self.ChangeAntennaPorts(self.TXport, self.RXport)
        self.ChangeTXReadPower(self.readPwr)
        if self.protocol != 'GEN2':
            raise M5eError('Sorry, GEN2 is only protocol supported at this time')
        self.TransmitCommandWithRepeat('\x02\x93\x00\x05')
        self.TransmitCommandWithRepeat('\x01\x97\x08')
        self.TransmitCommandWithRepeat('\x00g')
        self.TransmitCommandWithRepeat('\x0c\x95\x00\r9\x8c\x00\r:T\x00\r;\xe4')
        self.TransmitCommandWithRepeat('\x00e')

    def ChangeAntennaPorts(self, TXport, RXport):
        self.TXport = TXport
        self.RXport = RXport
        self.TransmitCommandWithRepeat('\x02\x91' + chr(self.TXport) + chr(self.RXport))

    def ChangeTXReadPower(self, readPwr):
        self.readPwr = readPwr
        readTXPwrHighByte = chr((self.readPwr & 65535) >> 8)
        readTXPwrLowByte = chr(self.readPwr & 255)
        self.TransmitCommandWithRepeat('\x02\x92' + readTXPwrHighByte + readTXPwrLowByte)

    def CalculateCRC(self, msg):
        crc_result = 65535
        for x in range(len(msg)):
            curr_char = ord(msg[x])
            v = 128
            for y in range(8):
                xor_flag = 0
                if crc_result & 32768:
                    xor_flag = 1
                crc_result <<= 1
                if curr_char & v:
                    crc_result += 1
                if xor_flag:
                    crc_result ^= 4129
                v >>= 1
                crc_result &= 65535

        return chr(crc_result >> 8 & 255) + chr(crc_result & 255)

    def ReturnHexString(self, hexStr):
        result = ''
        for i in range(len(hexStr)):
            result = result + hex(ord(hexStr[i])) + ' '

        return result

    def ConstructCommand(self, hexCommand):
        return '\xff' + hexCommand + self.CalculateCRC(hexCommand)

    def TransmitCommandWithRepeat(self, send_command):
        self.TransmitCommandWithAnswer(send_command)
        start, length, command, status, data, CRC = self.ReceiveResponse()
        if status != '\x00\x00':
            if status != '\x01\x01' and send_command != '\x00\x04':
                self.TransmitCommandWithAnswer(send_command)
                start, length, command, status, data, CRC = self.ReceiveResponse()
        if status != '\x00\x00':
            if status != '\x01\x01' and send_command != '\x00\x04':
                debug_message.print_message('========M5e handle error==============')
                debug_message.print_message('M5e not ready')
                debug_message.print_message('========M5e handle error==============')
                self.handle_error()
        return (
         start, length, command, status, data, CRC)

    def TransmitCommandWithAnswer(self, command):
        if not self.is_connected():
            return False
        _ret = self.TransmitCommand(command)
        if not _ret and self.send_errors < 3:
            self.send_errors += 1
            self.ser.flushInput()
            time.sleep(1)
            _ret = self.TransmitCommandWithAnswer(command)
        if self.send_errors:
            self.send_errors = 0
        return _ret

    def TransmitCommand(self, command):
        if not self.is_connected():
            return False
        _ret = True
        try:
            self.ser.write(self.ConstructCommand(command))
        except Exception as e:
            _ret = False
            debug_message.print_message(e)
            debug_message.print_message('Error (maybe power failure) to write to port')

        return _ret

    def ReadStartByte(self):
        start = '\x00'
        timeouts_waited = 0
        while timeouts_waited < 5:
            start = self.ser.read()
            if start == '\xff':
                break
            timeouts_waited += 1
            time.sleep(0.01)

        return start

    def ReadData(self):
        data_raw = ''
        try:
            data_raw = self.ReadStartByte()
            if data_raw == '\xff':
                _data = self.ser.read()
                if len(_data) != 1:
                    raise M5eReceiveError('Error in read data.')
                data_raw += _data
                _data = self.ser.read()
                if len(_data) != 1:
                    raise M5eReceiveError('Error in read data.')
                data_raw += _data
                _data = self.ser.read(2)
                if len(_data) != 2:
                    raise M5eReceiveError('Error in read data.')
                data_raw += _data
                _data = self.ser.read(ord(data_raw[1]))
                if len(_data) != ord(data_raw[1]):
                    raise M5eReceiveError('Error in read data.')
                data_raw += _data
                _data = self.ser.read(2)
                if len(_data) != 2:
                    raise M5eReceiveError('Error in read data.')
                data_raw += _data
        except serial.SerialTimeoutException:
            debug_message.print_message('RFID866 Read Error')
            time.sleep(2)
            self.ser.flushInput()
        except serial.SerialException:
            debug_message.print_message('RFID866 SerialException Error')
            time.sleep(2)
            self.ser.flushInput()
        except ValueError as e:
            debug_message.print_message(e)
            debug_message.print_message('RFID866 ValueError Error')
        except M5eReceiveError as e:
            debug_message.print_message('========M5e handle error==============')
            debug_message.print_message(e)
            debug_message.print_message('========M5e handle error==============')
        except Exception as e:
            debug_message.print_message(e)
            debug_message.print_message('RFID866 Exception Error')

        if not data_raw:
            debug_message.print_message('Empty Data read')
            time.sleep(2)
            self.ser.flushInput()
        if data_raw and len(data_raw) < 7:
            debug_message.print_message('Data not full')
            time.sleep(2)
            self.ser.flushInput()
        return data_raw

    def ReceiveResponse(self):
        receive_status = True
        start = '\x00'
        length = 0
        command = ''
        status = '\xff\xff'
        data = 0
        crc = 0
        if not self.is_connected():
            return (start, length, command, status, data, crc)
        data_raw = self.ReadData()
        try:
            if data_raw:
                if data_raw[0] != '\xff':
                    raise M5eReceiveError('Error in receive stream (start byte).')
                if len(data_raw) < 7:
                    raise M5eReceiveError('Error in receive stream (length less then 7 bytes).')
                start = data_raw[0]
                length = data_raw[1]
                command = data_raw[2]
                status = data_raw[3:5]
                _length = ord(length)
                data = ''
                if _length > 0:
                    data = data_raw[5:5 + _length]
                crc = data_raw[5 + _length:7 + _length]
                validate_crc = length + command + status + data
                if self.CalculateCRC(validate_crc) != crc:
                    raise M5eCrcError('Received response crc failed')
                if status != '\x00\x00':
                    raise M5eCommandStatusError('Received response returned non-zero status', status)
            else:
                debug_message.print_message(' Data raw is empty')
        except M5eReceiveError as e:
            debug_message.print_message('========M5e handle receive error==============')
            receive_status = False
            debug_message.print_message(e)
            debug_message.print_message('========M5e handle reveive error==============')
        except M5eCrcError as e:
            debug_message.print_message('========M5e handle crc error==============')
            status = '\xff\xff'
            debug_message.print_message(e)
            debug_message.print_message('========M5e handle crc error==============')
        except M5eCommandStatusError as e:
            pass
        except Exception as e:
            debug_message.print_message('========M5e handle error==============')
            receive_status = False
            debug_message.print_message(e)
            debug_message.print_message('========M5e handle error==============')

        if not receive_status:
            start = '\x00'
            length = 0
            command = ''
            data = 0
            crc = 0
            self.handle_error()
        return (
         start, length, command, status, data, crc)

    def query_environment(self, timeout=50):
        if self.ser is None:
            return []
        else:
            timeout_high_byte = chr((timeout & 65535) >> 8)
            timeout_low_byte = chr(timeout & 255)
            self.TransmitCommand('\x04"\x00\x00' + timeout_high_byte + timeout_low_byte)
            start, length, command, status, data, CRC = self.ReceiveResponse()
            if status != '\x00\x00':
                return []
            if status == '\x04\x00':
                return []
            self.TransmitCommand('\x00)')
            start, length, command, status, data, CRC = self.ReceiveResponse()
            if status != '\x00\x00':
                return []
            try:
                read_index = (ord(data[0]) << 8) + ord(data[1])
                write_index = (ord(data[2]) << 8) + ord(data[3])
                num_tags = write_index - read_index
                results = []
                while num_tags > 0:
                    self.TransmitCommand('\x03)\x00\x02\x00')
                    start, length, command, status, data, CRC = self.ReceiveResponse()
                    if status != '\x00\x00':
                        return []
                    tags_retrieved = ord(data[3])
                    for i in xrange(tags_retrieved):
                        rssi = ord(data[(4 + i * 19)])
                        tag_id = data[4 + i * 19 + 5:4 + i * 19 + 5 + 12]
                        results.append((tag_id, rssi))

                    num_tags -= tags_retrieved

            except Exception as e:
                results = []
                debug_message.print_message('----------------------M5E error-------------------')
                debug_message.print_message(e)
                debug_message.print_message('----------------------M5E error-------------------')
            else:
                self.TransmitCommand('\x00*')
                self.ReceiveResponse()
                if status != '\x00\x00':
                    return []

            return results