# Coma

## Overview

[Coma][] is the computational condensed matter physics programming toolkit. It
is a small Python library aiding with some aspects of conducting "numerical
experiments"---running computer simulations. Coma helps with storing and
managing data from numerical simulations and additionally includes a simple job
runner (with parallelization support), a flexible mechanism to extract data
from data files, and object serialization. This is the second iteration of the
library (version 2.x.x) which is different from and incompatible with [version
1][].

For a more detailed explanation of what Coma is, the features it provides and
what a typical workflow with Coma looks like, have a look at the documentation
([Notebook viewer][notebook],[pdf][]).

## Installation

Coma requires Python 2.7. Older or newer versions won't work. To install the
Python module, go to the Coma source directory and run the `setup.py` file.
    
    $ ./setup.py install

Or to install it into your home directory.

    $ ./setup.py install --user

## License

Coma is distributed under the two-clause BSD license. Have a look at the file
`LICENSE` for details.

---

Burkhard Ritter (<burkhard@seite9.de>), February 2014.

[Coma]: https://bitbucket.org/meznom/coma
[version 1]: https://bitbucket.org/cjchandler/coma-toolkit
[notebook]: #
[pdf]: #
