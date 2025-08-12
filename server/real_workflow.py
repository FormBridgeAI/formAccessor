import os
import json
from practice import extract_and_generate_schema
from image_generator import FormImageGenerator
from enhanced_coordinate_extractor import CoordinateExtractor
import time

def real_form_workflow(input_image_path: str, output_image_path: str = None):
    """
    Real workflow: Process form image → Extract schema → Fill form → Generate filled image
    Uses actual Azure + OpenAI data from practice.py and interview.py
    
    Args:
        input_image_path (str): Path to the input form image
        output_image_path (str): Path for the output filled image (optional)
    """
    
    print("🚀 Starting REAL form workflow...")
    print(f"📸 Processing image: {input_image_path}")
    
    # Azure credentials (from your existing code)
    endpoint = 'https://aiformfilling-doc-ai.cognitiveservices.azure.com/'
    key = 'CTVcKut0gFiwLBPWB5dvHfJg33Lf3OCnPLmwHl0HmmYnrT1mh0pdJQQJ99BGACYeBjFXJ3w3AAALACOGVNkh'
    
    # Step 1: Extract and generate schema using your real practice.py
    print("\n📋 Step 1: Extracting form structure with Azure + OpenAI...")
    schema = extract_and_generate_schema(input_image_path)
    
    if not schema:
        print("❌ Could not extract schema. Please check the previous output for errors.")
        return None
    
    print("✅ Schema extracted successfully!")
    
    # Step 2: Check for existing manual coordinates or extract new ones
    print("\n📐 Step 2: Checking for field coordinates...")
    
    # First, check if manual coordinates already exist
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
    
    # If no manual coordinates exist, run automatic detection
    if not field_coordinates:
        print("🔍 No manual coordinates found. Running automatic coordinate detection...")
        extractor = CoordinateExtractor(endpoint, key)
        field_coordinates = extractor.get_coordinate_mapping(input_image_path)
        
        if not field_coordinates:
            print("⚠️  No field coordinates found. Will use estimated positioning.")
            field_coordinates = {}
    
    # Step 3: Fill the form interactively (like your interview.py)
    print("\n✍️  Step 3: Filling out the form...")
    
    # Get required fields
    fields = []
    if "fields" in schema:
        fields = schema["fields"]
    elif "sections" in schema:
        for section in schema["sections"]:
            fields.extend(section.get("fields", []))
    
    required_fields = [f for f in fields if f.get('required')]
    
    print(f"Found {len(required_fields)} required fields to fill.")
    
    # Fill each required field
    for i, field in enumerate(required_fields, 1):
        print(f"\n--- Field {i}/{len(required_fields)} ---")
        print(f"Label: {field.get('label', 'N/A')}")
        print(f"Type: {field.get('type', 'N/A')}")
        
        if field.get('options'):
            print(f"Options: {', '.join(field.get('options', []))}")
        
        # Get user input
        user_input = input(f"Enter value for '{field.get('label', '')}': ")
        field['value'] = user_input
    
    print("\n✅ All required fields filled!")
    
    # Step 4: Generate the filled form image using precise coordinates
    print("\n🎨 Step 4: Generating filled form image with precise positioning...")
    
    try:
        generator = FormImageGenerator(input_image_path)
        
        if output_image_path is None:
            # Generate default output path
            base_name = os.path.splitext(os.path.basename(input_image_path))[0]
            output_image_path = f"completed_{base_name}.jpg"
        
        # Use precise coordinates if available, fall back to estimated if not
        if field_coordinates:
            print(f"🎯 Using {len(field_coordinates)} precise field coordinates...")
            final_image_path = generator.generate_filled_image_with_coordinates(schema, field_coordinates, output_image_path)
        else:
            print("⚠️  Using estimated positioning...")
            final_image_path = generator.generate_filled_image(schema, output_image_path)
        
        print(f"✅ Filled form image generated: {final_image_path}")
        
        # Save the completed schema
        schema_path = "completed_schema.json"
        with open(schema_path, 'w') as f:
            json.dump(schema, f, indent=2)
        print(f"💾 Completed schema saved to: {schema_path}")
        
        # Save the field coordinates for future use
        if field_coordinates:
            coords_path = "field_coordinates.json"
            with open(coords_path, 'w') as f:
                json.dump(field_coordinates, f, indent=2)
            print(f"📐 Field coordinates saved to: {coords_path}")
            
            # Add helpful message about manual editing
            print("💡 Tip: You can manually edit this file to adjust field positions!")
            print("   - Edit the X,Y coordinates in field_coordinates.json")
            print("   - Run the workflow again to use your manual adjustments")
        
        return {
            'schema': schema,
            'filled_image_path': final_image_path,
            'schema_path': schema_path,
            'field_coordinates': field_coordinates
        }
        
    except Exception as e:
        print(f"❌ Error generating filled image: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """
    Main function to run the real workflow
    """
    # Use the form in sample_data folder starting with 427
    input_image = "/Users/asfawy/jsonTest/sample_data/simple-job-application-form-27d287c8e2b97cd3f175c12ef67426b2-classic.png"
    
    # Check if the image exists
    if not os.path.exists(input_image):
        print(f"❌ Image not found at: {input_image}")
        print("Please place your form image in the sample_data directory or update the path.")
        return
    
    # Run the real workflow
    result = real_form_workflow(input_image)
    
    if result:
        print("\n🎉 Real workflow completed successfully!")
        print(f"📄 Filled form image: {result['filled_image_path']}")
        print(f"📋 Completed schema: {result['schema_path']}")
        
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
            print(f"\n🎯 Field coordinates used: {len(result['field_coordinates'])} precise positions")
    else:
        print("\n❌ Workflow failed. Please check the error messages above.")

if __name__ == "__main__":
    main() 