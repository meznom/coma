# Copyright (c) 2013, Burkhard Ritter
# This code is distributed under the two-clause BSD License.

__version__ = 'unknown'

try:
    from ._version import __version__
except ImportError:
    pass

from .experiment import Experiment, ExperimentError, ParameterSet, Result, ResultList
from .parallelexperiment import ParallelExperiment
from .measurement import FileMeasurement, MemoryMeasurement
from .serialization import XMLArchive, XMLArchiveError, JsonArchive, \
                           JsonArchiveError, Serializer, Archive, \
                           ArchiveError, archive_exists, RecursiveSerializer
from .config import expand_path, load_config, create_config_file, \
                    create_default_config
from .indexfile import IndexFile
from . import test
