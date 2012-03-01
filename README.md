Introduction
----

This package contains tools for creating thumbnail images from a variety of document formats.
It accomplishes this by using the UNO package which is part of OO.org/LibreOffice. UNO allows
Python to control an instance of the office suite via a socket connection. This is not a trivial
process so, this package includes many tools to make thumbnailing suitable for a variety of use-
cases.

Command Line Tools
----

This package includes a tool named thumb which will perform thumbnail generation for your shell.
This tool also aids in spawning the soffice server.

Conversion Library
----

The library returns the thumbnail as a StringIO instance containing a .png image.

If you are only creating one thumbnail, you can use the library directly. For the first thumbnail
a connection is opened to soffice. This can take some time, so the first thumbnail may take several
seconds to create. However, connections are pooled, so any subsequent thumbnails of office documents
will automatically reuse an existing connection.

```python
from thumbnailer import library as thumb

# Use the default width and height:
image = thumb.create('path_to.png')
# Specify the optional width and height (default is 128x128):
image = thumb.create('path_to.png', width=100, height=200)
```

The create function will detect the file type and create a thumbnail for it. It will use one or a
combination of several backends to create the thumbnail.

The first argument can be a path, or a file-like object. If the file-like object is actually an open
file or other file-like object with a `name` attribute, that attribute will be used for type detection.
Otherwise, you can must provide the optional `file_name` parameter, which will be used for type
detection.

If for some reason, you want more control over what backend is used, you can instantiate a backend
and use it directly.

```python
from thumbnailer.library import OfficeBackend

# Use the default width and height:
backend = OfficeBackend()
image = backend.create('path_to.docx')

# Specify the width and height for backend:
backend = OfficeBackend(width=100, height=200)
image = backend.create('path_to.docx')

# Override the width and height when calling create()
image = backend.create('path_to.docx', width=200, height=300)
```

There are four backends. Python inheritance is used to provide a step by step conversion from the
given file to the desired thumbnail image.

- ImageBackend - Converts an image to a smaller thumbnail image. This backend uses PIL.
    - PdfBackend - Converts a PDF to an Image. This backend uses GhostScript.
        - OfficeBackend - Converts an office document to a PDF. This backend used UNO and soffice.
    - VideoBackend - Converts a video to an image by grabbing the first frame.

If you use the OfficeBackend, it will convert the office document to a one page PDF file, then pass
the result to it's base class PdfBackend to convert that to an image. The resulting image will then
be handed off to the base class ImageBackend for final resize into a thumbnail.

Conversion Server
----

As is often the case, thumbnail creation requiring a running instance of soffice is not always something
you want to do on your webserver. Thus, if you are planning to use this package in conjunction with a
Django web application, you can also use the client/server model.

In addition to the conversion library, this package provides a simple asynchronous HTTP server that
does the conversion of documents to images. This HTTP server supports a simple REST API for performing
conversions. There is also a client provided for use in your web application. This server has not been
audited for security problems, so it is not suggested that you expose it to your users via the Internet.

The server is provided as a module, which you can use to build your own server. It is packaged with a
runnable demo server. The demo server can also spawn soffice, to ensure it is available. To run the demo
server do the following.

```
$ python thumbnailer/server.py
```

There are a number of arguments you can pass to the demo server.

Conversion Client
----

A client library is provided for interfacing with the conversion server. This client is a class which
you can import and then use to communicate with the server. The thumb CLI tool also has a mode to use
the server client rather than the library directly.

REST API
----

The conversion server can receive jobs via either a POST or GET request.

A POST is expected to provide a Content-Type header indicating the document format. The request
body should contain the document itself.

A GET request should provide a URL that is accessible to the conversion server. That is, the URL
should be valid for the conversion server to read the document. The format will be determined
by the file's extension. file:// is a valid scheme for the URL, in which case, the document is
read directly from disk.

In either case, the width and height can optionally be provided on the query string. If omitted, the
default of 128x128 is used.

The following flow illustrates what happens within the conversion server in response to either a
POST or GET request.

POST only:

- The document content (POST body) is written to a temporary file.

GET only:

- If the URL is a network location, the document content is fetched and written to a temporary
file. For a file:// URL, this step is skipped.

POST or GET:

- The proper backend is selected and the .png file is returned to the caller.
- Headers are included to control upstream caching.
- Any temporary files are cleaned up after handling the request.
