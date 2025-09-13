"""
Voice-Enabled Form Filling with Text-to-Speech and Data Formatting
Uses Deepgram's speech-to-text for user input and text-to-speech for AI questions
Includes proper data formatting for dates, addresses, etc.
"""

import os
import json
import time
import pyaudio
import wave
import threading
import subprocess
import re
from datetime import datetime
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

from deepgram import DeepgramClient, PrerecordedOptions, SpeakOptions

# Load environment variables
load_dotenv("../.env")

class VoiceFormFillerWithFormatting:
    def __init__(self, form_schema: Dict[str, Any]):
        """
        Initialize the Voice Form Filler with TTS and formatting
        
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
    
    def format_field_value(self, raw_value: str, field: Dict[str, Any]) -> str:
        """
        Format the raw transcribed value based on field type
        
        Args:
            raw_value: Raw transcribed text
            field: Field information including type and label
            
        Returns:
            str: Formatted value
        """
        field_type = field.get('type', 'text').lower()
        field_label = field.get('label', '').lower()
        
        if field_type == 'date' or 'date' in field_label or 'birth' in field_label:
            return self._format_date(raw_value)
        elif field_type == 'email' or 'email' in field_label:
            return self._format_email(raw_value)
        elif field_type == 'phone' or 'phone' in field_label or 'number' in field_label:
            return self._format_phone(raw_value)
        elif 'address' in field_label:
            return self._format_address(raw_value)
        elif 'zip' in field_label or 'postal' in field_label:
            return self._format_zip_code(raw_value)
        elif 'name' in field_label:
            return self._format_name(raw_value)
        else:
            return raw_value.strip()
    
    def _format_date(self, raw_value: str) -> str:
        """Format date input to MM/DD/YYYY format"""
        try:
            # Clean the input
            text = raw_value.lower().strip()
            
            # Common month mappings
            month_map = {
                'january': '01', 'jan': '01',
                'february': '02', 'feb': '02',
                'march': '03', 'mar': '03',
                'april': '04', 'apr': '04',
                'may': '05',
                'june': '06', 'jun': '06',
                'july': '07', 'jul': '07',
                'august': '08', 'aug': '08',
                'september': '09', 'sep': '09', 'sept': '09',
                'october': '10', 'oct': '10',
                'november': '11', 'nov': '11',
                'december': '12', 'dec': '12'
            }
            
            # Try to extract date components
            # Pattern 1: "october 5 2006" or "oct 5 2006"
            month_pattern = r'(january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)'
            day_pattern = r'(\d{1,2})'
            year_pattern = r'(\d{4})'
            
            # Look for month day year pattern
            month_match = re.search(month_pattern, text)
            day_match = re.search(day_pattern, text)
            year_match = re.search(year_pattern, text)
            
            if month_match and day_match and year_match:
                month = month_map.get(month_match.group(1), '01')
                day = day_match.group(1).zfill(2)
                year = year_match.group(1)
                return f"{month}/{day}/{year}"
            
            # Pattern 2: "10/5/2006" or "10-5-2006"
            date_pattern = r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})'
            date_match = re.search(date_pattern, text)
            if date_match:
                month = date_match.group(1).zfill(2)
                day = date_match.group(2).zfill(2)
                year = date_match.group(3)
                return f"{month}/{day}/{year}"
            
            # Pattern 3: "5/10/2006" (day/month/year)
            date_pattern2 = r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})'
            date_match2 = re.search(date_pattern2, text)
            if date_match2:
                day = date_match2.group(1).zfill(2)
                month = date_match2.group(2).zfill(2)
                year = date_match2.group(3)
                return f"{month}/{day}/{year}"
            
            # If no pattern matches, return as is
            return raw_value.strip()
            
        except Exception as e:
            print(f"Date formatting error: {e}")
            return raw_value.strip()
    
    def _format_email(self, raw_value: str) -> str:
        """Format email input"""
        text = raw_value.strip().lower()
        # Basic email validation
        if '@' in text and '.' in text:
            return text
        else:
            return raw_value.strip()
    
    def _format_phone(self, raw_value: str) -> str:
        """Format phone number to (XXX) XXX-XXXX format"""
        try:
            # Extract only digits
            digits = re.sub(r'[^\d]', '', raw_value)
            
            if len(digits) == 10:
                return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
            elif len(digits) == 11 and digits[0] == '1':
                return f"({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
            else:
                return raw_value.strip()
        except:
            return raw_value.strip()
    
    def _format_address(self, raw_value: str) -> str:
        """Format address input"""
        # Capitalize first letter of each word
        words = raw_value.strip().split()
        formatted_words = [word.capitalize() for word in words]
        return ' '.join(formatted_words)
    
    def _format_zip_code(self, raw_value: str) -> str:
        """Format zip code input"""
        # Extract only digits
        digits = re.sub(r'[^\d]', '', raw_value)
        if len(digits) == 5:
            return digits
        elif len(digits) == 9:
            return f"{digits[:5]}-{digits[5:]}"
        else:
            return raw_value.strip()
    
    def _format_name(self, raw_value: str) -> str:
        """Format name input (capitalize each word)"""
        words = raw_value.strip().split()
        formatted_words = [word.capitalize() for word in words]
        return ' '.join(formatted_words)
    
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
            return f"Question {field_number} of {total_fields}. What is your date of birth? Please say the month, day, and year. For example, say 'October 5, 2006'."
        elif 'address' in field_label.lower():
            return f"Question {field_number} of {total_fields}. What is your address? Please include street, city, and state."
        elif 'email' in field_label.lower():
            return f"Question {field_number} of {total_fields}. What is your email address?"
        elif 'phone' in field_label.lower():
            return f"Question {field_number} of {total_fields}. What is your phone number? Please say all 10 digits."
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
                    # Format the value based on field type
                    formatted_value = self.format_field_value(transcript, field)
                    
                    # Store the formatted value
                    self.filled_fields[field_label] = formatted_value
                    print(f"✅ Captured: '{transcript}' -> Formatted: '{formatted_value}'")
                    
                    # Confirm the answer
                    confirmation_text = f"Got it! You said: {transcript}. I've formatted it as: {formatted_value}. Moving to the next question."
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
    """Example usage of the Voice Form Filler with TTS and formatting"""
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
            },
            {
                "label": "Phone Number",
                "type": "phone",
                "required": True
            }
        ]
    }
    
    # Create voice form filler with TTS and formatting
    filler = VoiceFormFillerWithFormatting(sample_schema)
    
    # Fill form with voice and TTS
    filler.fill_form_with_voice_and_tts()
    
    # Get filled schema
    filled_schema = filler.get_filled_schema()
    print(f"\nFinal filled form data: {json.dumps(filled_schema, indent=2)}")

if __name__ == "__main__":
    main()
