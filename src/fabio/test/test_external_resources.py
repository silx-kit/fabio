#
#    Project: X-ray image reader
#             https://github.com/silx-kit/fabio
#
#
#    Copyright (C) European Synchrotron Radiation Facility, Grenoble, France
#
#    Principal author:       Jérôme Kieffer (Jerome.Kieffer@ESRF.eu)
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#  .
#  The above copyright notice and this permission notice shall be included in
#  all copies or substantial portions of the Software.
#  .
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
#  THE SOFTWARE.
"""Tests for the download of test data (`fabio.utils.ExternalResources`)"""

import bz2
import gzip
import io
import json
import os
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

from ..utils.ExternalResources import ExternalResources


class TestDownload(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.resources = ExternalResources("fabio_test", "http://localhost/none", data_home=self.tmp.name)
        # a proxy would make `getfile` use `build_opener` instead of `urlopen`
        env = {k: v for k, v in os.environ.items() if k.lower() not in ("http_proxy", "https_proxy")}
        patcher = mock.patch.dict(os.environ, env, clear=True)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_response_is_closed(self):
        """The response of the download is closed (#678: ResourceWarning on unclosed socket)"""
        response = mock.MagicMock()
        response.__enter__.return_value = response
        response.read.return_value = b"data"
        with mock.patch("urllib.request.urlopen", return_value=response):
            filename = self.resources.getfile("file.bin")
        with open(filename, "rb") as fd:
            self.assertEqual(fd.read(), b"data")
        response.__exit__.assert_called_once()

    def test_http_error_is_closed(self):
        """The HTTPError holds the response of the server: it is closed (#678)"""
        fp = io.BytesIO(b"not found")
        error = urllib.error.HTTPError("http://localhost/none/file.bin", 404, "Not Found", {}, fp)
        with mock.patch("urllib.request.urlopen", side_effect=error), self.assertRaises(unittest.SkipTest):
            self.resources.getfile("file.bin")
        self.assertTrue(fp.closed)


    def test_bug_153(self):
        """Reuse cached bzip2 test data when the repacked files are missing (#153)."""
        cache = Path(self.tmp.name)
        data = b"fixture data"
        compressed = cache / "image.bin.bz2"
        compressed.write_bytes(bz2.compress(data))
        (cache / "all_testdata.json").write_text(
            json.dumps({compressed.name: self.resources.get_hash(compressed.name)}),
            encoding="utf-8",
        )

        with mock.patch("urllib.request.urlopen") as urlopen:
            filename = self.resources.get_file_and_repack(compressed.name)

        urlopen.assert_not_called()
        self.assertEqual(Path(filename), compressed)
        self.assertTrue((cache / "image.bin").is_file())
        self.assertEqual((cache / "image.bin").read_bytes(), data)
        self.assertEqual(gzip.decompress((cache / "image.bin.gz").read_bytes()), data)


def suite():
    loadTests = unittest.defaultTestLoader.loadTestsFromTestCase
    testsuite = unittest.TestSuite()
    testsuite.addTest(loadTests(TestDownload))
    return testsuite


if __name__ == "__main__":
    runner = unittest.TextTestRunner()
    runner.run(suite())
