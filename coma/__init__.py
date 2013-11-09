__version__ = 'unknown'

try:
    from ._version import __version__
except ImportError:
    pass

from .experiment import Experiment, ExperimentError, ParameterSet, Result, ResultList
from .measurement import Measurement
from .serialization import XMLArchive, XMLArchiveError, JsonArchive, \
                           JsonArchiveError, Serializer, Restorer, Archive, \
                           ArchiveError, archive_exists
from .config import Config
from .indexfile import IndexFile
import test
