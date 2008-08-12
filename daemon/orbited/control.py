import fcntl
import os
import sys
import time
import signal
from start import logger
from start import main as orbited_main
from config import map as config

pid_location = config['[global]']['pid.location']

def start():
    print "Starting Orbited Daemon"
    
    checkpidfile = open(pid_location, 'a')
    try:
        fcntl.lockf(checkpidfile , fcntl.LOCK_EX|fcntl.LOCK_NB)
        fcntl.lockf(checkpidfile , fcntl.LOCK_UN)
    except IOError:
        print "\tOrbited Daemon is already running"
        raise SystemExit
    checkpidfile.close()

    # Fork, creating a new process for the child.
    process_id = os.fork()
    if process_id < 0:
        # Fork error.  Exit badly.
        sys.exit(1)
    elif process_id != 0:
        # This is the parent process.  Exit.
        print "\tOrbited Daemon Started"
        sys.exit(0)
    try:
        devnull = '/dev/null'
        if hasattr(os, "devnull"):
            # Python has set os.devnull on this system, use it instead 
            # as it might be different than /dev/null.'
            devnull = os.devnull
        rnull_descriptor = open(devnull, 'r')
        wnull_descriptor = open(devnull, 'w')
        rnull_descriptor.read()
        wnull_descriptor.write('woot')
        sys.stdin.close()
        sys.stdout.close()
        sys.stderr.close()
        sys.stdin = rnull_descriptor
        sys.stdout = wnull_descriptor
        sys.stderr = wnull_descriptor
        # Set umask to default to safe file permissions when running
        # as a root daemon. 027 is an octal number.
        os.umask(027)
        # Change to a known directory.  If this isn't done, starting
        # a daemon in a subdirectory that needs to be deleted results
        # in "directory busy" errors.
        # On some systems, running with chdir("/") is not allowed
        os.chdir('/tmp')
        # Try to get an exclusive lock on the file.  This will fail
        # if another process has the file locked.
        pidfile = open(pid_location, 'w')    
        fcntl.lockf(pidfile, fcntl.LOCK_EX|fcntl.LOCK_NB)
        
        # Record the process id to the lockfile.  This is standard
        # practice for daemons.
        pidfile.write('%s' %(os.getpid()))
        pidfile.flush()
        orbited_main()
    except Exception, e:
        logger.error("Error: %s" % (e,), tb=True) 
        
def stop():
    print "Stopping Orbited Daemon"
    checkpidfile = open(pid_location, 'a')  
    try:
        fcntl.lockf(checkpidfile, fcntl.LOCK_EX|fcntl.LOCK_NB)
        fcntl.lockf(checkpidfile, fcntl.LOCK_UN)
    except IOError:
        pass
    else:
        print "\tOrbited Daemon is not running"
        raise SystemExit
      
    rpidfile = open(pid_location, 'r')
    try:
        pid = int(rpidfile.read())
    except ValueError:
        print "Invalid pid file: %s" % (pid_location,)
        raise SystemExit
    
    os.kill(pid, signal.SIGKILL)
    print "\tOrbited Daemon Stopped"

def restart():
    try:
        stop()
    except SystemExit:
        pass
    start()

def status():
    wpidfile = open(pid_location, 'a')  
    try:
        fcntl.lockf(wpidfile, fcntl.LOCK_EX|fcntl.LOCK_NB)
        fcntl.lockf(wpidfile, fcntl.LOCK_UN)
        print "Orbited Daemon is [ offline ]"
    except IOError:
        print "Orbited Daemon is [ online ]"

def main():
    import sys
    if len(sys.argv) < 2 or sys.argv[1] == 'status':
        status()
    elif sys.argv[1] == 'start':
        start()
    elif sys.argv[1] == 'stop':
        stop()
    elif sys.argv[1] == 'restart':
        restart()
        
