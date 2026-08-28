import base64
from io import BytesIO

import qrcode

# Lazy import - Code128 barcode is optional, same pattern as utils/label_generator.py
try:
	import barcode
	from barcode.writer import ImageWriter
	HAS_BARCODE = True
except ImportError:
	HAS_BARCODE = False


def get_gift_certificate_qr(data, box_size=8, border=1):
	"""
	Generate a QR code natively (via the `qrcode` library) and return it as a
	base64 data URI, ready to drop straight into an <img src="..."> tag in a
	Print Format - no call to an external QR service required.
	"""
	qr = qrcode.QRCode(box_size=box_size, border=border)
	qr.add_data(data)
	qr.make(fit=True)
	img = qr.make_image(fill_color="black", back_color="white")
	return _image_to_data_uri(img)


def get_gift_certificate_barcode(data, barcode_type="code128"):
	"""
	Generate a linear barcode (Code128 by default) natively via the
	`python-barcode` library and return it as a base64 data URI - no call to
	an external barcode service required.

	Falls back to a QR code if python-barcode isn't installed.
	"""
	if not HAS_BARCODE:
		return get_gift_certificate_qr(data)

	barcode_class = barcode.get_barcode_class(barcode_type)
	writer = ImageWriter()
	writer.dpi = 150
	barcode_obj = barcode_class(data, writer=writer)

	buffer = BytesIO()
	barcode_obj.write(buffer, options={"write_text": False})
	return f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode()}"


def _image_to_data_uri(img):
	buffer = BytesIO()
	img.save(buffer, format="PNG")
	return f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode()}"
