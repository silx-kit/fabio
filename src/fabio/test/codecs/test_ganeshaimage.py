"""SAXSLAB Ganesha TIFF metadata regression tests (#336)."""

import io
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import numpy
from PIL import Image

import fabio
from fabio import TiffIO, fabioformats, tifimage


class TestGanesha(unittest.TestCase):
    description = "# Pixel_size 172e-6 m x 172e-6 m\r\n# Exposure_time 900 s\r\n"
    artist = (
        '<?xml version="1.0"?><SAXSLABparameters>'
        '<param name="detector_dist">129.9995</param>'
        '<param name="sample_ID">A &amp; B &#181;m</param>'
        '<param name="sample_temp"></param>'
        '<param name="wavelength" unit="angstrom">1.5418</param>'
        "</SAXSLABparameters>"
    )

    def setUp(self):
        self.data = numpy.arange(12, dtype=numpy.int32).reshape(3, 4) - 2

    def make_tiff(self, artist=artist):
        stream = io.BytesIO()
        tags = {270: self.description}
        if artist is not None:
            tags[315] = artist
        Image.fromarray(self.data).save(stream, format="TIFF", tiffinfo=tags)
        stream.seek(0)
        return stream

    def reader(self):
        self.assertIn("ganeshaimage", [c.codec_name() for c in fabioformats.get_all_classes()])
        return fabio.factory("ganeshaimage")

    def test_bug_336_artist(self):
        """Expose tag 315 without parsing it in the generic TIFF reader."""
        for use_tiffio in (True, False):
            with (
                self.subTest(tiffio=use_tiffio),
                mock.patch.object(tifimage, "_USE_TIFFIO", use_tiffio),
                tifimage.TifImage().read(self.make_tiff()) as image,
            ):
                numpy.testing.assert_array_equal(image.data, self.data)
                self.assertEqual(image.header.get("artist"), self.artist)
                self.assertEqual(image.lib, "TiffIO" if use_tiffio else "PIL")

    def test_bug_336_headers(self):
        """Both original header blocks must survive either TIFF backend."""
        for use_tiffio in (True, False):
            with (
                self.subTest(tiffio=use_tiffio),
                mock.patch.object(tifimage, "_USE_TIFFIO", use_tiffio),
                self.reader().read(self.make_tiff()) as image,
            ):
                numpy.testing.assert_array_equal(image.data, self.data)
                self.assertEqual(image.lib, "TiffIO" if use_tiffio else "PIL")
                self.assertEqual(
                    dict(image.header),
                    {
                        "Pixel_size": "172e-6 m x 172e-6 m",
                        "Exposure_time": "900 s",
                        "detector_dist": "129.9995",
                        "sample_ID": "A & B µm",
                        "sample_temp": None,
                        "wavelength": "1.5418",
                    },
                )

    def test_frame(self):
        with self.reader().read(self.make_tiff()) as image:
            frame = image.getframe(0)
            numpy.testing.assert_array_equal(frame.data, self.data)
            self.assertEqual(frame.header, image.header)
            self.assertEqual(frame.tiff_header["artist"], self.artist)
            self.assertEqual(frame.pilatus_header["Exposure_time"], "900 s")
            self.assertEqual(frame.ganesha_header["detector_dist"], "129.9995")

    def test_duplicates(self):
        reader = self.reader()
        for second, conflict in (("129.9995", False), ("130", True)):
            artist = self.artist.replace(
                "</SAXSLABparameters>", f'<param name="detector_dist">{second}</param></SAXSLABparameters>'
            )
            with (
                self.subTest(second=second),
                mock.patch("fabio.ganeshaimage._logger.warning") as warning,
                reader.read(self.make_tiff(artist)) as image,
            ):
                self.assertEqual(image.header["detector_dist"], "129.9995")
                self.assertEqual(warning.call_count, int(conflict))

    def test_separate_images(self):
        with self.reader().read(self.make_tiff()) as first:
            expected = first.header.copy()
            with self.reader().read(
                self.make_tiff('<SAXSLABparameters><param name="other">2</param></SAXSLABparameters>')
            ) as second:
                self.assertNotIn("detector_dist", second.header)
                self.assertEqual(second.header["other"], "2")
                self.assertEqual(first.header, expected)

    def test_non_ganesha_artist(self):
        for artist in (None, "An ordinary TIFF author", "<SAXSLABparameters>", "<different/>"):
            with self.subTest(artist=artist), self.reader() as image, self.assertRaises(OSError):
                image.read(self.make_tiff(artist))

    def test_tiff_without_artist(self):
        with tifimage.TifImage().read(self.make_tiff(None)) as image:
            self.assertNotIn("artist", image.header)
            numpy.testing.assert_array_equal(image.data, self.data)

    def test_tiffio_filename(self):
        """Reading metadata must work when TiffIO owns and closes the file."""
        with tempfile.TemporaryDirectory() as directory:
            filename = Path(directory) / "ganesha.tiff"
            filename.write_bytes(self.make_tiff().getvalue())
            with TiffIO.TiffIO(str(filename)) as image:
                self.assertEqual(image.getInfo(0).get("artist"), self.artist)
                numpy.testing.assert_array_equal(image.getData(0), self.data)


def suite():
    return unittest.defaultTestLoader.loadTestsFromTestCase(TestGanesha)
