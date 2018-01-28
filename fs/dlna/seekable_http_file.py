from six.moves.urllib.request import BaseHandler
from six.moves.urllib.request import Request
from six.moves.urllib.request import build_opener
from six.moves.urllib.request import install_opener
from six.moves.urllib.request import urlopen
from six.moves.urllib.response import addinfourl

from .. import errors


class HTTPRangeHandler(BaseHandler):
    @classmethod
    def http_error_206(self, req, fp, code, msg, hdrs):
        # Range header supported
        r = addinfourl(fp, hdrs, req.get_full_url())
        r.code = code
        r.msg = msg
        return r

    @classmethod
    def http_error_416(self, req, fp, code, msg, hdrs):
        # Range header not supported
        raise URLError('Requested Range Not Satisfiable')


class SeekableHTTPFile:
    def __init__(self, url, *args, **kwargs):
        self.url = url
        self.pos = 0
        self.fileobj = None

        response = urlopen(url)
        response.close()

    def read(self, size=-1):
        if self.fileobj:
            self.fileobj.close()
        opener = build_opener(HTTPRangeHandler)
        install_opener(opener)

        if size < 0:
            rangeheader = {'Range': 'bytes=%s-' % (self.pos)}
        else:
            rangeheader = {'Range': 'bytes=%s-%s' % (self.pos, self.pos + size - 1)}

        req = Request(self.url, headers=rangeheader)
        res = urlopen(req)

        self.pos += size
        data = res.read()

        return data

    def tell(self):
        return self.pos

    def flush(self):
        pass

    def seek(self, offset, whence=0):
        """Seek within the byte range.
        Positioning is identical to that described under tell().
        """

        if whence == 0:  # absolute seek
            self.pos = offset
        elif whence == 1:  # relative seek
            self.pos += offset
        elif whence == 2:  # absolute from end of file
            raise errors.Unsupported('seek from end of file not supported.')
        else:
            raise errors.Unsupported('Whence must be 0, 1 or 2')

    def close(self):
        if self.fileobj:
            self.fileobj.close()

    @classmethod
    def writable(self):
        return False
