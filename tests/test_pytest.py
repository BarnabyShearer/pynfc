"""Need hardware to test fully."""

import sys

import pytest

sys.path = sys.path[2:]  # Hack: test sdist not checkout


import pynfc  # noqa: E402


def test_pynfc():
    # type: () -> None
    """Check we can initialize."""
    with pytest.raises(Exception) as e:
        pynfc.Nfc("pn532_uart:/dev/ttyFake:115200")
    assert "nfc_open" in str(e)
