# uncompyle6 version 3.4.0
# Python bytecode 2.7 (62211)
# Decompiled from: Python 2.7.15+ (default, Oct  7 2019, 17:39:04) 
# [GCC 7.4.0]
# Embedded file name: /home/user/zeus/frame.py
# Compiled at: 2018-06-13 14:24:18
from frame import *
from constants import *
import binascii, os, sys
from DebugImport import debug_message
lib_path = os.path.abspath('../')
sys.path.append(lib_path)

class Pn532Frame:
    """Pn532Frame represents a single communication frame for
    communication with the PN532 NFC Chip.
    """

    def __init__(self, frame_type=PN532_FRAME_TYPE_DATA, preamble=PN532_PREAMBLE, start_code_1=PN532_START_CODE_1, start_code_2=PN532_START_CODE_2, frame_identifier=212, data=bytearray(), postamble=PN532_POSTAMBLE):
        """Constructor for the Pn532Frame class.

        Arguments:
        @param[in]  frame_type      Type of current frame.
                                    (default = PN532_FRAME_TYPE_DATA)

        @param[in]  preamble        Preamble to be used.
                                    (default = PN532_PREAMBLE)

        @param[in]  start_code_1    First byte of frame's start code.
                                    (default = PN532_START_CODE_1)

        @param[in]  start_code_2    Last byte of frame's start code.
                                    (default = PN532_START_CODE_2)

        @param[in]  frame_identifier Frame Identifier.
                                     (default = PN532_IDENTIFIER_HOST_TO_PN532)

        @param[in]  data            Frame's data in a bytearray().

        @param[in]  postamble       Postamble to be used.
                                    (default = PN532_PREAMBLE)

        """
        self._frame_type = frame_type
        self._preamble = preamble
        self._startCode1 = start_code_1
        self._startCode2 = start_code_2
        self._frameIdentifier = frame_identifier
        self._data = data
        self._postamble = postamble

    def get_length(self):
        """Gets the frame's data length."""
        return len(self._data) + 1

    def get_length_checksum(self):
        """Gets the checksum of get_length()."""
        return (~self.get_length() & 255) + 1

    def get_data(self):
        """Gets the frame's data."""
        return self._data

    def get_data_checksum(self):
        """Gets a checksum for the frame's data."""
        byte_array = bytearray()
        for byte in self._data:
            byte_array.append(byte)

        byte_array.append(self._frameIdentifier)
        inverse = (~sum(byte_array) & 255) + 1
        if inverse > 255:
            inverse -= 256
        return inverse

    def calc_data_checksum(self):
        byte_array = bytearray()
        byte_array.append(self._frameIdentifier)
        for byte in self._data:
            byte_array.append(byte)

        return -(sum(c for c in byte_array) % 256) & 255

    def get_frame_type(self):
        """Gets the frame's type."""
        return self._frame_type

    def to_tuple(self):
        byte_array = bytearray()
        if self._frame_type == PN532_FRAME_TYPE_ACK:
            byte_array.append(PN532_PREAMBLE)
            byte_array.append(PN532_START_CODE_1)
            byte_array.append(PN532_START_CODE_2)
            byte_array.append(PN532_START_CODE_1)
            byte_array.append(PN532_START_CODE_2)
            byte_array.append(PN532_POSTAMBLE)
            return byte_array
        if self._frame_type == PN532_FRAME_INIT:
            byte_array.append(PN532_START_CODE_3)
            byte_array.append(PN532_START_CODE_3)
            byte_array.append(PN532_PREAMBLE)
            byte_array.append(PN532_PREAMBLE)
            byte_array.append(PN532_PREAMBLE)
        byte_array.append(self._preamble)
        byte_array.append(self._startCode1)
        byte_array.append(self._startCode2)
        byte_array.append(self.get_length())
        byte_array.append(self.get_length_checksum())
        byte_array.append(self._frameIdentifier)
        for byte in self._data:
            byte_array.append(byte)

        byte_array.append(self.get_data_checksum())
        byte_array.append(self._postamble)
        return byte_array

    @staticmethod
    def from_response(response):
        response = bytearray(response)
        if len(response) < 6:
            return Pn532Frame(frame_type=PN532_FRAME_TYPE_ERROR, frame_identifier=127, data='\x81')
        if Pn532Frame.is_valid_response(response) is not True:
            return Pn532Frame(frame_type=PN532_FRAME_TYPE_ERROR, frame_identifier=127, data='\x81')
        if Pn532Frame.is_ack(response):
            return Pn532Frame(frame_type=PN532_FRAME_TYPE_ACK, frame_identifier=0)
        if Pn532Frame.is_error(response):
            return Pn532Frame(frame_type=PN532_FRAME_TYPE_ERROR, frame_identifier=127, data='\x81')
        if len(response) < PN532_ACK_LENGTH + PN532_FRAME_POSITION_LENGTH + 1:
            return Pn532Frame(frame_type=PN532_FRAME_TYPE_ERROR, frame_identifier=127, data='\x81')
        try:
            response_length = response[3]
            data = response[6:6 + response_length - 1]
            _frame = Pn532Frame(preamble=response[0], start_code_1=response[1], start_code_2=response[2], frame_identifier=response[5], data=data, postamble=response[(5 + response_length + 1)])
            if response[4] != _frame.get_length_checksum():
                debug_message.print_message('error get length checksum')
                return Pn532Frame(frame_type=PN532_FRAME_TYPE_ERROR, frame_identifier=127, data='\x81')
            if response[(5 + response_length)] != _frame.get_data_checksum():
                debug_message.print_message('error get data checksum')
                return Pn532Frame(frame_type=PN532_FRAME_TYPE_ERROR, frame_identifier=127, data='\x81')
            return _frame
        except Exception as e:
            debug_message.print_message('-------------RFID1356 FRAME-----------------')
            debug_message.print_message(e)
            debug_message.print_message('-------------!RFID1356 FRAME----------------')
            return Pn532Frame(frame_type=PN532_FRAME_TYPE_ERROR, frame_identifier=127, data='\x81')

    @staticmethod
    def is_valid_response(response):
        """Checks if a response from the PN532 is valid."""
        if response[PN532_FRAME_POSITION_PREAMBLE] == PN532_PREAMBLE:
            if response[PN532_FRAME_POSITION_START_CODE_1] == PN532_START_CODE_1:
                if response[PN532_FRAME_POSITION_START_CODE_2] == PN532_START_CODE_2:
                    return True
        return False

    @staticmethod
    def is_ack(response):
        """Checks if the response is an ACK frame."""
        if len(response) == 6:
            return True
        return False

    @staticmethod
    def is_error(response):
        """ Checks if the response is an error frame."""
        if response[PN532_FRAME_POSITION_LENGTH] == 1:
            if response[PN532_FRAME_POSITION_LENGTH_CHECKSUM] == 255:
                if response[PN532_FRAME_POSITION_FRAME_IDENTIFIER] == 127:
                    if response[PN532_FRAME_POSITION_DATA_START] == 129:
                        return True
        return False