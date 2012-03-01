import os, uno
from unohelper import Base, systemPathToFileUrl
from com.sun.star.beans import PropertyValue
from com.sun.star.connection import NoConnectException
from com.sun.star.io import IOException, XOutputStream
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

# Taken from example:
# http://www.openoffice.org/udk/python/samples/ooextract.py

# To run in Foreground:
# soffice --accept=socket,host=localhost,port=2002;urp;
# To run headless:
# soffice --accept=socket,host=localhost,port=2002;urp; --headless

# Then set environment:
# UNO_CONNECTION="uno:socket,host=localhost,port=2002;urp;StarOffice.ComponentContext"

class OutputStream( Base, XOutputStream ):
    def __init__( self ):
        self.closed = 0
        self.stream = StringIO()

    def closeOutput(self):
        self.closed = 1

    def writeBytes( self, seq ):
        self.stream.write( seq.value )

    def seek(self, off):
        self.stream.seek(off)

    def flush( self ):
        pass


class Client(object):
    def __init__(self, connection):
        context = uno.getComponentContext()
        manager = context.ServiceManager
        resolver = manager.createInstanceWithContext(
            'com.sun.star.bridge.UnoUrlResolver',
            context,
        )
        try:
            context = resolver.resolve(connection)
        except NoConnectException:
            raise Exception('Invalid UNO connection information')
        manager = context.ServiceManager
        self.desktop = manager.createInstanceWithContext(
            'com.sun.star.frame.Desktop',
            context,
        )

    def export_to_pdf(self, path):
        stream = OutputStream()
        props_out = (
            PropertyValue('FilterName', 0, 'writer_pdf_Export', 0),
            PropertyValue('Overwrite', 0, True, 0),
            PropertyValue('OutputStream', 0, stream, 0),
            PropertyValue('PageRange', 0, 1, 0),
        )
        props_in = (
            PropertyValue('Hidden', 0, True, 0),
        )
        document = None
        try:
            pathUrl = systemPathToFileUrl(os.path.abspath(path))
            document = self.desktop.loadComponentFromURL(pathUrl, '_blank', 0, props_in)
            document.storeToURL('private:stream', props_out)
        finally:
            if document:
                document.dispose()
        return stream
