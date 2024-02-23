# uncompyle6 version 3.4.0
# Python bytecode 2.7 (62211)
# Decompiled from: Python 2.7.15+ (default, Oct  7 2019, 17:39:04) 
# [GCC 7.4.0]
# Embedded file name: /home/user/zeus/daemon.py
# Compiled at: 2017-06-11 20:13:04
import atexit, os, sys, signal, time

class Daemon(object):
    """
    A generic daemon class.

    Usage: subclass the Daemon class and override the run() method
    """

    def __init__(self, pidfile, stdin='/dev/null', stdout='/dev/null', stderr='/dev/null'):
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        self.pidfile = pidfile
        self.pid = 0

    def register_signal(self, signum):
        signal.signal(signum, self.signal_handler)

    def signal_handler(self, signum, frame):
        self.log('=============================')
        self.log('stop handle')
        self.log(signum)
        self.log(frame)
        self.log('=============================')
        self.shutdown()

    def shutdown(self):
        self.exit()
        return 1

    def daemonize(self):
        """
        do the UNIX double-fork magic, see Stevens' "Advanced
        Programming in the UNIX Environment" for details (ISBN 0201563177)
        http://www.erlenstar.demon.co.uk/unix/faq_2.html#SEC16
        """
        try:
            pid = os.fork()
            if pid > 0:
                sys.exit(0)
        except OSError as e:
            sys.stderr.write('fork #1 failed: %d (%s)\n' % (e.errno, e.strerror))
            sys.exit(1)
        else:
            os.chdir('/')
            os.setsid()
            os.umask(0)
            try:
                pid = os.fork()
                if pid > 0:
                    sys.exit(0)
            except OSError as e:
                sys.stderr.write('fork #2 failed: %d (%s)\n' % (e.errno, e.strerror))
                sys.exit(1)

        sys.stdout.flush()
        sys.stderr.flush()
        si = file(self.stdin, 'r')
        so = file(self.stdout, 'a+')
        se = file(self.stderr, 'a+', 0)
        os.dup2(si.fileno(), sys.stdin.fileno())
        os.dup2(so.fileno(), sys.stdout.fileno())
        os.dup2(se.fileno(), sys.stderr.fileno())
        atexit.register(self.delpid)
        pid = str(os.getpid())
        self.pid = pid
        file(self.pidfile, 'w+').write('%s\n' % pid)
        self.log('My pid is: ' + str(pid))

    @staticmethod
    def log(obj):
        if isinstance(obj, basestring):
            data = obj
        else:
            data = str(obj)
        sys.stdout.write(data)
        sys.stdout.write('\n')
        sys.stdout.flush()

    def delpid(self):
        if os.path.exists(self.pidfile):
            os.remove(self.pidfile)

    def start(self, os_start=False):
        """
        Start the daemon
        """
        if os_start:
            if os.path.exists(self.pidfile):
                os.remove(self.pidfile)
        self.register_signal(signal.SIGHUP)
        self.register_signal(signal.SIGTERM)
        self.register_signal(signal.SIGUSR1)
        try:
            pf = file(self.pidfile, 'r')
            pid = int(pf.read().strip())
            pf.close()
        except IOError:
            pid = None

        if pid:
            message = 'pidfile %s already exist. Daemon already running?\n'
            sys.stderr.write(message % self.pidfile)
            sys.exit(1)
        self.daemonize()
        self.run()
        return

    def stop(self):
        """
        Stop the daemon
        """
        self.log('Stop method')
        try:
            pf = file(self.pidfile, 'r')
            pid = int(pf.read().strip())
            pf.close()
            self.log('\tIn stop method')
        except IOError:
            pid = None

        if not pid:
            message = 'pidfile %s does not exist. Daemon not running?\n'
            sys.stderr.write(message % self.pidfile)
            return
        else:
            try:
                os.kill(pid, signal.SIGHUP)
            except OSError as err:
                err = str(err)
                self.log('\tIn stop method')
                if os.path.exists(self.pidfile):
                    os.remove(self.pidfile)
                else:
                    print 'Error stop: ' + str(err)
                    sys.exit(1)

            return

    def restart(self):
        """
        Restart the daemon
        """
        self.stop()
        _sleep_count = 0
        while os.path.exists(self.pidfile):
            time.sleep(0.1)
            _sleep_count += 0.1
            if _sleep_count > 20:
                break

        if not os.path.exists(self.pidfile):
            self.start()

    def run(self):
        """
        You should override this method when you subclass Daemon. It will be called after the process has been
        daemonized by start() or restart().
        """
        pass

    def exit(self):
        """
        You should override this method when you subclass Daemon. It will be called after the process has been
        daemonized by start() or restart().
        """
        pass