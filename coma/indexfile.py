import os
from .serialization import XMLArchive

class IndexFile(object):
    def __init__(self, indexfile, indextype):
        self.f = indexfile
        self.archive = ''
        self.element = ''
        if indextype == 'experiment':
            self.archive = 'experiments'
            self.element = 'last_experiment_id'
        elif indextype == 'measurement':
            self.archive = 'measurements'
            self.element = 'last_measurement_id'
        if not os.path.exists(self.f):
            self.createfile()

    def read(self):
        #self.mtime = os.path.getmtime(self.f)
        f = open(self.f)
        a = XMLArchive(self.archive)
        o = a.load(f)
        f.close()
        return o[self.element]

    def increment(self):
        self.lock()
        
        f = open(self.f, 'r+')
        a = XMLArchive(self.archive)
        o = a.load(f)
        o[self.element] += 1
        lastid = o[self.element]
        
        f.truncate(0)
        f.seek(0)
        a.dump(o,f)
        f.close()
        
        self.unlock()
        
        return lastid

    def createfile(self):
        self.lock()
        o = {self.element: 0}
        f = open(self.f, 'w')
        a = XMLArchive(self.archive)
        a.dump(o,f)
        f.close()
        self.unlock()

    def lock(self):
        lockfile = self.f + '.lock'
        if os.path.exists(lockfile):
            raise IOError('File "{}" is locked'.format(self.f))
        open(lockfile,'a').close()

    def unlock(self):
        lockfile = self.f + '.lock'
        os.remove(lockfile)
