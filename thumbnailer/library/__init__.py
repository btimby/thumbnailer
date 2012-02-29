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
    #'-f', 'image2',
    #'-c:v', 'png',
    #'pipe:1',
)
UC_ARGS = (
    'unoconv',
)

def create(f):
    if isinstance(f, basestring):
        ext = os.path.splitext(f)[1]
    else:
        ext = os.path.splitext(getattr(f, 'name'))[1]
    backend = None
    for klass, extensions in BACKEND_SUPPORT.items():
        if ext in extensions:
            backend = klass()
            break
    if backend is None:
        raise Exception('Unsupported format {0}'.format(ext))
    return backend.create(f)


class ImageBackend(object):
    def __init__(self):
        pass

    def create(self, f, width=DEFAULT_WIDTH, height=DEFAULT_HEIGHT):
        image = Image.open(f)
        image.thumbnail((width, height), Image.ANTIALIAS)
        thumb = StringIO()
        image.save(thumb, 'png')
        thumb.seek(0)
        return thumb


class VideoBackend(ImageBackend):
    def __init__(self):
        pass

    def create(self, f, width=DEFAULT_WIDTH, height=DEFAULT_HEIGHT):
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
        return super(VideoBackend, self).create(fname, width, height)


class PdfBackend(ImageBackend):
    def __init__(self):
        pass

    def create(self, f, width=DEFAULT_WIDTH, height=DEFAULT_HEIGHT):
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
        return super(PdfBackend, self).create(StringIO(stdout), width, height)


class OfficeBackend(PdfBackend):
    # TODO: perhaps import unoconv and use some of it's internals.
    # Particularly it would be nice to use a persistent server (OO.org/LibreOffice).
    def __init__(self, connection=None):
        pass

    def create(self, f, width=DEFAULT_WIDTH, height=DEFAULT_HEIGHT):
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
        args.append('--output={0}'.format(fname))
        args.append(f)
        stdout, stderr = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
        return super(OfficeBackend, self).create(fname, width, height)


BACKEND_SUPPORT = {
    ImageBackend: (
        '.png', '.jpg', '.jpeg', '.gif',
    ),
    VideoBackend: (
        '.mpg', '.mpeg', '.avi', '.wmv',
    ),
    PdfBackend: (
        '.pdf',
    ),
    OfficeBackend: (
        '.odt', '.ods', '.odp',
        '.doc', '.xls', '.ppt',
        '.docx', '.xlsx', '.pptx',
        '.rtf', '.txt'
    )
}
