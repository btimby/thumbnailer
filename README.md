Introduction
----

This package contains tools for creating thumbnail images from a variety of document formats.
It accomplishes this by using the UNO package which is part of OO.org/LibreOffice. UNO allows
Python to control an instance of the office suite via a socket connection. This is not a trivial
process.

Conversion Library
----

If you are only creating one thumbnail, you can use the library directly. The startup cost is
high, so if you are creating more than one thumbnail, read the next section about the conversion
server.

```python
from thumbnailer import library as thumb

thumb.create('path_to.png')
```

The create function will detect the file type and create a thumbnail for it. It will use one or a
combination of several backends to create the thumbnail.

If for some reason, you want more control over what backend is used, you can instantiate a backend
and use it directly.

```python
from thumbnailer import library as thumb

backend = thumb.OfficeBackend()
backend.create('path_to.docx')
```

There are three backends.

- OfficeBackend - Converts an office document to a PDF. This backend used UNO and OO.org/LibreOffice.
- PdfBackend - Converts a PDF to an Image. This backend uses GhostScript.
- ImageBackend - Converts an image to a smaller thumbnail image. This backend uses PIL.

So, if you use the high level thumbnailer.library.create() function on a .docx file, all three
backends will be utilized. If you instead pass in a PDF file, only the PDFBackend and ImageBackend
will be used. For an image file, only the ImageBackend is necessary.

Conversion Server REST API
----

In addition to the conversion library, this package provides a simple asynchronous HTTP server that
does the conversion of documents to images. This HTTP server supports a simple REST API for
performing conversions. The server should be used when you plan on creating many thumbnails. Using
the server incurs the startup cost only once and is able to quickly generate thumbnails afterwards.

The conversion server can receive jobs via either a POST or GET request.

A POST is expected to provide a Content-Type header indicated the document format. The request
body should contain the document itself.

A GET request should provide a URL that is accessible to the conversion server. That is, the URL
should be valid for the conversion server to read the document. The format will be determined
by the file's extension. file:// is a valid scheme for the URL, in which case, the document is
read directly from disk.

The following flow illustrates what happens within the conversion server in response to either a
POST or GET request.

POST only:
- The document content (POST body) is written to a temporary file.

GET only:
- If the URL is a network location, the document content is fetched and written to a temporary
file. For a file:// URL, this step is skipped.

POST or GET:
- The document is submitted to the office suite for conversion to PDF.
- The PDF file is provided to ghostscript for conversion to PNG.
- The PNG file is returned to the caller.
- Temporary files are cleaned up after handling the request.
