__version__ = 'unknown'

try:
    from ._version import __version__
except ImportError:
    pass

from .experiment import Experiment, ExperimentError, ParameterSet, Result, ResultList
from .measurement import FileMeasurement, MemoryMeasurement
from .serialization import XMLArchive, XMLArchiveError, JsonArchive, \
                           JsonArchiveError, Serializer, Restorer, Archive, \
                           ArchiveError, archive_exists
from .config import Config
from .indexfile import IndexFile
import test
