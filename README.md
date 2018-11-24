# fs.dlna

[![PyPI version](https://badge.fury.io/py/fs.dlnafs.svg)](https://pypi.python.org/pypi/fs.dlnafs) [![Build Status](https://travis-ci.org/media-proxy/fs.dlna.svg?branch=master)](https://travis-ci.org/media-proxy/fs.dlna) [![Codacy Badge](https://api.codacy.com/project/badge/Grade/bcd41855125941bdbe61413f53e502e9)](https://www.codacy.com/app/media-proxy/fs.dlna?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=media-proxy/fs.dlna&amp;utm_campaign=Badge_Grade) [![codecov](https://codecov.io/gh/media-proxy/fs.dlna/branch/master/graph/badge.svg)](https://codecov.io/gh/media-proxy/fs.dlna) [![Updates](https://pyup.io/repos/github/media-proxy/fs.dlna/shield.svg)](https://pyup.io/repos/github/media-proxy/fs.dlna/)



A PyFilesystem2 implementation for accessing DLNA Servers


Installation
------------

Install directly from PyPI, using [pip](<https://pip.pypa.io/>):

    pip install fs.dlna

Usage
-----

### Opener

Use ``fs.open_fs`` to open a filesystem with a DLNA
[FS URL](<https://pyfilesystem2.readthedocs.io/en/latest/openers.html>):

```python
import fs
dlna_fs = fs.open_fs('dlna:///')
```


### Constructor

```python
import fs.dlna
dlna_fs = fs.dlna.DLNAFS()
```

with each argument explained below:


Once created, the ``DLNAFS`` filesystem behaves like any other filesystem
(see the [Pyfilesystem2 documentation](<https://pyfilesystem2.readthedocs.io>)).

Feedback
--------

Found a bug ? Have an enhancement request ? Head over to the
[GitHub issue tracker](<https://github.com/media-proxy/fs.dlna/issues>) of the
project if you need to report or ask something. If you are filling in on a bug,
please include as much information as you can about the issue, and try to
recreate the same bug in a simple, easily reproductible situation.

See also
--------

* [fs](<https://github.com/Pyfilesystem/pyfilesystem2>), the core Pyfilesystem2 library
* [Index of Filesystems](<https://www.pyfilesystem.org/page/index-of-filesystems/>), a list of PyFilesystem 2 implementations
