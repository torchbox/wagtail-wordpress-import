import io
import tempfile

from bs4 import BeautifulSoup
from PIL import Image


def get_soup(html, parser):
    soup = BeautifulSoup(html, parser)
    return soup


def mock_image(file_name="test.jpg", width=100, height=100, color="white"):
    file = io.BytesIO()
    image = Image.new("RGB", (width, height), color)
    image.save(file, "JPEG")
    file.name = file_name
    file.seek(0)
    return file


def mock_pdf():
    temp_file = tempfile.NamedTemporaryFile(suffix=".pdf")
    temp_file.write(b"PDF Document")
    return open(temp_file.name, mode="rb")
