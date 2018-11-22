# coding: utf-8
"""`DLNA` opener definition.
"""
from __future__ import absolute_import
from __future__ import unicode_literals

from fs.opener.base import Opener

__license__ = "MIT"
__copyright__ = "Copyright (c) 2017 merlink01"
__author__ = "merlink01"
__version__ = 'dev'

# Dynamically get the version of the main module
try:
    import pkg_resources

    _name = __name__.replace('.opener', '')
    __version__ = pkg_resources.get_distribution(_name).version
except Exception:  # pragma: no cover
    pkg_resources = None
finally:
    del pkg_resources


class DLNAOpener(Opener):
    """`DLNA` opener.
    """

    protocols = ['dlna']

    @staticmethod
    def open_fs(fs_url, parse_result, writeable, create, cwd):  # noqa: D102
        from ..dlna import DLNAFS
        dlna_fs = DLNAFS()
        return dlna_fs
