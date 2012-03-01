import os, subprocess, tempfile, shutil
from PIL import Image
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

DEFAULT_WIDTH, DEFAULT_HEIGHT = 128, 128
GS_ARGS = (
    'gs',
    '-q',
    '-dSAFER',
    '-dNOPAUSE',
    '-dBATCH',
    '-sDEVICE=png48',
    '-sOutputFile=-',
    '-dFirstPage=1',
    '-dLastPage=1',
)
FF_ARGS = (
    'ffmpeg',
    '-vframes', '1',
    '-ss', '1',
)
UC_ARGS = (
    'unoconv',
)

def create(f, **kwargs):
    if isinstance(f, basestring):
        ext = os.path.splitext(f)[1]
    else:
        ext = os.path.splitext(getattr(f, 'name'))[1]
    backend = None
    for klass, extensions in BACKEND_SUPPORT.items():
        if ext in extensions:
            backend = klass(**kwargs)
            break
    if backend is None:
        raise Exception('Unsupported format {0}'.format(ext))
    return backend.create(f)


class ImageBackend(object):
    def __init__(self, width=DEFAULT_WIDTH, height=DEFAULT_HEIGHT):
        self.width = width
        self.height = height

    def create(self, f):
        image = Image.open(f)
        image.thumbnail((self.width, self.height), Image.ANTIALIAS)
        thumb = StringIO()
        image.save(thumb, 'png')
        thumb.seek(0)
        return thumb


class VideoBackend(ImageBackend):
    def create(self, f):
        args = list(FF_ARGS)
        if isinstance(f, basestring):
            args.extend(('-i', str(f)))
            input = None
        else:
            args.extend(('-i', ' pipe:0'))
            input = f.read()
        o, fname = tempfile.mkstemp(suffix='.png')
        os.close(o)
        args.append(fname)
        stdout, stderr = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate(input)
        return super(VideoBackend, self).create(fname)


class PdfBackend(ImageBackend):
    def create(self, f):
        args = list(GS_ARGS)
        if not isinstance(f, basestring):
            o, fname = tempfile.mkstemp()
            try:
                with os.fdopen(o, 'w') as o:
                    shutil.copyfileobj(f, o)
            finally:
                f.close()
            f = fname
        args.append(f)
        stdout, stderr = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
        return super(PdfBackend, self).create(StringIO(stdout))


class OfficeBackend(PdfBackend):
    # TODO: perhaps import unoconv and use some of it's internals.
    # Particularly it would be nice to use a persistent server (OO.org/LibreOffice).
    def __init__(self, connection=None, width=DEFAULT_WIDTH, height=DEFAULT_HEIGHT):
        from . import unoclient
        super(OfficeBackend, self).__init__(width, height)
        if connection is None:
            connection = os.environ.get('UNO_CONNECTION', None)
        if connection is None:
            raise Exception('You must provide the UNO connection information. Either use the ' \
                            'connection kwarg, or set the UNO_CONNECTION environment variable.')
        self.client = unoclient.Client(connection)

    def create(self, f):
        args = list(UC_ARGS)
        if not isinstance(f, basestring):
            o, fname = tempfile.mkstemp()
            try:
                with os.fdopen(o, 'w') as o:
                    shutil.copyfileobj(f, o)
            finally:
                f.close()
            f = fname
        o, fname = tempfile.mkstemp()
        os.close(o)
        pdf = self.client.export_to_pdf(f)
        pdf.seek(0)
        return super(OfficeBackend, self).create(pdf.stream)


BACKEND_SUPPORT = {
    ImageBackend: (
        '.png', '.jpg', '.jpeg', '.jpe', '.gif', '.bmp', '.dib', '.dcx',
        '.eps', '.ps', '.im', '.pcd', '.pcx', '.pbm', '.pbm', '.ppm',
        '.psd', '.tif', '.tiff', '.xbm', '.xpm',
    ),
    VideoBackend: (
        '.mpg', '.mpeg', '.avi', '.wmv', '.mkv', '.fli', '.flc', '.flv', '.ac3',
        '.cin', '.vob'
    ),
    PdfBackend: (
        '.pdf',
    ),
    OfficeBackend: (
        '.odt', '.ods', '.odp', '.dot', '.docm', '.dotx', '.dotm', '.psw'
        '.doc', '.xls', '.ppt', '.wpd', '.wps', '.csv', '.sdw', '.sgl', '.vor'
        '.docx', '.xlsx', '.pptx', '.xlsm', '.xltx', '.xltm', '.xlt', '.xlw', '.dif'
        '.rtf', '.txt', '.pxl'
    )
}
