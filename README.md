# fs.youtube


A PyFilesystem2 implementation for accessing DLNA Servers


Installation
------------

Install directly from PyPI, using [pip](<https://pip.pypa.io/>):

    pip install fs.dlna

Usage
-----

### Opener

Use ``fs.open_fs`` to open a filesystem with an Youtube
[FS URL](<https://pyfilesystem2.readthedocs.io/en/latest/openers.html>):

```python
import fs
yt_fs = fs.open_fs('dlna:///')
```


### Constructor

```python
import fs.dlna
dlna_fs = fs.dlna.DLNAFS(timeout=10)
```

with each argument explained below:

``timeout``
  The Scantime for DLNA/UPNP Devices

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