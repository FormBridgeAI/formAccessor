import os
import json
import time
import threading
from openai import OpenAI
from dotenv import load_dotenv
from practice import extract_and_generate_schema
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
        print(f"🔊 Speaking: {text}")
        self.tts_engine.say(text)
        self.tts_engine.runAndWait()
    
    def listen(self, timeout=10):
        """Listen for user speech input"""
        print(f"�� Listening... (timeout: {timeout}s)")
        
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
    
    def process_form_with_speech(self, input_image_path):
        """Main workflow: Extract schema and fill form using speech"""
        print("🚀 Starting Speech-Enabled Form Filling...")
        
        # Step 1: Extract schema
        print("📋 Extracting form structure...")
        self.speak("I'm analyzing your form. Please wait a moment.")
        
        schema = extract_and_generate_schema(input_image_path)
        if not schema:
            self.speak("Sorry, I couldn't analyze the form. Please check the image and try again.")
            return None
        
        # Flatten fields
        fields = []
        if "fields" in schema:
            fields = schema["fields"]
        elif "sections" in schema:
            for section in schema["sections"]:
                fields.extend(section.get("fields", []))
        
        # Filter required fields
        required_fields = [f for f in fields if f.get('required')]
        
        if not required_fields:
            self.speak("No required fields found in this form.")
            return schema
        
        self.speak(f"I found {len(required_fields)} required fields to fill out. Let's start!")
        
        # Step 2: Fill fields using speech
        messages = [{
            'role': 'system',
            'content': (
                "You are a helpful assistant guiding a user through filling out a digital form. "
                "Ask one required field at a time in a conversational way. "
                "Keep questions short and clear. When all required fields are filled, "
                "respond ONLY with the completed schema in valid JSON format."
            )
        }]
        
        for i, field in enumerate(required_fields):
            # Generate question using OpenAI
            field_prompt = (
                f"Ask the user for the following field in a conversational way:\n"
                f"Label: {field.get('label','')}\n"
                f"Type: {field.get('type','')}\n"
                f"Options: {', '.join(field.get('options', [])) if field.get('options') else 'N/A'}\n"
                f"Accessibility: {field.get('accessibility','')}\n"
                f"Respond with only the question, keep it short and friendly."
            )
            
            messages.append({'role': 'user', 'content': field_prompt})
            
            try:
                ai_question = self.client.chat.completions.create(
                    model='gpt-4-1106-preview',
                    messages=messages[-6:],
                    max_tokens=100,
                    temperature=0.3
                ).choices[0].message.content
                
                # Add progress indicator
                progress = f"Question {i+1} of {len(required_fields)}: "
                full_question = f"{progress}{ai_question}"
                
                # Get user input through speech
                user_input = self.get_user_input_speech(full_question, field.get('type', 'text'))
                
                if user_input:
                    field['value'] = user_input
                    messages.append({'role': 'assistant', 'content': ai_question})
                    messages.append({'role': 'user', 'content': user_input})
                    
                    # Confirm the input
                    self.speak(f"Got it! {field.get('label')}: {user_input}")
                else:
                    self.speak("Skipping this field. Let's continue.")
                    
            except Exception as e:
                print(f"Error processing field {field.get('label')}: {e}")
                self.speak("There was an error with this field. Let's continue.")
        
        # Step 3: Complete the form
        self.speak("Great! I've collected all the required information. Let me process the form now.")
        
        # Save completed schema
        schema_path = f"completed_schema_speech_{int(time.time())}.json"
        with open(schema_path, 'w') as f:
            json.dump(schema, f, indent=2)
        
        print(f"\n✅ Form filling completed!")
        print(f"📄 Completed schema saved to: {schema_path}")
        
        # Show summary
        filled_fields = [f for f in required_fields if f.get('value')]
        self.speak(f"Form completed! I filled out {len(filled_fields)} fields for you.")
        
        return {
            'schema': schema,
            'schema_path': schema_path,
            'filled_fields_count': len(filled_fields)
        }

def main():
    """Main function to run speech-enabled form filling"""
    # Initialize speech form filler
    speech_filler = SpeechFormFiller()
    
    # Welcome message
    speech_filler.speak("Welcome to Speech-Enabled Form Filling! I'll help you fill out forms using voice commands.")
    
    # Use the form in sample_data folder
    input_image = "/Users/asfawy/hopHack(fill.ai)/formAccessor/sample_data/simple-job-application-form-27d287c8e2b97cd3f175c12ef67426b2-classic.png"
    
    # Check if image exists
    if not os.path.exists(input_image):
        speech_filler.speak("Sorry, I couldn't find the form image. Please check the file path.")
        print(f"❌ Image not found at: {input_image}")
        return
    
    # Process the form
    result = speech_filler.process_form_with_speech(input_image)
    
    if result:
        speech_filler.speak("Form processing completed successfully! You can now view the filled form.")
        print("\n🎉 Speech-enabled form filling completed!")
        print(f"📄 Schema saved to: {result['schema_path']}")
        print(f"📝 Fields filled: {result['filled_fields_count']}")
    else:
        speech_filler.speak("Sorry, there was an error processing the form. Please try again.")
        print("❌ Form processing failed.")

if __name__ == "__main__":
    main()
