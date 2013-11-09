import os
from .serialization import Archive, archive_exists
from .config import Config

class IndexFile(object):
    def __init__(self, indexfile, indextype, config=Config()):
        self.element = ''
        archive_name = ''
        if indextype == 'experiment':
            archive_name = 'experiments'
            self.element = 'last_experiment_id'
        elif indextype == 'measurement':
            archive_name = 'measurements'
            self.element = 'last_measurement_id'
        self.archive = Archive(indexfile, archive_name, default_format=config.default_format)
        if not archive_exists(indexfile):
            self.createfile()

    def read(self):
        o = self.archive.load()
        return o[self.element]

    def increment(self):
        self.lock()
        o = self.archive.load()
        o[self.element] += 1
        lastid = o[self.element]
        self.archive.save(o)
        self.unlock()
        return lastid

    def createfile(self):
        o = {self.element: 0}
        self.lock()
        self.archive.save(o)
        self.unlock()

    def lock(self):
        lockfile = self.archive.filename + '.lock'
        if os.path.exists(lockfile):
            raise IOError('File "{}" is locked'.format(self.archive.filename))
        open(lockfile,'a').close()

    def unlock(self):
        lockfile = self.archive.filename + '.lock'
        os.remove(lockfile)
