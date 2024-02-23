# uncompyle6 version 3.4.0
# Python bytecode 2.7 (62211)
# Decompiled from: Python 2.7.15+ (default, Jul  9 2019, 16:51:35) 
# [GCC 7.4.0]
# Embedded file name: /home/user/zeus/eth.py
# Compiled at: 2017-06-01 15:16:10
import os, subprocess, sys

class Eth:

    def __init__(self):
        self.eth0_file = '/sys/devices/platform/fec.0/net/eth0/operstate'
        self.eth1_file = '/sys/devices/platform/fec.1/net/eth1/operstate'

    def run_cmd_thread(self, _cmd=''):
        p = subprocess.Popen(_cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        p.communicate('q')
        p.stdout.close()
        sys.stdout.flush()

    def network_check(self):
        _status = False
        if os.path.isfile(self.eth0_file):
            with open(self.eth0_file, 'r') as (_file):
                _content = _file.read()
                if 'up' in _content:
                    print 'Eth0 is up'
                    _status = True
                else:
                    print 'Eth0 is down'
        if os.path.isfile(self.eth1_file):
            with open(self.eth1_file, 'r') as (_file):
                _content = _file.read()
                if 'up' in _content:
                    print 'Eth1 is up'
                    print 'Down eth1'
                    self.run_cmd_thread('ifconfig eth1 down')
                else:
                    print 'Eth1 is down'
        if not _status:
            print 'Rerun eth0'
            self.run_cmd_thread('ifconfig eth1 down')
            self.run_cmd_thread('ifconfig eth0 down')
            self.run_cmd_thread('ifconfig eth0 up')
# okay decompiling /home/a/Desktop/app/eth.pyc
