from setuptools import setup, find_packages

# get version from __version__ variable in label_creator/__init__.py
from label_creator import __version__ as version

setup(
	name="label_creator",
	version=version,
	description="Create professional product labels with QR codes for ERPNext",
	author="Your Company",
	author_email="info@yourcompany.com",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=[
		"frappe",
		"qrcode>=7.4.2",
		"python-barcode>=0.15.1",
		"Pillow>=10.0.0",
		"reportlab>=4.0.4",
		"PyMuPDF>=1.23.0",
	]
)
