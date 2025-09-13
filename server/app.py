"""
Flask Web Application for Voice-Enabled Form Filling
"""

import os
import json
import time
import threading
import shutil
from flask import Flask, render_template, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
from voice_workflow import voice_form_workflow, list_available_documents
from voice_form_filler import VoiceFormFiller
from image_generator import FormImageGenerator

# Load environment variables
load_dotenv("../.env")

app = Flask(__name__)
CORS(app)

# Configure upload settings
UPLOAD_FOLDER = '../sample_data'
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'tiff', 'bmp'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Global variables for session management
current_session = {
    'status': 'idle',  # idle, processing, ready, filling, completed
    'document': None,
    'schema': None,
    'filled_schema': None,
    'voice_filler': None,
    'current_field': 0,
    'total_fields': 0,
    'filled_fields': {},
    'error': None,
    'filled_image_path': None
}

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/test')
def test():
    """Test page"""
    return render_template('test.html')

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Handle file upload"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'})
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'})
        
        if file and allowed_file(file.filename):
            # Save file to sample_data folder
            filename = file.filename
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            return jsonify({
                'success': True, 
                'message': 'File uploaded successfully',
                'filename': filename,
                'filepath': filepath
            })
        else:
            return jsonify({'success': False, 'error': 'File type not allowed'})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/documents')
def get_documents():
    """Get list of available documents"""
    try:
        documents = list_available_documents()
        return jsonify({
            'success': True,
            'documents': [{'name': doc[0], 'path': doc[1]} for doc in documents]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/process', methods=['POST'])
def process_document():
    """Process a document and extract schema"""
    try:
        data = request.json
        document_path = data.get('document_path')
        use_voice = data.get('use_voice', True)
        
        if not document_path:
            return jsonify({'success': False, 'error': 'No document path provided'})
        
        # Reset session
        current_session.update({
            'status': 'processing',
            'document': document_path,
            'schema': None,
            'filled_schema': None,
            'voice_filler': None,
            'current_field': 0,
            'total_fields': 0,
            'filled_fields': {},
            'error': None,
            'filled_image_path': None
        })
        
        # Process document in background
        def process_in_background():
            try:
                # Only extract schema, don't fill the form yet
                from practice import extract_and_generate_schema
                schema = extract_and_generate_schema(document_path)
                
                if schema:
                    current_session['schema'] = schema
                    current_session['status'] = 'ready'
                    
                    # Extract fields for counting
                    fields = []
                    if 'fields' in schema:
                        fields = schema['fields']
                    elif 'form' in schema and 'fields' in schema['form']:
                        fields = schema['form']['fields']
                    elif 'sections' in schema:
                        for section in schema['sections']:
                            fields.extend(section.get('fields', []))
                    
                    required_fields = [field for field in fields if field.get('required', False)]
                    if not required_fields:
                        required_fields = fields
                    
                    current_session['total_fields'] = len(required_fields)
                    current_session['voice_filler'] = VoiceFormFiller(schema)
                else:
                    current_session['status'] = 'error'
                    current_session['error'] = 'Failed to extract schema from document'
            except Exception as e:
                current_session['status'] = 'error'
                current_session['error'] = str(e)
        
        # Start background processing
        thread = threading.Thread(target=process_in_background)
        thread.daemon = True
        thread.start()
        
        return jsonify({'success': True, 'message': 'Processing started'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/status')
def get_status():
    """Get current processing status"""
    return jsonify({
        'success': True,
        'status': current_session['status'],
        'current_field': current_session['current_field'],
        'total_fields': current_session['total_fields'],
        'filled_fields': current_session['filled_fields'],
        'error': current_session['error']
    })

@app.route('/api/fields')
def get_fields():
    """Get form fields"""
    if current_session['status'] != 'ready':
        return jsonify({'success': False, 'error': 'Document not ready'})
    
    try:
        schema = current_session['schema']
        fields = []
        
        if 'fields' in schema:
            fields = schema['fields']
        elif 'form' in schema and 'fields' in schema['form']:
            fields = schema['form']['fields']
        elif 'sections' in schema:
            for section in schema['sections']:
                fields.extend(section.get('fields', []))
        
        required_fields = [field for field in fields if field.get('required', False)]
        if not required_fields:
            required_fields = fields
        
        return jsonify({
            'success': True,
            'fields': required_fields
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/fill-field', methods=['POST'])
def fill_field():
    """Fill a specific field"""
    try:
        data = request.json
        field_label = data.get('field_label')
        value = data.get('value')
        
        if not field_label or not value:
            return jsonify({'success': False, 'error': 'Field label and value required'})
        
        # Store the filled value
        current_session['filled_fields'][field_label] = value
        
        # Update the schema
        if current_session['voice_filler']:
            current_session['voice_filler'].filled_fields[field_label] = value
        
        return jsonify({'success': True, 'message': 'Field filled successfully'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/complete')
def complete_form():
    """Complete the form and generate final result"""
    try:
        if current_session['status'] != 'ready':
            return jsonify({'success': False, 'error': 'Form not ready'})
        
        # Get filled schema
        if current_session['voice_filler']:
            filled_schema = current_session['voice_filler'].get_filled_schema()
        else:
            filled_schema = current_session['schema']
        
        current_session['filled_schema'] = filled_schema
        
        # Generate filled form image
        try:
            generator = FormImageGenerator(current_session['document'])
            filled_image_path = generator.generate_filled_image(filled_schema)
            current_session['filled_image_path'] = filled_image_path
        except Exception as e:
            print(f"Error generating filled image: {e}")
            current_session['filled_image_path'] = None
        
        current_session['status'] = 'completed'
        
        return jsonify({
            'success': True,
            'message': 'Form completed successfully',
            'filled_schema': filled_schema,
            'filled_image_path': current_session['filled_image_path']
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/filled-image')
def get_filled_image():
    """Get the filled form image"""
    if current_session['filled_image_path'] and os.path.exists(current_session['filled_image_path']):
        return send_file(current_session['filled_image_path'], mimetype='image/jpeg')
    else:
        return jsonify({'success': False, 'error': 'No filled image available'})

@app.route('/api/reset')
def reset_session():
    """Reset the current session"""
    current_session.update({
        'status': 'idle',
        'document': None,
        'schema': None,
        'filled_schema': None,
        'voice_filler': None,
        'current_field': 0,
        'total_fields': 0,
        'filled_fields': {},
        'error': None,
        'filled_image_path': None
    })
    return jsonify({'success': True, 'message': 'Session reset'})

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    
    print("🚀 Starting Voice-Enabled Form Filling Web Application")
    print("📱 Main page: http://localhost:8080")
    print("🧪 Test page: http://localhost:8080/test")
    print("🛑 Press Ctrl+C to stop the server")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=8080)
