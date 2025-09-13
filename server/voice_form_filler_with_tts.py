"""
Voice-Enabled Form Filling with Text-to-Speech using Deepgram
Uses Deepgram's speech-to-text for user input and text-to-speech for AI questions
"""

import os
import json
import time
import pyaudio
import wave
import threading
import subprocess
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

from deepgram import DeepgramClient, PrerecordedOptions, SpeakOptions

# Load environment variables
load_dotenv("../.env")

class VoiceFormFillerWithTTS:
    def __init__(self, form_schema: Dict[str, Any]):
        """
        Initialize the Voice Form Filler with TTS
        
        Args:
            form_schema: The extracted form schema from Azure Document Intelligence
        """
        self.form_schema = form_schema
        self.filled_fields = {}
        self.current_field_index = 0
        self.required_fields = []
        
        # Initialize Deepgram client
        self.api_key = os.getenv("DEEPGRAM_API_KEY")
        if not self.api_key:
            raise ValueError("DEEPGRAM_API_KEY environment variable is not set")
        
        self.deepgram = DeepgramClient(self.api_key)
        
        # Audio recording settings
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 16000
        self.RECORD_SECONDS = 5  # Record for 5 seconds at a time
        
        # Extract required fields from schema
        self._extract_required_fields()
    
    def _extract_required_fields(self):
        """Extract required fields from the form schema"""
        fields = self.form_schema.get('fields', [])
        if not fields and 'sections' in self.form_schema:
            for section in self.form_schema['sections']:
                fields.extend(section.get('fields', []))
        
        self.required_fields = [field for field in fields if field.get('required', False)]
        print(f"Found {len(self.required_fields)} required fields to fill")
    
    def speak_text(self, text: str, filename: str = None):
        """
        Convert text to speech using Deepgram and play it
        
        Args:
            text: Text to convert to speech
            filename: Optional filename to save the audio
        """
        try:
            if not filename:
                filename = f"temp_speech_{int(time.time())}.mp3"
            
            print(f"🔊 Speaking: '{text}'")
            
            # Create text payload
            text_payload = {"text": text}
            
            # Configure TTS options
            options = SpeakOptions(
                model="aura-2-thalia-en",
            )
            
            # Generate speech
            response = self.deepgram.speak.v("1").save(
                filename,
                text_payload,
                options,
            )
            
            print(f"✅ Speech generated: {filename}")
            
            # Play the audio file
            self.play_audio_file(filename)
            
            # Clean up the file after playing
            try:
                os.remove(filename)
            except:
                pass
                
        except Exception as e:
            print(f"❌ TTS error: {e}")
    
    def play_audio_file(self, filename: str):
        """
        Play an audio file using the system's default audio player
        
        Args:
            filename: Path to the audio file
        """
        try:
            # Try different audio players based on the system
            if os.name == 'nt':  # Windows
                os.startfile(filename)
            elif os.name == 'posix':  # macOS and Linux
                subprocess.run(['afplay', filename], check=True)
            else:
                # Fallback for other systems
                subprocess.run(['play', filename], check=True)
        except Exception as e:
            print(f"⚠️  Could not play audio automatically: {e}")
            print(f"Audio file saved as: {filename}")
    
    def record_audio(self, duration: int = 5) -> str:
        """
        Record audio from microphone and save to temporary file
        
        Args:
            duration: Recording duration in seconds
            
        Returns:
            str: Path to the recorded audio file
        """
        print(f"🎤 Recording for {duration} seconds... Speak now!")
        
        # Initialize PyAudio
        p = pyaudio.PyAudio()
        
        # Open stream
        stream = p.open(
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.RATE,
            input=True,
            frames_per_buffer=self.CHUNK
        )
        
        frames = []
        
        # Record audio
        for i in range(0, int(self.RATE / self.CHUNK * duration)):
            data = stream.read(self.CHUNK)
            frames.append(data)
        
        print("✅ Recording complete!")
        
        # Stop and close stream
        stream.stop_stream()
        stream.close()
        p.terminate()
        
        # Save to file
        filename = f"temp_audio_{int(time.time())}.wav"
        wf = wave.open(filename, 'wb')
        wf.setnchannels(self.CHANNELS)
        wf.setsampwidth(p.get_sample_size(self.FORMAT))
        wf.setframerate(self.RATE)
        wf.writeframes(b''.join(frames))
        wf.close()
        
        return filename
    
    def transcribe_audio(self, audio_file_path: str) -> str:
        """
        Transcribe audio file using Deepgram
        
        Args:
            audio_file_path: Path to the audio file
            
        Returns:
            str: Transcribed text
        """
        try:
            print("🔄 Transcribing audio...")
            
            with open(audio_file_path, "rb") as audio:
                buffer_data = audio.read()
            
            payload = {"buffer": buffer_data}
            
            options = PrerecordedOptions(
                model="nova-3",
                language="en",
            )
            
            response = self.deepgram.listen.rest.v("1").transcribe_file(
                payload,
                options,
            )
            
            # Extract transcript
            transcript = response.results.channels[0].alternatives[0].transcript
            print(f"📝 Transcribed: '{transcript}'")
            
            return transcript.strip()
            
        except Exception as e:
            print(f"❌ Transcription error: {e}")
            return ""
    
    def generate_question_text(self, field: Dict[str, Any], field_number: int, total_fields: int) -> str:
        """
        Generate a natural language question for a form field
        
        Args:
            field: The form field dictionary
            field_number: Current field number
            total_fields: Total number of fields
            
        Returns:
            str: Generated question text
        """
        field_label = field.get('label', 'Unknown')
        field_type = field.get('type', 'text')
        
        # Create natural language questions based on field type and label
        if 'name' in field_label.lower():
            if 'first' in field_label.lower():
                return f"Question {field_number} of {total_fields}. What is your first name?"
            elif 'last' in field_label.lower():
                return f"Question {field_number} of {total_fields}. What is your last name?"
            else:
                return f"Question {field_number} of {total_fields}. What is your full name?"
        elif 'date' in field_label.lower() or 'birth' in field_label.lower():
            return f"Question {field_number} of {total_fields}. What is your date of birth? Please say the month, day, and year."
        elif 'address' in field_label.lower():
            return f"Question {field_number} of {total_fields}. What is your address? Please include street, city, and state."
        elif 'email' in field_label.lower():
            return f"Question {field_number} of {total_fields}. What is your email address?"
        elif 'phone' in field_label.lower():
            return f"Question {field_number} of {total_fields}. What is your phone number?"
        elif 'city' in field_label.lower():
            return f"Question {field_number} of {total_fields}. What city do you live in?"
        elif 'state' in field_label.lower():
            return f"Question {field_number} of {total_fields}. What state do you live in?"
        elif 'zip' in field_label.lower() or 'postal' in field_label.lower():
            return f"Question {field_number} of {total_fields}. What is your zip code or postal code?"
        else:
            return f"Question {field_number} of {total_fields}. {field_label}. Please provide your answer."
    
    def fill_form_with_voice_and_tts(self):
        """Fill the form using voice input with TTS questions"""
        print("🎤 Starting Voice Form Filling Session with Text-to-Speech...")
        print("I will ask you questions out loud, and you can respond by speaking.")
        print("Press Ctrl+C to stop at any time.\n")
        
        # Welcome message
        welcome_text = f"Hello! I'm Fill.ai, your voice assistant. I'll help you fill out this form by asking you {len(self.required_fields)} questions. Let's begin!"
        self.speak_text(welcome_text)
        
        try:
            for i, field in enumerate(self.required_fields, 1):
                field_label = field.get('label', 'Unknown')
                field_type = field.get('type', 'text')
                
                print(f"\n--- Field {i}/{len(self.required_fields)} ---")
                print(f"Field: {field_label}")
                print(f"Type: {field_type}")
                
                # Generate and speak the question
                question_text = self.generate_question_text(field, i, len(self.required_fields))
                self.speak_text(question_text)
                
                # Record audio
                audio_file = self.record_audio(duration=self.RECORD_SECONDS)
                
                # Transcribe audio
                transcript = self.transcribe_audio(audio_file)
                
                if transcript:
                    # Store the transcribed text
                    self.filled_fields[field_label] = transcript
                    print(f"✅ Captured: '{transcript}'")
                    
                    # Confirm the answer
                    confirmation_text = f"Got it! You said: {transcript}. Moving to the next question."
                    self.speak_text(confirmation_text)
                else:
                    print("⚠️  No speech detected, skipping this field")
                    skip_text = "I didn't catch that. Let's move to the next question."
                    self.speak_text(skip_text)
                
                # Clean up audio file
                try:
                    os.remove(audio_file)
                except:
                    pass
                
                # Small delay between questions
                time.sleep(1)
            
            # Completion message
            completion_text = f"Excellent! I've collected all your information. You've completed all {len(self.required_fields)} required fields. Thank you!"
            self.speak_text(completion_text)
            
            print("\n🎉 Voice form filling completed!")
            self._show_summary()
            
        except KeyboardInterrupt:
            print("\n\n🛑 Voice form filling stopped by user")
            stop_text = "Form filling stopped. Thank you for using Fill.ai!"
            self.speak_text(stop_text)
            self._show_summary()
    
    def _show_summary(self):
        """Show a summary of filled fields"""
        print("\n📝 Summary of filled fields:")
        if self.filled_fields:
            for field_label, value in self.filled_fields.items():
                print(f"  • {field_label}: {value}")
        else:
            print("  No fields were filled")
    
    def get_filled_schema(self):
        """Get the form schema with filled values"""
        # Update the schema with filled values
        updated_schema = self.form_schema.copy()
        
        # Update fields with filled values
        fields = updated_schema.get('fields', [])
        if not fields and 'sections' in updated_schema:
            for section in updated_schema['sections']:
                fields = section.get('fields', [])
                break
        
        for field in fields:
            if field['label'] in self.filled_fields:
                field['value'] = self.filled_fields[field['label']]
        
        return updated_schema

def main():
    """Example usage of the Voice Form Filler with TTS"""
    # Load a sample form schema (you would get this from your existing workflow)
    sample_schema = {
        "fields": [
            {
                "label": "Full Name",
                "type": "text",
                "required": True
            },
            {
                "label": "Date of Birth",
                "type": "date",
                "required": True
            },
            {
                "label": "Address",
                "type": "text",
                "required": True
            }
        ]
    }
    
    # Create voice form filler with TTS
    filler = VoiceFormFillerWithTTS(sample_schema)
    
    # Fill form with voice and TTS
    filler.fill_form_with_voice_and_tts()
    
    # Get filled schema
    filled_schema = filler.get_filled_schema()
    print(f"\nFinal filled form data: {json.dumps(filled_schema, indent=2)}")

if __name__ == "__main__":
    main()
