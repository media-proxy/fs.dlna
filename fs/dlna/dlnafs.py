# coding: utf-8
from __future__ import absolute_import
from __future__ import unicode_literals
from __future__ import with_statement

import json
import os

import six
import upnpclient
import xmltodict
from fs.path import iteratepath

from .seekable_http_file import SeekableHTTPFile
from .. import errors
from ..base import FS
from ..enums import ResourceType
from ..info import Info
from ..iotools import RawWrapper


class DLNAFS(FS):
    def __init__(self):
        self.devices = []
        self.scan()

    def __str__(self):
        return u'DLNAFS'

    def scan(self, timeout=2):
        self.devices = {}

        devices = upnpclient.discover(timeout=timeout)
        for device in devices:
            if 'ContentDirectory' not in device.service_map:
                continue

            self.devices[device.friendly_name] = device

    @classmethod
    def parse(self, device, oid, start=0, count=100):
        xml = device.ContentDirectory.Browse(
            ObjectID=str(oid),
            BrowseFlag=u'BrowseDirectChildren',
            Filter=u'*',
            StartingIndex=str(start),
            RequestedCount=str(count),
            SortCriteria=u''
        )

        results = xmltodict.parse(xml['Result'], process_namespaces=True)
        didl = results['urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/:DIDL-Lite']
        if not didl:
            return None

        outdata = {}

        containers = []
        items = []
        if 'urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/:container' in didl:
            containers = didl['urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/:container']
        if 'urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/:item' in didl:
            items = didl['urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/:item']

        if not isinstance(containers, (list)):
            containers = [containers]
                          
        if not isinstance(items, (list)):
            items = [items]

        # Scan Containers
        for c in containers:
            name = c['http://purl.org/dc/elements/1.1/:title'].replace(':', '').replace('/', '')
            outdata[name] = {'id': c['@id'], 'folder': True, 'title': c['http://purl.org/dc/elements/1.1/:title']}

        # Scan Items
        # print('################')
        # print(json.dumps(items, indent=4))
        # print('################')
        for i in items:
            if not 'urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/:res' in i:
                continue

            resinfo = i['urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/:res']
            if isinstance(resinfo, (list)):
                for e in resinfo:
                    if '@protocolInfo' in e:
                        if '@size' in e:
                            if 'http-get' in e['@protocolInfo'] and 'DLNA.ORG_PN' in e['@protocolInfo']:
                                # print('######', e)
                                resinfo = e

            if isinstance(resinfo, (list)):
                # print('#'*20)
                # print('type(resinfo) == list,check this case')
                # print(json.dumps(resinfo, indent=4))
                # print('#'*20)

                continue

            if  not '#text' in resinfo:
                print('#'*20)
                print('resinfo[#text] missing: "%s"'%repr(resinfo))
                print(json.dumps(resinfo, indent=4))
                print('#'*20)
                continue

            try:
                extension = os.path.splitext(resinfo['#text'])[1]
            except:
                extension = ''
            name = i['http://purl.org/dc/elements/1.1/:title'].replace(':', '').replace('/', '')
            if not name.endswith(extension):
                name = '%s%s' % (name, extension)

            outdata[name] = {'id': i['@id'], 'folder': False, 'title': i['http://purl.org/dc/elements/1.1/:title']}
            outdata[name]['url'] = resinfo['#text']

            if '@size' in resinfo:
                outdata[name]['size'] = resinfo['@size']

            if '@duration' in resinfo:
                outdata[name]['duration'] = resinfo['@duration']

            if '@bitrate' in resinfo:
                outdata[name]['bitrate'] = resinfo['@bitrate']

            if '@sampleFrequency' in resinfo:
                outdata[name]['sampleFrequency'] = resinfo['@sampleFrequency']

            if '@nrAudioChannels' in resinfo:
                outdata[name]['nrAudioChannels'] = resinfo['@nrAudioChannels']

            if '@resolution' in resinfo:
                outdata[name]['resolution'] = resinfo['@resolution']

            if '@protocolInfo' in resinfo:
                if 'video' in resinfo['@protocolInfo']:
                    outdata[name]['type'] = 'video'

                if 'audio' in resinfo['@protocolInfo']:
                    outdata[name]['type'] = 'audio'

                if 'pictures' in resinfo['@protocolInfo']:
                    outdata[name]['type'] = 'pictures'

                outdata[name]['size'] = resinfo['@size']

        return outdata

    def parseall(self, device, oid, steps=20):
        counter = 0
        complete = {}
        while 1:
            data = self.parse(device, oid, start=counter, count=steps)
            if not data:
                break
            complete.update(data)
            if len(data) < steps:
                break
            counter += steps
        return complete

    def listdir(self, path):
        _path = self.validatepath(path)
        outlist = []
        print('listdir', _path)
        if _path in [u'', u'.', u'/', u'./']:
            for device in self.devices:
                if six.PY2:
                    device = unicode(device)
                outlist.append(device)
            return outlist

        pathiter = iteratepath(_path)
        devname = pathiter.pop(0)
        if not devname in self.devices:
            raise errors.ResourceNotFound(_path)
        device = self.devices[devname]
        parent = self.parseall(device, 0)

        for entry in pathiter:
            if not entry in parent:
                raise errors.ResourceNotFound(_path)
            parent = self.parseall(device, parent[entry]['id'])

        for name in parent:
            if six.PY2:
                name = unicode(name)
            outlist.append(name)


        return outlist

    def getinfo(self, path, namespaces=None):
        _path = self.validatepath(path)
        namespaces = namespaces or ('basic')
        print('getinfo', path, namespaces)

        if _path in [u'', u'.', u'/', u'./']:

            info_dict = {
                "basic":
                    {
                        "name": '',
                        "is_dir": True
                    },
                "details":
                    {
                        "type": int(ResourceType.directory)
                    }
            }
            return Info(info_dict)
        else:
            pathiter = iteratepath(_path)
            devname = pathiter.pop(0)
            if not devname in self.devices:
                raise errors.ResourceNotFound(_path)
            device = self.devices[devname]
            parent = self.parseall(device, 0)

            info_dict = {}
            if len(pathiter) < 1:
                info_dict['basic'] = {
                    "name": devname,
                    "is_dir": True
                }
                info_dict['details'] = {
                    "type": int(ResourceType.directory),
                }
            else:
                name = pathiter.pop()
                for entry in pathiter:
                    if not parent[entry]['folder']:
                        raise errors.DirectoryExpected(_path)

                    parent = self.parseall(device, parent[entry]['id'])
                if not name in parent:
                    raise errors.ResourceNotFound(_path)

                child = parent[name]
                info_dict['basic'] = {
                    "name": name,
                    "is_dir": child['folder']
                }
                if child['folder']:
                    info_dict['details'] = {
                        "type": int(ResourceType.directory),
                    }
                else:
                    info_dict['details'] = {
                        "type": int(ResourceType.file),
                    }


            print(Info(info_dict))
            return Info(info_dict)

    def openbin(self, path, mode=u'r', *args, **kwargs):
        _path = self.validatepath(path)

        if mode == 'rt':
            raise ValueError('rt mode not supported in openbin')

        if mode == 'h':
            raise ValueError('h mode not supported in openbin')

        if not 'r' in mode:
            raise errors.Unsupported()

        pathiter = iteratepath(_path)
        devname = pathiter.pop(0)
        if not devname in self.devices:
            raise errors.ResourceNotFound(_path)
        device = self.devices[devname]
        parent = self.parseall(device, 0)

        name = pathiter.pop()
        for entry in pathiter:
            if not parent[entry]['folder']:
                raise errors.DirectoryExpected(_path)
            parent = self.parseall(device, parent[entry]['id'])

        child = parent[name]
        print(child)
        if not 'url' in child:
            print('#################ERROR')
            print('Need url in',child)
            raise IOError
        response = SeekableHTTPFile(child['url'])
        return RawWrapper(response, mode=mode)


    @classmethod
    def makedir(self, *args, **kwargs):
        raise errors.Unsupported()

    @classmethod
    def remove(self, *args, **kwargs):
        raise errors.Unsupported()

    @classmethod
    def removedir(self, *args, **kwargs):
        raise errors.Unsupported()

    @classmethod
    def setinfo(self, *args, **kwargs):
        raise errors.Unsupported()
