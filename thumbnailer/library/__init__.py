import os, subprocess, tempfile, shutil, zipfile
from PIL import Image
from unoclient import client
from compat import StringIO

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

def get_backend(file_name):
    ext = os.path.splitext(file_name)[1]
    ext = ext.lower()
    backend = None
    for klass, extensions in BACKEND_SUPPORT.items():
        if ext in extensions:
            return klass

def get(f, **kwargs):
    """A convenience function to determine the correct backend, instantiate
    it, then ask it to create a thumbnail."""
    default = kwargs.pop('default', None)
    file_name = kwargs.pop('file_name', getattr(f, 'name', None))
    try:
        if isinstance(f, basestring):
            file_name = f
        else:
            if file_name is None:
                raise Exception('File name must be provided for type detection')
        backend = get_backend(file_name)
        if backend is None:
            raise Exception('Unsupported format {0}'.format(ext))
        return backend(**kwargs).get(f, file_name=file_name)
    except:
        if default:
            return default
        raise


class ImageBackend(object):
    """A backend that uses the PIL library to resize an image to the requested
    dimensions."""
    def __init__(self, width=DEFAULT_WIDTH, height=DEFAULT_HEIGHT):
        self.width = width
        self.height = height

    def get(self, f, file_name='', width=None, height=None):
        width = width or self.width
        height = height or self.height
        image = Image.open(f)
        image.thumbnail((width, height), Image.ANTIALIAS)
        thumb = StringIO()
        image.save(thumb, 'png')
        thumb.seek(0)
        return thumb


class VideoBackend(ImageBackend):
    """A backend that uses the ffmpeg command to grab the first frame of a video
    to an image. That image is then sent upstream to the ImageBackend for resizing."""
    def get(self, f, file_name='', width=None, height=None):
        args = list(FF_ARGS)
        if not isinstance(f, basestring):
            if hasattr(f, 'name'):
                f = f.name
            else:
                type = os.path.splitext(file_name)[1]
                t = tempfile.NamedTemporaryFile(suffix=type)
                try:
                    shutil.copyfileobj(f, t)
                    t.flush()
                finally:
                    f.close()
                f = t.name
        args.extend(('-i', f))
        o = tempfile.NamedTemporaryFile(suffix='.png')
        args.append(o.name)
        stdout, stderr = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
        return super(VideoBackend, self).get(o, width=width, height=height)


class PdfBackend(ImageBackend):
    """A backend that uses GhostScript to convert the first page of a PDF into
    an image. That image is then sent upstream to the ImageBackend for resizing."""
    def get(self, f, file_name='', width=None, height=None):
        args = list(GS_ARGS)
        if not isinstance(f, basestring):
            if hasattr(f, 'name'):
                f = f.name
            else:
                # Convert a file-like object to a file on disk.
                t = tempfile.NamedTemporaryFile(suffix='.pdf')
                try:
                    shutil.copyfileobj(f, t)
                    t.flush()
                finally:
                    f.close()
                f = t.name
        args.append(f)
        stdout, stderr = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
        return super(PdfBackend, self).get(StringIO(stdout), width=width, height=height)


class OfficeBackend(ImageBackend):
    def get(self, f, file_name='', width=None, height=None):
        # ZipFile requires seek:
        if not isinstance(f, basestring) and not hasattr(f, 'seek'):
            d = StringIO()
            shutil.copyfileobj(f, d)
            d.seek(0)
            f = d
        # Extract: 'Thumbnails/thumbnail.png'
        png = StringIO(zipfile.ZipFile(f, 'r').read('Thumbnails/thumbnail.png', 'r'))
        return super(OfficeBackend, self).get(png, width=width, height=height)


class UnoBackend(PdfBackend):
    """A backend that communicates with OO.o/LibreOffice via UNO. The office suite
    converts the document to a PDF, which is then sent upstream to the PdfBackend
    for conversion to an image."""
    def get(self, f, file_name='', width=None, height=None):
        # Get an UNO client from the pool.
        uno = client()
        try:
            if not isinstance(f, basestring):
                if hasattr(f, 'name'):
                    f = f.name
                else:
                    # Convert a file-like object to a file on disk.
                    type = os.path.splitext(file_name)[1]
                    t = tempfile.NamedTemporaryFile(suffix=type)
                    try:
                        shutil.copyfileobj(f, t)
                        t.flush()
                    finally:
                        f.close()
                    f = t.name
            pdf = uno.export_to_pdf(f)
        finally:
            uno.close()
        return super(UnoBackend, self).get(pdf.getStream(), width=width, height=height)


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
    OfficeBackend: (
        '.odt', '.ods', '.odp', 
    ),
    PdfBackend: (
        '.pdf',
    ),
    UnoBackend: (
        '.dot', '.docm', '.dotx', '.dotm', '.psw',
        '.doc', '.xls', '.ppt', '.wpd', '.wps', '.csv', '.sdw', '.sgl', '.vor',
        '.docx', '.xlsx', '.pptx', '.xlsm', '.xltx', '.xltm', '.xlt', '.xlw', '.dif',
        '.rtf', '.txt', '.pxl',
    )
}
"Maps backends to the file extensions they support."
