"""
Voice-Enabled Form Filling Workflow
Sequential conversation flow with proper data formatting
Easy document switching - just change the input path
"""

import os
import json
import time
from dotenv import load_dotenv
from practice import extract_and_generate_schema
from image_generator import FormImageGenerator
from enhanced_coordinate_extractor import CoordinateExtractor
from voice_form_filler import VoiceFormFiller

# Load environment variables
load_dotenv("../.env")

def convert_pdf_to_image(pdf_path: str) -> str:
    """
    Convert PDF to image for processing
    Returns the path to the converted image
    """
    try:
        import fitz  # PyMuPDF
        import PIL.Image
        
        # Open PDF
        pdf_document = fitz.open(pdf_path)
        page = pdf_document[0]  # Get first page
        
        # Convert to image
        mat = fitz.Matrix(2.0, 2.0)  # 2x zoom for better quality
        pix = page.get_pixmap(matrix=mat)
        img_data = pix.tobytes("png")
        
        # Save as PNG
        image_path = pdf_path.replace('.pdf', '_converted.png')
        with open(image_path, 'wb') as f:
            f.write(img_data)
        
        pdf_document.close()
        print(f"✅ Converted PDF to image: {image_path}")
        return image_path
        
    except ImportError:
        print("❌ PyMuPDF not installed. Install with: pip install PyMuPDF")
        return None
    except Exception as e:
        print(f"❌ Error converting PDF: {e}")
        return None

def voice_form_workflow(input_document_path: str, use_voice: bool = True):
    """
    Voice-enabled form filling workflow
    
    Args:
        input_document_path (str): Path to the input form document (PDF, PNG, JPG, etc.)
        use_voice (bool): Whether to use voice interaction (True) or text input (False)
    """
    
    print("🚀 Starting Voice-Enabled Form Workflow...")
    print(f"📸 Processing document: {input_document_path}")
    print(f"�� Voice interaction: {'Enabled' if use_voice else 'Disabled'}")
    
    # Handle PDF files by converting to image
    processing_path = input_document_path
    if input_document_path.lower().endswith('.pdf'):
        print("\n📄 PDF detected, converting to image...")
        converted_image = convert_pdf_to_image(input_document_path)
        if converted_image:
            processing_path = converted_image
        else:
            print("❌ Could not convert PDF to image")
            return None
    
    # Step 1: Extract and generate schema using Azure + OpenAI
    print("\n📋 Step 1: Extracting form structure with Azure + OpenAI...")
    schema = extract_and_generate_schema(processing_path)
    
    if not schema:
        print("❌ Could not extract schema. Please check the previous output for errors.")
        return None
    
    print("✅ Schema extracted successfully!")
    
    # Step 2: Check for existing manual coordinates or extract new ones
    print("\n📐 Step 2: Checking for field coordinates...")
    
    # Generate coordinate filename based on document name
    doc_name = os.path.splitext(os.path.basename(input_document_path))[0]
    coords_file = f"field_coordinates_{doc_name}.json"
    
    if os.path.exists(coords_file):
        try:
            with open(coords_file, 'r') as f:
                field_coordinates = json.load(f)
            print(f"✅ Found existing manual coordinates: {len(field_coordinates)} fields")
            print("📝 Using your manually adjusted coordinates (skipping automatic detection)")
        except Exception as e:
            print(f"⚠️  Error reading manual coordinates: {e}")
            field_coordinates = {}
    else:
        # Extract coordinates automatically
        print("🔍 No manual coordinates found, extracting automatically...")
        
        # Get Azure credentials
        endpoint = 'https://aiformfilling-doc-ai.cognitiveservices.azure.com/'
        key = os.getenv('AZURE_KEY')
        
        if not key:
            print("❌ AZURE_KEY not found in environment variables")
            field_coordinates = {}
        else:
            try:
                extractor = CoordinateExtractor(endpoint, key)
                field_coordinates = extractor.get_coordinate_mapping(processing_path)
                
                if field_coordinates:
                    print(f"✅ Extracted coordinates for {len(field_coordinates)} fields")
                else:
                    print("⚠️  Could not extract coordinates automatically")
                    field_coordinates = {}
            except Exception as e:
                print(f"❌ Error extracting coordinates: {e}")
                field_coordinates = {}
    
    # Step 3: Fill out the form
    if use_voice:
        print("\n🎤 Step 3: Voice-enabled form filling...")
        print("Starting voice form filler...")
        
        # Create voice form filler
        voice_filler = VoiceFormFiller(schema)
        
        # Fill form with voice (sequential conversation)
        voice_filler.fill_form_with_voice()
        
        # Get filled schema
        filled_schema = voice_filler.get_filled_schema()
        print("✅ Voice form filling completed!")
    else:
        print("\n✍️  Step 3: Text-based form filling...")
        filled_schema = fill_form_text_input(schema)
    
    # Step 4: Generate the filled form image
    print("\n🖼️  Step 4: Generating filled form image...")
    
    try:
        # Use the original document path for image generation
        generator = FormImageGenerator(input_document_path)
        
        if field_coordinates:
            # Use precise coordinates
            filled_image_path = generator.generate_filled_image_with_coordinate_file(
                filled_schema, 
                coords_file if os.path.exists(coords_file) else None
            )
        else:
            # Use automatic positioning
            filled_image_path = generator.generate_filled_image(filled_schema)
        
        if filled_image_path:
            print(f"✅ Filled form image created: {filled_image_path}")
        else:
            print("❌ Failed to generate filled form image")
            return None
            
    except Exception as e:
        print(f"❌ Error generating filled form image: {e}")
        return None
    
    # Step 5: Save completed schema
    schema_path = f"completed_{doc_name}_voice_schema.json"
    try:
        with open(schema_path, 'w') as f:
            json.dump(filled_schema, f, indent=2)
        print(f"✅ Completed schema saved: {schema_path}")
    except Exception as e:
        print(f"⚠️  Error saving schema: {e}")
        schema_path = None
    
    # Return results
    result = {
        'filled_image_path': filled_image_path,
        'schema_path': schema_path,
        'schema': filled_schema,
        'field_coordinates': field_coordinates,
        'voice_enabled': use_voice
    }
    
    return result

def fill_form_text_input(schema):
    """Fill form using text input (fallback method)"""
    print("Using text input for form filling...")
    
    # Extract required fields - handle different schema structures
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
        print(f"⚠️  No fields marked as required, treating all {len(fields)} fields as required")
    
    print(f"Found {len(required_fields)} fields to fill.")
    
    # Fill each required field
    for i, field in enumerate(required_fields, 1):
        print(f"\n--- Field {i}/{len(required_fields)} ---")
        print(f"Label: {field.get('label', 'N/A')}")
        print(f"Type: {field.get('type', 'N/A')}")
        
        if field.get('options'):
            print(f"Options: {[opt.get('label', str(opt)) for opt in field.get('options', [])]}")
        
        # Get user input
        user_input = input(f"Enter value for '{field.get('label', '')}': ")
        field['value'] = user_input
    
    print("\n✅ All required fields filled!")
    return schema

def list_available_documents():
    """List available documents in the sample_data directory"""
    sample_data_dir = "../sample_data"
    if not os.path.exists(sample_data_dir):
        print(f"❌ Sample data directory not found: {sample_data_dir}")
        return []
    
    # Supported document formats
    supported_formats = ['.pdf', '.png', '.jpg', '.jpeg', '.tiff', '.bmp']
    
    documents = []
    for file in os.listdir(sample_data_dir):
        file_path = os.path.join(sample_data_dir, file)
        if os.path.isfile(file_path):
            _, ext = os.path.splitext(file.lower())
            if ext in supported_formats:
                documents.append((file, file_path))
    
    return documents

def main():
    """Main function to run the voice-enabled workflow"""
    print("🎯 Voice-Enabled Form Filling Workflow")
    print("=" * 50)
    
    # List available documents
    documents = list_available_documents()
    
    if not documents:
        print("❌ No supported documents found in sample_data directory")
        print("Supported formats: PDF, PNG, JPG, JPEG, TIFF, BMP")
        return
    
    print("\n📁 Available documents:")
    for i, (filename, filepath) in enumerate(documents, 1):
        print(f"  {i}. {filename}")
    
    # Let user choose document
    while True:
        try:
            choice = input(f"\nSelect document (1-{len(documents)}): ").strip()
            doc_index = int(choice) - 1
            if 0 <= doc_index < len(documents):
                selected_doc = documents[doc_index]
                break
            else:
                print(f"Please enter a number between 1 and {len(documents)}")
        except ValueError:
            print("Please enter a valid number")
    
    input_document = selected_doc[1]
    print(f"\n✅ Selected: {selected_doc[0]}")
    
    # Ask user if they want voice interaction
    print("\nChoose interaction method:")
    print("1. Voice interaction (sequential conversation)")
    print("2. Text input (type your answers)")
    
    while True:
        choice = input("Enter your choice (1 or 2): ").strip()
        if choice in ['1', '2']:
            use_voice = choice == "1"
            break
        else:
            print("Please enter 1 or 2")
    
    # Run the workflow
    result = voice_form_workflow(input_document, use_voice)
    
    if result:
        print("\n🎉 Voice-enabled workflow completed successfully!")
        print(f"📄 Filled form image: {result['filled_image_path']}")
        print(f"📋 Completed schema: {result['schema_path']}")
        print(f"🎤 Voice enabled: {result['voice_enabled']}")
        
        # Show a summary of what was filled
        print("\n📝 Summary of filled fields:")
        schema = result['schema']
        
        # Extract fields from different schema structures
        fields = []
        if 'fields' in schema:
            fields = schema['fields']
        elif 'form' in schema and 'fields' in schema['form']:
            fields = schema['form']['fields']
        elif 'sections' in schema:
            for section in schema['sections']:
                fields.extend(section.get('fields', []))
        
        for field in fields:
            if field.get('value'):
                print(f"  • {field.get('label', 'Unknown')}: {field['value']}")
        
        if result.get('field_coordinates'):
            print(f"📍 Field coordinates: {len(result['field_coordinates'])} fields positioned")
    else:
        print("\n❌ Workflow failed. Please check the error messages above.")

if __name__ == "__main__":
    main()
