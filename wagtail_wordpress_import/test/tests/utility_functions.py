import tempfile
from PIL import Image
from bs4 import BeautifulSoup


def get_soup(html, parser):
    soup = BeautifulSoup(html, parser)
    return soup


def mock_image():
    temp_file = tempfile.NamedTemporaryFile(suffix=".png")
    image = Image.new("RGB", (200, 200), "white")
    image.save(temp_file, "PNG")
    return open(temp_file.name, mode="rb")


def mock_pdf():
    temp_file = tempfile.NamedTemporaryFile(suffix=".pdf")
    temp_file.write(b"PDF Document")
    return open(temp_file.name, mode="rb")
