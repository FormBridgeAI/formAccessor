"""
Complete Voice-Enabled Form Filling Workflow with TTS
Combines Azure Document Intelligence, OpenAI, Deepgram Speech-to-Text, and Text-to-Speech
"""

import os
import json
import time
from dotenv import load_dotenv
from practice import extract_and_generate_schema
from image_generator import FormImageGenerator
from enhanced_coordinate_extractor import CoordinateExtractor
from voice_form_filler_with_tts import VoiceFormFillerWithTTS

# Load environment variables
load_dotenv("../.env")

def complete_voice_form_workflow(input_image_path: str, use_voice: bool = True):
    """
    Complete voice-enabled form filling workflow with TTS
    
    Args:
        input_image_path (str): Path to the input form image
        use_voice (bool): Whether to use voice interaction (True) or text input (False)
    """
    
    print("🚀 Starting Complete Voice-Enabled Form Workflow...")
    print(f"📸 Processing image: {input_image_path}")
    print(f"🎤 Voice interaction: {'Enabled' if use_voice else 'Disabled'}")
    
    # Step 1: Extract and generate schema using Azure + OpenAI
    print("\n📋 Step 1: Extracting form structure with Azure + OpenAI...")
    schema = extract_and_generate_schema(input_image_path)
    
    if not schema:
        print("❌ Could not extract schema. Please check the previous output for errors.")
        return None
    
    print("✅ Schema extracted successfully!")
    
    # Step 2: Check for existing manual coordinates or extract new ones
    print("\n📐 Step 2: Checking for field coordinates...")
    
    coords_file = "field_coordinates.json"
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
        extractor = CoordinateExtractor()
        field_coordinates = extractor.get_coordinate_mapping(input_image_path)
        
        if field_coordinates:
            print(f"✅ Extracted coordinates for {len(field_coordinates)} fields")
        else:
            print("⚠️  Could not extract coordinates automatically")
            field_coordinates = {}
    
    # Step 3: Fill out the form
    if use_voice:
        print("\n🎤 Step 3: Voice-enabled form filling with TTS...")
        print("Starting voice form filler with text-to-speech...")
        
        # Create voice form filler with TTS
        voice_filler = VoiceFormFillerWithTTS(schema)
        
        # Fill form with voice and TTS
        voice_filler.fill_form_with_voice_and_tts()
        
        # Get filled schema
        filled_schema = voice_filler.get_filled_schema()
        print("✅ Voice form filling completed!")
    else:
        print("\n✍️  Step 3: Text-based form filling...")
        filled_schema = fill_form_text_input(schema)
    
    # Step 4: Generate the filled form image
    print("\n🖼️  Step 4: Generating filled form image...")
    
    try:
        generator = FormImageGenerator(input_image_path)
        
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
    schema_path = "completed_voice_schema.json"
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
    
    # Extract required fields
    fields = schema.get('fields', [])
    if not fields and 'sections' in schema:
        for section in schema['sections']:
            fields.extend(section.get('fields', []))
    
    required_fields = [field for field in fields if field.get('required', False)]
    print(f"Found {len(required_fields)} required fields to fill.")
    
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

def main():
    """Main function to run the complete voice-enabled workflow"""
    # Use the form in sample_data folder
    input_image = "../sample_data/simple-job-application-form-27d287c8e2b97cd3f175c12ef67426b2-classic.png"
    
    # Check if the image exists
    if not os.path.exists(input_image):
        print(f"❌ Image not found at: {input_image}")
        print("Please place your form image in the sample_data directory or update the path.")
        return
    
    # Ask user if they want voice interaction
    print("Choose interaction method:")
    print("1. Voice interaction with TTS (AI speaks questions, you speak answers)")
    print("2. Text input (type your answers)")
    
    choice = input("Enter your choice (1 or 2): ").strip()
    use_voice = choice == "1"
    
    # Run the workflow
    result = complete_voice_form_workflow(input_image, use_voice)
    
    if result:
        print("\n🎉 Complete voice-enabled workflow completed successfully!")
        print(f"📄 Filled form image: {result['filled_image_path']}")
        print(f"📋 Completed schema: {result['schema_path']}")
        print(f"🎤 Voice enabled: {result['voice_enabled']}")
        
        # Show a summary of what was filled
        print("\n📝 Summary of filled fields:")
        schema = result['schema']
        fields = schema.get('fields', [])
        if not fields and 'sections' in schema:
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
