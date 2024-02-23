# uncompyle6 version 3.4.0
# Python bytecode 2.7 (62211)
# Decompiled from: Python 2.7.15+ (default, Oct  7 2019, 17:39:04) 
# [GCC 7.4.0]
# Embedded file name: /home/user/zeus/display_wrapper.py
# Compiled at: 2017-05-18 20:15:08
from lib import singleton
import os, sys, pty, select

@singleton
class DisplayWrapper:

    def __init__(self):
        self.host = '11.11.0.113'
        self.user = 'root'
        self.password = 'root'

    def set_host(self, host):
        self.host = host

    def _read(self, fd, rd_ready, rd_fds):
        if fd not in rd_ready:
            return
        else:
            try:
                data = os.read(fd, 1024)
            except (OSError, IOError):
                data = None
            else:
                try:
                    if not data:
                        rd_fds.remove(fd)
                except Exception as e:
                    pass

            return data

    def ssh_exec_pass(self, args, capture_output=False):
        try:
            _retval = None
            stdout_fd, w1_fd = os.pipe()
            stderr_fd, w2_fd = os.pipe()
            pid, pty_fd = pty.fork()
            if not pid:
                os.close(stdout_fd)
                os.close(stderr_fd)
                os.dup2(w1_fd, 1)
                os.dup2(w2_fd, 2)
                os.close(w1_fd)
                os.close(w2_fd)
                os.execvp(args[0], args)
            os.close(w1_fd)
            os.close(w2_fd)
            _output = bytearray()
            rd_fds = [stdout_fd, stderr_fd, pty_fd]
            while rd_fds:
                rd_ready, _, _ = select.select(rd_fds, [], [], 0.04)
                if rd_ready:
                    data = self._read(pty_fd, rd_ready, rd_fds)
                    os.write(pty_fd, bytes('q'))
                    if data is not None:
                        os.write(pty_fd, bytes('q\n'))
                    data = self._read(stdout_fd, rd_ready, rd_fds)
                    if data is not None:
                        if capture_output:
                            _output.extend(data)
                        else:
                            sys.stdout.write(data.decode('utf-8', 'ignore'))
                    data = self._read(stderr_fd, rd_ready, rd_fds)
                    if data is not None:
                        sys.stderr.write(data.decode('utf-8', 'ignore'))

        except Exception as e:
            print 'Error in display wrapper OSError IOError'
            print e
            os.close(pty_fd)
        else:
            try:
                _pid, _retval = os.waitpid(pid, 0)
            except (OSError, IOError):
                os.kill(pid, -9)
                print 'Error in display wrapper OSError IOError'

            try:
                os.kill(pid, -9)
            except Exception as e:
                print 'Display wrapper error killall'
                print e

        return (
         _retval, _output)

    def open_image(self, image):
        ret, out = self.ssh_exec_pass(['fbv', '--noinfo', image], True)
        print ret
        print out