import os, subprocess, tempfile, shutil
from PIL import Image
from . import unoclient
from .compat import StringIO

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
"Default arguments used with GhostScript."
FF_ARGS = (
    'ffmpeg',
    '-vframes', '1',
    '-ss', '1',
)
"Default arguments used with ffmpeg."

def create(f, **kwargs):
    """A convenience function to determine the correct backend, instantiate
    it, then ask it to create a thumbnail."""
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
    """A backend that uses the PIL library to resize an image to the requested
    dimensions."""
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
    """A backend that uses the ffmpeg command to grab the first frame of a video
    to an image. That image is then sent upstream to the ImageBackend for resizing."""
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
    """A backend that uses GhostScript to convert the first page of a PDF into
    an image. That image is then sent upstream to the ImageBackend for resizing."""
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
    """A backend that communicates with OO.o/LibreOffice via UNO. The office suite
    converts the document to a PDF, which is then sent upstream to the PdfBackend
    for conversion to an image."""
    def create(self, f):
        # Get an UNO client from the pool.
        with unoclient.client() as client:
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
            pdf = client.export_to_pdf(f)
        return super(OfficeBackend, self).create(pdf.getStream())


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
"Maps backends to the file extensions they support."
