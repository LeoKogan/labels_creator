# Label Creator for ERPNext

A professional label generation application for ERPNext that creates product labels with QR codes. This app allows you to generate PDF or Word documents containing formatted labels from CSV files with product information.

## Features

- **QR Code Generation**: Automatically generates QR codes for product SKUs
- **Multiple Label Formats**: Supports various label sheet formats (S-16987, A4-24, LETTER-30, etc.)
- **Flexible Output**: Generate labels in PDF or Word (.docx) format
- **CSV Import**: Process product data from CSV files
- **Batch Processing**: Handle multiple products and quantities in a single batch
- **Customizable Templates**: Easy to configure label dimensions and layouts
- **Price Display**: Show formatted prices on labels
- **Product Information**: Include SKU, product name, and pricing

## Installation

### Prerequisites

- Frappe/ERPNext installed
- Python 3.7 or higher
- Required Python packages (automatically installed)

### Install via Bench

1. Navigate to your bench directory:
```bash
cd frappe-bench
```

2. Get the app from the repository:
```bash
bench get-app https://github.com/yourusername/label_creator.git
```

3. Install the app on your site:
```bash
bench --site your-site-name install-app label_creator
```

4. Build assets:
```bash
bench build
```

5. Restart bench:
```bash
bench restart
```

6. **Configure Portal Settings** (to allow all users to access Label Creator):

   To make the Label Creator accessible to all portal users, add it to your Portal Settings:

   a. Go to **Setup > Website > Portal Settings** in ERPNext

   b. Scroll down to the **Custom Menu Items** section

   c. Click **Add Row** and enter:
      - **Title**: `Label Creator`
      - **Route**: `/label-creator`
      - **Enabled**: ✓ (checked)

   d. Click **Save**

   This will add a "Label Creator" link in the portal navigation menu, allowing all logged-in users to access the label generation tool.

## Usage

### Standalone Mode

The app includes a Flask-based standalone web interface that can be run independently:

```bash
cd apps/label_creator
python application.py
```

Then navigate to `http://localhost:5000` in your web browser.

### CSV File Format

The app accepts CSV files in two formats:

#### Format 1: Direct Product Data
```csv
product,sku,quantity,display_price
"Product Name 1",SKU-001,5,29.99
"Product Name 2",SKU-002,3,49.99
```

#### Format 2: Inventory Export
```csv
name,sku,retail_price,variant_option_one_value,variant_option_two_value,variant_option_three_value,inventory_location1,inventory_location2
"Product Name",SKU-001,29.99,"Red","Large","",5,3
```

### Using the Web Interface

1. **Upload CSV Files**:
   - Click "Choose CSV Files" or drag and drop CSV files
   - Multiple files can be uploaded at once
   - Files are validated for correct format

2. **Preview Products**:
   - Review the processed product list
   - Check quantities and pricing
   - Total label count is displayed

3. **Generate Labels**:
   - Select label type (sheet format)
   - Choose output format (PDF or Word)
   - Click "Generate Labels"
   - Download the generated file

### Label Types

The app comes pre-configured with several label formats:

| Label Type | Dimensions | Labels per Sheet | Page Size |
|-----------|-----------|------------------|-----------|
| S-16987 | 2.625" × 1.0" | 30 (3×10) | Letter |
| A4-24 | 2.75" × 1.375" | 24 (3×8) | A4 |
| LETTER-30 | 2.625" × 1.0" | 30 (3×10) | Letter |

### Customizing Label Formats

Label formats are defined in `templates/labels_types.json`. Each format includes:

```json
{
  "LABEL-ID": {
    "label_width": 2.625,
    "label_height": 1.0,
    "labels_per_row": 3,
    "labels_per_column": 10,
    "page_width_inch": 8.5,
    "page_height_inch": 11.0,
    "margin_top": 0.5,
    "margin_bottom": 0.5,
    "margin_left": 0.1875,
    "margin_right": 0.1875,
    "qrcode_x_offset": 0.0,
    "qrcode_y_offset": 0.0,
    "sku_x_offset": 0.0,
    "sku_y_offset": 0.0,
    "price_x_offset": 0.0,
    "price_y_offset": 0.0,
    "show_product_name": false,
    "file_name": "labels_custom"
  }
}
```

#### Configuration Parameters:

- **label_width/height**: Dimensions of each label in inches
- **labels_per_row/column**: Number of labels on the page
- **page_width/height_inch**: Paper size
- **margin_***: Page margins in inches
- ***_offset**: Fine-tune positioning of elements (in inches)
- **show_product_name**: Whether to display product name
- **file_name**: Output filename prefix

## Directory Structure

```
label_creator/
├── label_creator/          # Main module
│   ├── config/            # Configuration files
│   ├── public/            # Static assets (CSS, JS)
│   │   ├── css/
│   │   └── js/
│   └── templates/         # HTML templates
├── templates/             # Flask templates & config
│   ├── index.html
│   ├── preview.html
│   └── labels_types.json
├── static/               # Static files
│   └── css/
├── application.py        # Standalone Flask app
├── hooks.py             # ERPNext hooks
├── requirements.txt     # Python dependencies
├── setup.py            # Package setup
└── README.md           # This file
```

## Generated Files

The app creates several directories for generated content:

- `uploads/`: Temporary storage for uploaded CSV files
- `label_files/`: Generated PDF files
- `qr_codes/`: Generated QR code images (reused across sessions)
- `word_ready_files/`: Generated Word documents

Output files are named with the format: `YYYYMMDD_filename.pdf`

## Technical Details

### Dependencies

- **Flask**: Web framework
- **python-docx**: Word document generation
- **qrcode**: QR code generation
- **Pillow**: Image processing
- **reportlab**: PDF generation
- **frappe**: ERPNext framework

### Label Generation Process

1. CSV files are uploaded and validated
2. Product data is aggregated by SKU
3. QR codes are generated for each unique SKU
4. Labels are arranged on pages according to the selected format
5. PDF or Word document is created with properly positioned elements
6. File is downloaded to user's browser

### Security Features

- HTML entity decoding
- Special character sanitization
- JSON validation
- File type validation
- Safe file handling

## Customization

### Styling

Modify the CSS in `label_creator/public/css/style.css` to customize the web interface appearance.

### Label Templates

Edit `templates/labels_types.json` to add or modify label formats. The file is reloaded on each upload, so changes take effect immediately.

### Adding New Label Types

1. Open `templates/labels_types.json`
2. Add a new entry with your label specifications
3. Save the file
4. The new format will appear in the label type dropdown

## Troubleshooting

### Labels Not Aligning Properly

- Check margin and offset values in labels_types.json
- Verify label dimensions match your physical labels
- Test print on regular paper first

### QR Codes Too Large/Small

- Adjust the QR size calculation in `application.py`
- Modify the percentage in: `qr_size_pts = min(label_width_pts, label_height_pts * 0.4)`

### CSV Import Errors

- Ensure CSV files have the correct headers
- Check for special characters in product names
- Verify numeric fields (price, quantity) are properly formatted

### Missing Templates

If you get a "templates not found" error:
- Ensure the `templates/` directory exists
- Verify `labels_types.json` is in the templates folder
- Check file permissions

## ERPNext Integration

While this app can run standalone, it's designed to integrate with ERPNext. Future features may include:

- Direct integration with ERPNext Item master
- Automatic label generation on stock entry
- Batch printing from Stock Entry forms
- Custom print formats for labels

## License

MIT License - See `license.txt` for details

## Support

For issues, questions, or contributions:
- Create an issue on GitHub
- Contact: info@yourcompany.com

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## Version History

### v0.0.1 (Initial Release)
- Basic label generation functionality
- PDF and Word output support
- Multiple label format support
- QR code generation
- CSV import with dual format support
- Web-based interface

## Roadmap

- [ ] Direct ERPNext Item integration
- [ ] Batch printing from Stock Entry
- [ ] Custom field mapping
- [ ] Label templates designer UI
- [ ] Barcode format options (Code128, EAN13, etc.)
- [ ] Multi-language support
- [ ] Print directly to thermal printers
- [ ] API endpoints for programmatic access

## Credits

Developed for ERPNext ecosystem to simplify product labeling workflows.
