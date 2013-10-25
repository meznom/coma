import datetime
import os

class DirectoryError (Exception):
    pass

def current_date_as_string():
    return datetime.datetime.utcnow().replace(microsecond=0).isoformat() + 'Z'

def create_lockfile(filename):
    lockfile = filename + '.lock'
    if os.path.exists(lockfile):
        raise IOError('File "{}" is locked'.format(filename))
    open(lockfile,'a').close()

def remove_lockfile(filename):
    lockfile = filename + '.lock'
    os.remove(lockfile)

