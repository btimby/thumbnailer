import unittest
from PIL import Image
from thumbnailer import library as thumb

class ThumbnailerTestCase(unittest.TestCase):
    def assertDimensions(self, t):
        w, h = Image.open(t).size
        self.assertLessEqual(w, thumb.DEFAULT_WIDTH)
        self.assertLessEqual(h, thumb.DEFAULT_HEIGHT)

    def test_pdf(self):
        t = thumb.create('files/test.pdf')
        self.assertDimensions(t)

    def test_png(self):
        t = thumb.create('files/test.png')
        self.assertDimensions(t)

    def test_avi(self):
        t = thumb.create('files/test.avi')
        self.assertDimensions(t)

    def test_odt(self):
        t = thumb.create('files/test.odt')
        self.assertDimensions(t)


def main():
    unittest.main()

if __name__ == '__main__':
    main()
