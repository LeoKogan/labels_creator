frappe.pages['label-creator'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Label Creator',
		single_column: true
	});

	page.main.html(`
		<div class="label-creator-container" style="padding: 20px;">
			<div class="row">
				<div class="col-md-12">
					<p class="text-muted">Upload CSV files to generate product labels with QR codes</p>
				</div>
			</div>

			<div class="row mt-4">
				<div class="col-md-12">
					<div class="card">
						<div class="card-body">
							<h5 class="card-title">Upload CSV Files</h5>

							<div class="upload-area p-4 text-center border rounded" style="border-style: dashed !important; background-color: #f8f9fa; cursor: pointer;">
								<input type="file" id="fileInput" multiple accept=".csv" style="display: none;">
								<label for="fileInput" style="cursor: pointer; margin: 0; width: 100%;">
									<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" fill="currentColor" class="bi bi-cloud-upload mb-3" viewBox="0 0 16 16">
										<path fill-rule="evenodd" d="M4.406 1.342A5.53 5.53 0 0 1 8 0c2.69 0 4.923 2 5.166 4.579C14.758 4.804 16 6.137 16 7.773 16 9.569 14.502 11 12.687 11H10a.5.5 0 0 1 0-1h2.688C13.979 10 15 8.988 15 7.773c0-1.216-1.02-2.228-2.313-2.228h-.5v-.5C12.188 2.825 10.328 1 8 1a4.53 4.53 0 0 0-2.941 1.1c-.757.652-1.153 1.438-1.153 2.055v.448l-.445.049C2.064 4.805 1 5.952 1 7.318 1 8.785 2.23 10 3.781 10H6a.5.5 0 0 1 0 1H3.781C1.708 11 0 9.366 0 7.318c0-1.763 1.266-3.223 2.942-3.593.143-.863.698-1.723 1.464-2.383z"/>
										<path fill-rule="evenodd" d="M7.646 4.146a.5.5 0 0 1 .708 0l3 3a.5.5 0 0 1-.708.708L8.5 5.707V14.5a.5.5 0 0 1-1 0V5.707L5.354 7.854a.5.5 0 1 1-.708-.708l3-3z"/>
									</svg>
									<h5>Choose CSV Files</h5>
									<p class="text-muted">or drag and drop here</p>
								</label>
							</div>

							<div id="fileList" class="mt-3"></div>

							<button id="uploadBtn" class="btn btn-primary mt-3" style="display: none;">
								Process Files
							</button>
						</div>
					</div>
				</div>
			</div>

			<!-- Preview Section -->
			<div id="previewSection" class="row mt-4" style="display: none;">
				<div class="col-md-12">
					<div class="card">
						<div class="card-body">
							<h5 class="card-title">Label Preview</h5>
							<p>Total Labels: <strong id="totalLabels">0</strong></p>

							<div class="row mb-3">
								<div class="col-md-6">
									<label for="labelType" class="form-label">Label Type</label>
									<select id="labelType" class="form-control">
										<option value="">Loading...</option>
									</select>
								</div>
							</div>

							<div class="table-responsive">
								<table class="table table-striped" id="previewTable">
									<thead>
										<tr>
											<th style="width: 50px;">
												<input type="checkbox" id="selectAll" checked>
											</th>
											<th>SKU</th>
											<th>Product</th>
											<th style="width: 150px;">Price</th>
											<th style="width: 120px;">Quantity</th>
										</tr>
									</thead>
									<tbody id="previewTableBody">
									</tbody>
								</table>
							</div>

							<button id="generateBtn" class="btn btn-success">
								Generate Labels (PDF)
							</button>
							<button id="startOverBtn" class="btn btn-secondary">
								Start Over
							</button>
						</div>
					</div>
				</div>
			</div>

			<!-- Success Section -->
			<div id="successSection" class="row mt-4" style="display: none;">
				<div class="col-md-12">
					<div class="alert alert-success" role="alert">
						<h4 class="alert-heading">✅ Labels Generated Successfully!</h4>
						<p>Your PDF file is ready for download.</p>
						<hr>
						<div class="d-flex gap-2">
							<a id="downloadLink" href="#" class="btn btn-success" download>
								<i class="fa fa-download"></i> Download PDF
							</a>
							<button id="generateAnotherBtn" class="btn btn-primary">
								Generate Another
							</button>
						</div>
					</div>
				</div>
			</div>

			<!-- Loading Spinner -->
			<div id="loadingSpinner" class="row mt-4" style="display: none;">
				<div class="col-md-12 text-center">
					<div class="spinner-border text-primary" role="status">
						<span class="sr-only">Loading...</span>
					</div>
					<p class="mt-2">Processing...</p>
				</div>
			</div>
		</div>

		<style>
		.upload-area {
			transition: background-color 0.3s;
		}
		.upload-area:hover {
			background-color: #e9ecef !important;
		}
		.card {
			box-shadow: 0 1px 3px rgba(0,0,0,0.12);
			border: 1px solid #e8e9ea;
		}
		/* Editable input styling */
		.price-input, .quantity-input {
			background-color: white !important;
			border: 1px solid black !important;
			border-radius: 3px;
			padding: 4px 8px;
		}
		/* Make $ symbol blend with the row */
		.input-group-text {
			background-color: transparent !important;
			border: none !important;
			padding-left: 0;
			padding-right: 4px;
			color: inherit;
		}
		.input-group {
			border: none !important;
			background: transparent !important;
		}
		/* Remove Bootstrap's input-group borders */
		.input-group > .form-control {
			border-radius: 3px !important;
		}
		/* SKU column word wrapping - break on hyphens and word boundaries */
		#previewTable tbody td:nth-child(2) {
			overflow-wrap: anywhere;
			word-break: normal;
			white-space: normal;
			max-width: 200px;
			min-width: 80px;
		}
		</style>
	`);

	// Initialize the page
	let processedContent = [];

	// Load label types
	loadLabelTypes();

	function loadLabelTypes() {
		frappe.call({
			method: 'label_creator.api.labels.get_label_types',
			callback: function(r) {
				if (r.message && r.message.success) {
					const labelTypes = r.message.label_types;
					const select = page.main.find('#labelType');
					select.empty();

					Object.entries(labelTypes).forEach(([key, value]) => {
						const displayName = value.name || `${key} (${value.labels_per_row}x${value.labels_per_column})`;
						select.append(`<option value="${key}">${displayName}</option>`);
					});
				}
			}
		});
	}

	// File input handling
	page.main.find('#fileInput').on('change', function() {
		const files = this.files;
		const fileList = page.main.find('#fileList');
		const uploadBtn = page.main.find('#uploadBtn');

		if (files.length > 0) {
			fileList.html('<ul class="list-group"></ul>');
			const ul = fileList.find('ul');

			Array.from(files).forEach(file => {
				ul.append(`<li class="list-group-item">${file.name}</li>`);
			});

			uploadBtn.show();
		} else {
			fileList.html('');
			uploadBtn.hide();
		}
	});

	// Upload and process
	page.main.find('#uploadBtn').on('click', async function() {
		const files = page.main.find('#fileInput')[0].files;
		if (files.length === 0) return;

		page.main.find('#loadingSpinner').show();

		try {
			const filesData = [];

			for (let file of files) {
				const content = await file.text();
				filesData.push({
					filename: file.name,
					content: content
				});
			}

			frappe.call({
				method: 'label_creator.api.labels.upload_and_process',
				args: {
					files_json: JSON.stringify(filesData)
				},
				callback: function(r) {
					page.main.find('#loadingSpinner').hide();

					if (r.message && r.message.success) {
						processedContent = r.message.processed_content;
						displayPreview(processedContent, r.message.total_labels);
					} else {
						frappe.msgprint('Error processing files: ' + (r.message?.message || 'Unknown error'));
					}
				}
			});
		} catch (error) {
			console.error('Upload error:', error);
			frappe.msgprint('Error uploading files');
			page.main.find('#loadingSpinner').hide();
		}
	});

	function displayPreview(content, totalLabels) {
		page.main.find('#totalLabels').text(totalLabels);

		const tbody = page.main.find('#previewTableBody');
		tbody.empty();

		content.forEach((item, index) => {
			const row = $(`
				<tr data-index="${index}">
					<td>
						<input type="checkbox" class="item-checkbox" data-index="${index}" checked>
					</td>
					<td>${item.sku}</td>
					<td>${item.product}</td>
					<td>
						<div class="input-group input-group-sm">
							<span class="input-group-text">$</span>
							<input type="number" class="form-control price-input" data-index="${index}"
								value="${parseFloat(item.display_price).toFixed(2)}"
								step="0.01" min="0" style="max-width: 100px;">
						</div>
					</td>
					<td>
						<input type="number" class="form-control form-control-sm quantity-input" data-index="${index}"
							value="${item.quantity}" min="1" style="max-width: 80px;">
					</td>
				</tr>
			`);
			tbody.append(row);
		});

		// Update total when checkboxes or quantities change
		updateTotalLabels();

		// Add event listeners
		page.main.find('.item-checkbox').on('change', updateTotalLabels);
		page.main.find('.quantity-input').on('input', updateTotalLabels);

		// Select/deselect all checkbox
		const selectAllCheckbox = page.main.find('#selectAll');
		selectAllCheckbox.prop('checked', true);
		selectAllCheckbox.on('change', function() {
			page.main.find('.item-checkbox').prop('checked', this.checked);
			updateTotalLabels();
		});

		page.main.find('#previewSection').show();
		page.main.find('#previewSection')[0].scrollIntoView({ behavior: 'smooth' });
	}

	function updateTotalLabels() {
		let total = 0;
		page.main.find('.item-checkbox:checked').each(function() {
			const index = $(this).data('index');
			const quantityInput = page.main.find(`.quantity-input[data-index="${index}"]`);
			total += parseInt(quantityInput.val()) || 0;
		});
		page.main.find('#totalLabels').text(total);
	}

	// Generate labels
	page.main.find('#generateBtn').on('click', function() {
		const labelType = page.main.find('#labelType').val();

		if (!labelType) {
			frappe.msgprint('Please select a label type');
			return;
		}

		// Get selected items with updated prices and quantities
		const selectedItems = [];
		page.main.find('.item-checkbox:checked').each(function() {
			const index = $(this).data('index');
			const priceInput = page.main.find(`.price-input[data-index="${index}"]`);
			const quantityInput = page.main.find(`.quantity-input[data-index="${index}"]`);

			const item = {
				...processedContent[index],
				display_price: parseFloat(priceInput.val()).toFixed(2),
				quantity: parseInt(quantityInput.val()) || 0
			};

			if (item.quantity > 0) {
				selectedItems.push(item);
			}
		});

		if (selectedItems.length === 0) {
			frappe.msgprint('Please select at least one item to print');
			return;
		}

		page.main.find('#loadingSpinner').show();

		frappe.call({
			method: 'label_creator.api.labels.generate_labels',
			args: {
				label_type: labelType,
				processed_content_json: JSON.stringify(selectedItems)
			},
			callback: function(r) {
				page.main.find('#loadingSpinner').hide();

				if (r.message && r.message.success) {
					const downloadLink = page.main.find('#downloadLink');
					downloadLink.attr('href', r.message.file_url);
					downloadLink.attr('download', r.message.filename || 'labels.pdf');

					page.main.find('#successSection').show();
					page.main.find('#previewSection').hide();

					page.main.find('#successSection')[0].scrollIntoView({ behavior: 'smooth' });
				} else {
					frappe.msgprint('Error generating labels: ' + (r.message?.message || 'Unknown error'));
				}
			}
		});
	});

	// Start over
	page.main.find('#startOverBtn').on('click', function() {
		location.reload();
	});

	// Generate another
	page.main.find('#generateAnotherBtn').on('click', function() {
		page.main.find('#successSection').hide();
		page.main.find('#previewSection').show();
		page.main.find('#previewSection')[0].scrollIntoView({ behavior: 'smooth' });
	});
};
