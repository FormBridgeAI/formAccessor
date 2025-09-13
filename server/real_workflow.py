import os
import json
import time
import threading
from practice import extract_and_generate_schema
from image_generator import FormImageGenerator
from enhanced_coordinate_extractor import CoordinateExtractor
from openai import OpenAI
from dotenv import load_dotenv
import pyttsx3
import speech_recognition as sr

class SpeechFormFiller:
    def __init__(self):
        """Initialize the speech-enabled form filler"""
        load_dotenv()
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        # Initialize text-to-speech engine
        self.tts_engine = pyttsx3.init()
        self.setup_tts()
        
        # Initialize speech recognition
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        
        # Adjust for ambient noise
        print("🎤 Adjusting for ambient noise... Please wait.")
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
        print("✅ Microphone calibrated!")
        
    def setup_tts(self):
        """Configure text-to-speech settings"""
        voices = self.tts_engine.getProperty('voices')
        if voices:
            # Try to use a female voice if available
            for voice in voices:
                if 'female' in voice.name.lower() or 'zira' in voice.name.lower():
                    self.tts_engine.setProperty('voice', voice.id)
                    break
        
        # Set speech rate and volume
        self.tts_engine.setProperty('rate', 150)  # Speed of speech
        self.tts_engine.setProperty('volume', 0.9)  # Volume level (0.0 to 1.0)
    
    def speak(self, text):
        """Convert text to speech"""
        print(f" Speaking: {text}")
        self.tts_engine.say(text)
        self.tts_engine.runAndWait()
    
    def listen(self, timeout=10):
        """Listen for user speech input"""
        print(f"🎤 Listening... (timeout: {timeout}s)")
        
        try:
            with self.microphone as source:
                # Listen for audio with timeout
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=5)
            
            # Recognize speech using Google's service
            text = self.recognizer.recognize_google(audio)
            print(f"👤 You said: {text}")
            return text
            
        except sr.WaitTimeoutError:
            print("⏰ Timeout waiting for speech input")
            return None
        except sr.UnknownValueError:
            print("❓ Could not understand audio")
            return None
        except sr.RequestError as e:
            print(f"❌ Speech recognition error: {e}")
            return None
    
    def get_user_input_speech(self, question, field_type="text"):
        """Get user input through speech with fallback to text"""
        max_attempts = 3
        
        for attempt in range(max_attempts):
            # Speak the question
            self.speak(question)
            
            # Try to get speech input
            response = self.listen(timeout=15)
            
            if response:
                # Validate response based on field type
                if self.validate_response(response, field_type):
                    return response
                else:
                    self.speak("I didn't understand that. Please try again.")
            else:
                if attempt < max_attempts - 1:
                    self.speak("I didn't catch that. Please speak again.")
                else:
                    # Fallback to text input
                    print("🔄 Falling back to text input...")
                    return input(f"Please type your answer: ")
        
        return None
    
    def validate_response(self, response, field_type):
        """Basic validation for different field types"""
        if field_type == "email":
            return "@" in response and "." in response
        elif field_type == "phone":
            return any(char.isdigit() for char in response)
        elif field_type == "date":
            return any(char.isdigit() for char in response)
        else:
            return len(response.strip()) > 0

def real_form_workflow(input_image_path: str, output_image_path: str = None, use_speech: bool = False):
    """
    Real workflow: Process form image → Extract schema → Fill form → Generate filled image
    Uses actual Azure + OpenAI data from practice.py and interview.py
    
    Args:
        input_image_path (str): Path to the input form image
        output_image_path (str): Path for the output filled image (optional)
        use_speech (bool): Whether to use speech input for form filling
    """
    
    print("🚀 Starting REAL form workflow...")
    print(f"📸 Processing image: {input_image_path}")
    
    # Initialize speech filler if needed
    speech_filler = None
    if use_speech:
        try:
            speech_filler = SpeechFormFiller()
            speech_filler.speak("Welcome to Speech-Enabled Form Filling! I'll help you fill out forms using voice commands.")
        except Exception as e:
            print(f"⚠️  Speech initialization failed: {e}")
            print("🔄 Falling back to text input mode...")
            use_speech = False
    
    # Azure credentials (from your existing code)
    endpoint = 'https://aiformfilling-doc-ai.cognitiveservices.azure.com/'
    key = 'CTVcKut0gFiwLBPWB5dvHfJg33Lf3OCnPLmwHl0HmmYnrT1mh0pdJQQJ99BGACYeBjFXJ3w3AAALACOGVNkh'
    
    # Step 1: Extract and generate schema using your real practice.py
    print("\n📋 Step 1: Extracting form structure with Azure + OpenAI...")
    if use_speech and speech_filler:
        speech_filler.speak("I'm analyzing your form. Please wait a moment.")
    
    schema = extract_and_generate_schema(input_image_path)
    
    if not schema:
        error_msg = "❌ Could not extract schema. Please check the previous output for errors."
        print(error_msg)
        if use_speech and speech_filler:
            speech_filler.speak("Sorry, I couldn't analyze the form. Please check the image and try again.")
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
    
    if use_speech and speech_filler:
        speech_filler.speak(f"I found {len(required_fields)} required fields to fill out. Let's start!")
    
    # Fill each required field
    for i, field in enumerate(required_fields, 1):
        print(f"\n--- Field {i}/{len(required_fields)} ---")
        print(f"Label: {field.get('label', 'N/A')}")
        print(f"Type: {field.get('type', 'N/A')}")
        
        if field.get('options'):
            print(f"Options: {', '.join(field.get('options', []))}")
        
        # Get user input based on mode
        if use_speech and speech_filler:
            # Use speech input with AI-generated questions
            try:
                # Generate conversational question using OpenAI
                field_prompt = (
                    f"Ask the user for the following field in a conversational way:\n"
                    f"Label: {field.get('label','')}\n"
                    f"Type: {field.get('type','')}\n"
                    f"Options: {', '.join(field.get('options', [])) if field.get('options') else 'N/A'}\n"
                    f"Accessibility: {field.get('accessibility','')}\n"
                    f"Respond with only the question, keep it short and friendly."
                )
                
                ai_question = speech_filler.client.chat.completions.create(
                    model='gpt-4-1106-preview',
                    messages=[{
                        'role': 'system',
                        'content': "You are a helpful assistant guiding a user through filling out a digital form. Ask one required field at a time in a conversational way. Keep questions short and clear."
                    }, {
                        'role': 'user',
                        'content': field_prompt
                    }],
                    max_tokens=100,
                    temperature=0.3
                ).choices[0].message.content
                
                # Add progress indicator
                progress = f"Question {i} of {len(required_fields)}: "
                full_question = f"{progress}{ai_question}"
                
                # Get user input through speech
                user_input = speech_filler.get_user_input_speech(full_question, field.get('type', 'text'))
                
                if user_input:
                    field['value'] = user_input
                    # Confirm the input
                    speech_filler.speak(f"Got it! {field.get('label')}: {user_input}")
                else:
                    speech_filler.speak("Skipping this field. Let's continue.")
                    
            except Exception as e:
                print(f"Error processing field {field.get('label')} with speech: {e}")
                # Fallback to text input
                user_input = input(f"Enter value for '{field.get('label', '')}': ")
                field['value'] = user_input
        else:
            # Use text input (original behavior)
            user_input = input(f"Enter value for '{field.get('label', '')}': ")
            field['value'] = user_input
    
    print("\n✅ All required fields filled!")
    
    if use_speech and speech_filler:
        speech_filler.speak("Great! I've collected all the required information. Let me process the form now.")
    
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
        
        if use_speech and speech_filler:
            filled_fields = [f for f in required_fields if f.get('value')]
            speech_filler.speak(f"Form completed! I filled out {len(filled_fields)} fields for you.")
        
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
    # Ask user for input mode
    print("Choose input mode:")
    print("1. Text input (default)")
    print("2. Speech input")
    
    choice = input("Enter choice (1 or 2): ").strip()
    use_speech = choice == "2"
    
    # Use the form in sample_data folder starting with 427
    input_image = "/Users/asfawy/hopHack(fill.ai)/formAccessor/sample_data/simple-job-application-form-27d287c8e2b97cd3f175c12ef67426b2-classic.png"
    
    # Check if the image exists
    if not os.path.exists(input_image):
        print(f"❌ Image not found at: {input_image}")
        print("Please place your form image in the sample_data directory or update the path.")
        return
    
    # Run the real workflow
    result = real_form_workflow(input_image, use_speech=use_speech)
    
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