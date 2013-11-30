import os
from .serialization import Archive, archive_exists
from .config import Config

class IndexFile(object):
    def __init__(self, filename, indextype, default_format='json'):
        self.filename = filename
        self.element = ''
        archive_name = ''
        if indextype == 'experiment':
            archive_name = 'experiments'
            self.element = 'last_experiment_id'
        elif indextype == 'measurement':
            archive_name = 'measurements'
            self.element = 'last_measurement_id'
        self.archive = Archive(filename, archive_name, default_format=default_format)

    def get(self):
        if not self.exists():
            return 0
        o = self.archive.load()
        return o[self.element]

    def increment(self):
        if not self.exists():
            return 0
        self.lock()
        o = self.archive.load()
        o[self.element] += 1
        lastid = o[self.element]
        self.archive.save(o)
        self.unlock()
        return lastid

    def exists(self):
        return archive_exists(self.filename)

    def create(self):
        o = {self.element: 0}
        self.lock()
        self.archive.save(o)
        self.unlock()

    def remove(self):
        if self.exists():
            os.remove(self.archive.filename)

    def lock(self):
        lockfile = self.archive.filename + '.lock'
        if os.path.exists(lockfile):
            raise IOError('File "{}" is locked'.format(self.archive.filename))
        open(lockfile,'a').close()

    def unlock(self):
        lockfile = self.archive.filename + '.lock'
        os.remove(lockfile)
