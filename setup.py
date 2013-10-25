#!/usr/bin/env python

# This is largely taken from the python-ecdsa project,
# https://github.com/warner/python-ecdsa.
import os, sys, subprocess, re
from distutils.core import setup, Command, Extension
from distutils.command.sdist import sdist as _sdist
from distutils.command.install import install as _install

VERSION_PY_FILENAME = 'src/python/coma/_version.py'
VERSION_PY = """
# This file is originally generated from Git information by running 'setup.py
# version'. Distribution tarballs contain a pre-generated copy of this file.

__version__ = '{}'
"""

NOT_IN_PATH_MESSAGE = '''
Installed the coma script to "{}".
However, this directory does not seem to be in your path. To 
conveniently call the coma script on the command line, add
   export PATH="{}:$PATH"
to your "~/.bashrc" and restart your terminal.'''

def update_version_py():
    ver = 'unknown'
    try:
        p = subprocess.Popen(["git", "describe", "--dirty", "--always"],
                             stdout=subprocess.PIPE)
        stdout = p.communicate()[0]
        if p.returncode != 0:
            print('unable to run git')
        else:
            ver = stdout.strip()
    except EnvironmentError:
        print('unable to run git')
    if os.path.exists(VERSION_PY_FILENAME) and ver == 'unknown':
        return
    f = open(VERSION_PY_FILENAME, "w")
    f.write(VERSION_PY.format(ver))
    f.close()
    print('set {} to "{}"'.format(VERSION_PY_FILENAME, ver))

def get_version():
    try:
        f = open(VERSION_PY_FILENAME)
    except EnvironmentError:
        return None
    for line in f.readlines():
        mo = re.match("__version__ = '([^']+)'", line)
        if mo:
            ver = mo.group(1)
            return ver
    return None

class Version(Command):
    description = 'update _version.py from Git repo'
    user_options = []
    boolean_options = []
    def initialize_options(self):
        pass
    def finalize_options(self):
        pass
    def run(self):
        update_version_py()
        print 'Version is now', get_version()

class sdist(_sdist):
    def run(self):
        update_version_py()
        # unless we update this, the sdist command will keep using the old
        # version
        self.distribution.metadata.version = get_version()
        return _sdist.run(self)
    
class install(_install):
    def run(self):
        update_version_py()
        # unless we update this, the sdist command will keep using the old
        # version
        self.distribution.metadata.version = get_version()
        r = _install.run(self)
        
        # Check if the bin directory is in the user's path
        script_dir = self.install_scripts
        ps = os.environ['PATH'].split(':')
        if not (script_dir in ps or script_dir + '/' in ps):
            print(NOT_IN_PATH_MESSAGE.format(script_dir,script_dir))
        return r

setup(name='coma',
      version=get_version(),
      description='The computational condensed matter physics toolkit.',
      author='Burkhard Ritter',
      author_email='burkhard@ualberta.ca',
      url='https://bitbucket.org/cjchandler/coma-toolkit',
      scripts=['src/python/scripts/coma'],
      packages=['coma'],
      package_dir={'coma': 'src/python/coma'},
      package_data={'coma': ['data/templates/*/*']},
      cmdclass={'version': Version, 'sdist': sdist, 'install': install}
      )
