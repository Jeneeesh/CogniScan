from flask import Flask, request, jsonify, render_template, send_from_directory
import os
import requests
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename
import logging
from logging.handlers import RotatingFileHandler

# --- Configuration ---
app = Flask(__name__)

# Configure file upload settings
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max upload size
app.config['UPLOAD_TEMP_DIR'] = 'temp_uploads'
app.config['PROCESSED_FILES_DIR'] = 'processed_files_storage'
app.config['ALLOWED_EXTENSIONS'] = {
    'pdf': 'application/pdf',
    'jpg': 'image/jpeg',
    'jpeg': 'image/jpeg',
    'png': 'image/png',
    'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'xls': 'application/vnd.ms-excel',
    'json': 'application/json'
}

# Webhook configuration
n8n_webhook_url = "http://n8n:5678/webhook/flask-process"

# --- Logging Configuration ---
log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log_handler = RotatingFileHandler('app.log', maxBytes=10000000, backupCount=5)
log_handler.setFormatter(log_formatter)
log_handler.setLevel(logging.DEBUG)
app.logger.addHandler(log_handler)
app.logger.setLevel(logging.DEBUG)

# --- Ensure directories exist ---
os.makedirs(app.config['UPLOAD_TEMP_DIR'], exist_ok=True)
os.makedirs(app.config['PROCESSED_FILES_DIR'], exist_ok=True)

# --- In-memory transaction storage ---
transactions = []

# --- Helper Functions ---
def allowed_file(filename):
    """Check if the file has an allowed extension"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def validate_files(pdf_images, template_file):
    """Validate file types and content"""
    # Check PDF/Image files
    if not pdf_images or (len(pdf_images) == 1 and pdf_images[0].filename == ''):
        return False, "No PDF/Image files selected"
    
    for file in pdf_images:
        if not file or file.filename == '':
            return False, "Empty file detected in PDF/Images"
        if not allowed_file(file.filename):
            return False, f"Invalid file type: {file.filename}. Only PDF, JPG, PNG allowed."

    # Check Excel template
    if not template_file or template_file.filename == '':
        return False, "No Excel template selected"
    if not allowed_file(template_file.filename):
        return False, f"Invalid template file: {template_file.filename}. Only XLSX, XLS, or JSON allowed."

    return True, "Files validated successfully"

# --- Routes ---
@app.route('/')
def home():
    """Render the main upload page"""
    sorted_transactions = sorted(
        transactions,
        key=lambda x: datetime.strptime(x['uploaded_at'], '%Y-%m-%d %H:%M:%S'),
        reverse=True
    )
    return render_template('upload.html', transactions=sorted_transactions)

@app.route('/transactions', methods=['GET'])
def get_transactions():
    """API endpoint to retrieve current transactions"""
    # Sort by upload time (newest first)
    sorted_tx = sorted(
        transactions,
        key=lambda x: datetime.strptime(x['uploaded_at'], '%Y-%m-%d %H:%M:%S'),
        reverse=True
    )
    return jsonify(sorted_tx)

@app.route('/api/update_transaction_status', methods=['POST'])
def update_transaction_status():
    """Update transaction status from n8n workflow"""
    data = request.get_json()
    if not data:
        app.logger.error("No JSON data received in update_transaction_status")
        return jsonify({"error": "No data provided", "status": "error"}), 400

    transaction_id = data.get('transaction_id')
    status = data.get('status')
    processed_file_name = data.get('processed_file_name')
    document_type = data.get('document_type', 'Identifying')  # Default to 'Identifying'

    if not transaction_id or not status:
        app.logger.error(f"Missing transaction_id or status in update: {data}")
        return jsonify({"error": "Missing transaction_id or status", "status": "error"}), 400

    found = False
    for tx in transactions:
        if tx['id'] == transaction_id:
            tx['status'] = status
            tx['document_type'] = document_type  # Update document type
            if processed_file_name:
                tx['processed_file_name'] = processed_file_name
                tx['download_ready'] = True
            found = True
            app.logger.info(f"Updated transaction {transaction_id} to status: {status}, type: {document_type}")
            break
    
    if found:
        return jsonify({"message": "Transaction updated successfully", "document_type": document_type,"status": "success"}), 200
    else:
        app.logger.error(f"Transaction {transaction_id} not found for update")
        return jsonify({"error": "Transaction not found", "status": "error"}), 404

@app.route('/download/<transaction_id>', methods=['GET'])
def download_processed_file(transaction_id):
    """Serve processed files for download"""
    for tx in transactions:
        if tx['id'] == transaction_id and tx.get('download_ready'):
            processed_file_name = tx.get('processed_file_name')
            if processed_file_name:
                file_path = os.path.join(app.config['PROCESSED_FILES_DIR'], processed_file_name)
                if os.path.exists(file_path):
                    app.logger.info(f"Serving download for transaction {transaction_id}")
                    return send_from_directory(
                        app.config['PROCESSED_FILES_DIR'],
                        processed_file_name,
                        as_attachment=True
                    )
                else:
                    app.logger.error(f"File not found on disk: {processed_file_name}")
                    return jsonify({"error": "File not found on server", "status": "error"}), 404
            else:
                app.logger.error(f"No processed file name for transaction {transaction_id}")
                return jsonify({"error": "Processed file name not set", "status": "error"}), 400
    app.logger.error(f"Transaction {transaction_id} not found or file not ready")
    return jsonify({"error": "Transaction not found or file not ready", "status": "error"}), 404

@app.route('/upload', methods=['POST'])
def handle_upload():
    """Handle file uploads and send to n8n for processing"""
    app.logger.info("\n--- New Upload Request ---")
    app.logger.debug(f"Headers: {dict(request.headers)}")
    app.logger.debug(f"Form Data: {request.form}")
    app.logger.debug(f"Files Received: {request.files}")

    try:
        # --- File Validation ---
        if 'files' not in request.files or 'template' not in request.files:
            app.logger.error("Missing 'files' or 'template' in request.files")
            return jsonify({
                "status": "error",
                "message": "Missing required file inputs. Please select PDF/Image and Excel template files."
            }), 400

        pdf_images = request.files.getlist('files')
        template_file = request.files['template']

        # Validate file types and content
        is_valid, validation_msg = validate_files(pdf_images, template_file)
        if not is_valid:
            app.logger.error(f"File validation failed: {validation_msg}")
            return jsonify({"status": "error", "message": validation_msg}), 400

        # --- Transaction Setup ---
        transaction_id = str(uuid.uuid4())
        uploaded_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        transactions.append({
            'id': transaction_id,
            'uploaded_at': uploaded_datetime,
            'document_type': 'Identifying',  # Default value
            'status': 'Processing',
            'download_ready': False,
            'processed_file_name': None
        })
        app.logger.info(f"Created new transaction: {transaction_id}")

        # --- File Processing ---
        files_to_send = []
        temp_files = []  # To track files for cleanup
        
        try:
            # Process PDF/Image files
            for file in pdf_images:
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_TEMP_DIR'], filename)
                file.save(file_path)
                temp_files.append(file_path)
                files_to_send.append(('files', (filename, open(file_path, 'rb'), file.mimetype)))

            # Process Excel template
            template_filename = secure_filename(template_file.filename)
            template_path = os.path.join(app.config['UPLOAD_TEMP_DIR'], template_filename)
            template_file.save(template_path)
            temp_files.append(template_path)
            files_to_send.append(('template', (template_filename, open(template_path, 'rb'), template_file.mimetype)))

            # Prepare form data
            form_data = {
                'transaction_id': transaction_id,
                'uploaded_at': uploaded_datetime
            }

            # --- Send to n8n ---
            app.logger.info(f"Sending {len(pdf_images)} files and template to n8n")
            response = requests.post(
                n8n_webhook_url,
                data=form_data,
                files=files_to_send,
                timeout=30  # 30 seconds timeout
            )
            response.raise_for_status()

            # --- Cleanup ---
            for file_handle in [f[1][1] for f in files_to_send]:  # Get all file handles
                file_handle.close()
            
            for temp_file in temp_files:
                if os.path.exists(temp_file):
                    os.remove(temp_file)

            # --- Response Handling ---
            n8n_response = response.json()
            app.logger.debug(f"n8n response: {n8n_response}")

            return jsonify({
                "status": "success",
                "message": "Files uploaded and processing initiated!",
                "transaction_id": transaction_id,
                "n8n_response": n8n_response
            }), 200

        except Exception as processing_error:
            # Cleanup if something went wrong during processing
            app.logger.error(f"Error during file processing: {str(processing_error)}")
            for temp_file in temp_files:
                if os.path.exists(temp_file):
                    try:
                        os.remove(temp_file)
                    except Exception as cleanup_error:
                        app.logger.error(f"Error cleaning up temp file {temp_file}: {str(cleanup_error)}")
            raise processing_error

    except requests.exceptions.RequestException as req_err:
        error_msg = f"Error communicating with n8n: {str(req_err)}"
        app.logger.error(error_msg)
        return jsonify({
            "status": "error",
            "message": "Failed to communicate with processing service. Please try again later."
        }), 500

    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        app.logger.error(error_msg, exc_info=True)
        return jsonify({
            "status": "error",
            "message": "An unexpected error occurred during file upload."
        }), 500

@app.route('/test-webhook')
def test_webhook():
    """Test connectivity to n8n webhook"""
    try:
        response = requests.post(
            n8n_webhook_url,
            json={"test_connection": True},
            timeout=10
        )
        response.raise_for_status()
        return jsonify({
            "status": "success",
            "message": "Test webhook connection successful!",
            "n8n_response": response.json()
        }), 200
    except requests.exceptions.ConnectionError as ce:
        app.logger.error(f"Connection error testing webhook: {str(ce)}")
        return jsonify({
            "status": "error",
            "message": f"Could not connect to n8n at {n8n_webhook_url}. Ensure n8n is running."
        }), 500
    except Exception as e:
        app.logger.error(f"Error testing webhook: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"Error testing webhook: {str(e)}"
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)