# coding: utf-8
from __future__ import absolute_import
from __future__ import unicode_literals
from __future__ import with_statement

import json

import upnpclient
import xmltodict
from fs.path import iteratepath

from .. import errors
from ..base import FS
from ..enums import ResourceType
from ..info import Info


class DLNAFS(FS):
    def __init__(self):
        self.devices = []
        self.scan()

    def scan(self, timeout=2):
        self.devices = {}

        devices = upnpclient.discover(timeout=timeout)
        for device in devices:
            if 'ContentDirectory' not in device.service_map:
                continue

            self.devices[device.friendly_name] = device

    def parse(self, device, oid, start=0, count=100):
        xml = device.ContentDirectory.Browse(
            ObjectID=oid,
            BrowseFlag='BrowseDirectChildren',
            Filter='*',
            StartingIndex=start,
            RequestedCount=count,
            SortCriteria=''
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

        if type(containers) != list:
            containers = [containers]
        if type(items) != list:
            items = [items]

        # Scan Containers
        for c in containers:
            name = c['http://purl.org/dc/elements/1.1/:title'].replace(':', '').replace('/', '')
            outdata[name] = {'id': c['@id'], 'folder': True, 'title': c['http://purl.org/dc/elements/1.1/:title']}

        # Scan Items
        print(json.dumps(items, indent=4))
        for i in items:
            if not 'urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/:res' in i:
                continue

            resinfo = i['urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/:res']
            if type(resinfo) == list:
                for e in resinfo:
                    if '@protocolInfo' in e:
                        if '@size' in e:
                            if 'http-get' in e['@protocolInfo'] and 'DLNA.ORG_PN' in e['@protocolInfo']:
                                print('######', e)
                                resinfo = e

            name = i['http://purl.org/dc/elements/1.1/:title'].replace(':', '').replace('/', '')
            outdata[name] = {'id': i['@id'], 'folder': False, 'title': i['http://purl.org/dc/elements/1.1/:title']}

            if type(resinfo) == list:
                print('type(resinfo) == list,check this case')
                print(json.dumps(resinfo, indent=4))
                continue

            outdata[name]['thumb'] = resinfo['#text']
            # print(resinfo)

            if '@size' in resinfo:
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
                outlist.append(device)
            return outlist

        pathiter = iteratepath(_path)
        devname = pathiter.pop(0)
        if not devname in self.devices:
            raise errors.ResourceNotFound(_path)
        device = self.devices[devname]
        parent = self.parseall(device, 0)

        # if len(pathiter) < 1:
        #     last_data = parent

        for entry in pathiter:
            # if not entry in parent:
            #     print('Error',entry,'not in',parent)
            # if not parent[entry]['folder']:
            #     raise errors.DirectoryExpected(_path)
            if not entry in parent:
                raise errors.ResourceNotFound(_path)
            parent = self.parseall(device, parent[entry]['id'])

        for name in parent:
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
