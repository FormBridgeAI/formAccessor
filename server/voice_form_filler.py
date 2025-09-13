"""
Voice-Enabled Form Filling with Sequential Conversation Flow
Ensures only one voice speaks at a time: Ask -> Wait -> Confirm -> Next
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

class VoiceFormFiller:
    def __init__(self, form_schema: Dict[str, Any]):
        """
        Initialize the Voice Form Filler
        
        Args:
            form_schema: The extracted form schema from Azure Document Intelligence
        """
        self.form_schema = form_schema
        self.filled_fields = {}
        self.current_field_index = 0
        self.required_fields = []
        self.is_speaking = False  # Flag to prevent overlapping speech
        
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
        self.RECORD_SECONDS = 5
        
        # Extract required fields from schema
        self._extract_required_fields()
    
    def _extract_required_fields(self):
        """Extract required fields from the form schema"""
        # Handle different schema structures
        fields = []
        
        # Check for direct fields array
        if 'fields' in self.form_schema:
            fields = self.form_schema['fields']
        # Check for nested form.fields structure
        elif 'form' in self.form_schema and 'fields' in self.form_schema['form']:
            fields = self.form_schema['form']['fields']
        # Check for sections structure
        elif 'sections' in self.form_schema:
            for section in self.form_schema['sections']:
                fields.extend(section.get('fields', []))
        
        # If no fields are marked as required, treat all fields as required
        self.required_fields = [field for field in fields if field.get('required', False)]
        
        # If still no required fields, treat all fields as required
        if not self.required_fields:
            self.required_fields = fields
            print(f"⚠️  No fields marked as required, treating all {len(fields)} fields as required")
        
        print(f"Found {len(self.required_fields)} fields to fill")
        
        # Debug: print field details
        for i, field in enumerate(self.required_fields[:5]):  # Show first 5 fields
            print(f"  Field {i+1}: {field.get('label', 'Unknown')} (required: {field.get('required', False)})")
    
    def _convert_words_to_numbers(self, text: str) -> str:
        """Convert spoken numbers to digits (e.g., 'two thousand' -> '2000')"""
        # Number word mappings
        number_words = {
            'zero': '0', 'one': '1', 'two': '2', 'three': '3', 'four': '4',
            'five': '5', 'six': '6', 'seven': '7', 'eight': '8', 'nine': '9',
            'ten': '10', 'eleven': '11', 'twelve': '12', 'thirteen': '13',
            'fourteen': '14', 'fifteen': '15', 'sixteen': '16', 'seventeen': '17',
            'eighteen': '18', 'nineteen': '19', 'twenty': '20', 'thirty': '30',
            'forty': '40', 'fifty': '50', 'sixty': '60', 'seventy': '70',
            'eighty': '80', 'ninety': '90', 'hundred': '00', 'thousand': '000',
            'million': '000000', 'billion': '000000000'
        }
        
        # Convert to lowercase for matching
        text_lower = text.lower()
        
        # Handle compound numbers like "twenty five" -> "25"
        for word, digit in number_words.items():
            if word in text_lower:
                text_lower = text_lower.replace(word, digit)
        
        # Handle special cases for compound numbers
        # Pattern: "twenty five" -> "25"
        compound_pattern = r'(\d+)\s+(\d+)'
        def combine_numbers(match):
            first = int(match.group(1))
            second = int(match.group(2))
            if first < 10 and second < 10:  # e.g., "2 5" -> "25"
                return str(first * 10 + second)
            else:
                return match.group(0)
        
        text_lower = re.sub(compound_pattern, combine_numbers, text_lower)
        
        # Handle "hundred" and "thousand" multipliers
        # Pattern: "2 hundred" -> "200", "3 thousand" -> "3000"
        hundred_pattern = r'(\d+)\s*hundred'
        thousand_pattern = r'(\d+)\s*thousand'
        
        def process_hundred(match):
            num = int(match.group(1))
            return str(num * 100)
        
        def process_thousand(match):
            num = int(match.group(1))
            return str(num * 1000)
        
        text_lower = re.sub(hundred_pattern, process_hundred, text_lower)
        text_lower = re.sub(thousand_pattern, process_thousand, text_lower)
        
        return text_lower
    
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
        
        # Convert spoken numbers to digits first
        if field_type == 'number' or 'number' in field_label or 'year' in field_label or 'day' in field_label:
            raw_value = self._convert_words_to_numbers(raw_value)
        
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
        elif field_type == 'number' or 'number' in field_label:
            # Extract only digits for number fields
            digits = re.sub(r'[^\d]', '', raw_value)
            return digits if digits else raw_value.strip()
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
            
            # If no pattern matches, return as is
            return raw_value.strip()
            
        except Exception as e:
            print(f"Date formatting error: {e}")
            return raw_value.strip()
    
    def _format_email(self, raw_value: str) -> str:
        """Format email input"""
        text = raw_value.strip().lower()
        if '@' in text and '.' in text:
            return text
        else:
            return raw_value.strip()
    
    def _format_phone(self, raw_value: str) -> str:
        """Format phone number to (XXX) XXX-XXXX format"""
        try:
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
        words = raw_value.strip().split()
        formatted_words = [word.capitalize() for word in words]
        return ' '.join(formatted_words)
    
    def _format_zip_code(self, raw_value: str) -> str:
        """Format zip code input"""
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
    
    def speak_text(self, text: str):
        """
        Convert text to speech using Deepgram and play it (sequential - waits for completion)
        
        Args:
            text: Text to convert to speech
        """
        # Wait for any previous speech to finish
        while self.is_speaking:
            time.sleep(0.1)
        
        self.is_speaking = True
        
        try:
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
            
            # Play the audio file and wait for completion
            self.play_audio_file_and_wait(filename)
            
            # Clean up the file
            self._cleanup_file(filename)
                
        except Exception as e:
            print(f"❌ TTS error: {e}")
        finally:
            self.is_speaking = False
    
    def _cleanup_file(self, filename: str):
        """Clean up audio file"""
        try:
            os.remove(filename)
        except:
            pass
    
    def play_audio_file_and_wait(self, filename: str):
        """
        Play an audio file and wait for completion
        
        Args:
            filename: Path to the audio file
        """
        try:
            # Try different audio players based on the system
            if os.name == 'nt':  # Windows
                os.startfile(filename)
                # Wait for audio to finish (estimate based on text length)
                time.sleep(len(filename) * 0.1)  # Rough estimate
            elif os.name == 'posix':  # macOS and Linux
                result = subprocess.run(['afplay', filename], check=True, capture_output=True)
                # afplay blocks until completion, so no need to wait
            else:
                # Fallback for other systems
                subprocess.run(['play', filename], check=True)
        except Exception as e:
            print(f"⚠️  Could not play audio automatically: {e}")
            print(f"Audio file saved as: {filename}")
            # Wait a bit anyway to simulate speech time
            time.sleep(2)
    
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
            
            # Use normal model for transcription
            options = PrerecordedOptions(
                model="nova-2",
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
        Generate a question for a form field
        
        Args:
            field: The form field dictionary
            field_number: Current field number
            total_fields: Total number of fields
            
        Returns:
            str: Generated question text
        """
        field_label = field.get('label', 'Unknown')
        field_type = field.get('type', 'text')
        
        # Create questions
        if 'name' in field_label.lower():
            if 'first' in field_label.lower():
                return f"What is your first name?"
            elif 'last' in field_label.lower():
                return f"What is your last name?"
            elif 'middle' in field_label.lower():
                return f"What is your middle name?"
            else:
                return f"What is your full name?"
        elif 'date' in field_label.lower() or 'birth' in field_label.lower():
            if 'month' in field_label.lower():
                return f"What month were you born?"
            elif 'day' in field_label.lower():
                return f"What day were you born?"
            elif 'year' in field_label.lower():
                return f"What year were you born?"
            else:
                return f"What is your date of birth? Please say the month, day, and year."
        elif 'address' in field_label.lower():
            if 'line 2' in field_label.lower():
                return f"What is your address line 2?"
            else:
                return f"What is your street address?"
        elif 'email' in field_label.lower():
            return f"What is your email address?"
        elif 'phone' in field_label.lower():
            return f"What is your phone number?"
        elif 'city' in field_label.lower():
            return f"What city do you live in?"
        elif 'state' in field_label.lower() or 'province' in field_label.lower():
            return f"What state or province do you live in?"
        elif 'zip' in field_label.lower() or 'postal' in field_label.lower():
            return f"What is your zip code?"
        elif field_type == 'number' or 'number' in field_label.lower():
            return f"What is your {field_label.lower()}? Please say the number."
        else:
            return f"What is your {field_label.lower()}?"
    
    def fill_form_with_voice(self):
        """Fill the form using voice input with sequential conversation flow"""
        print("🎤 Starting Voice Form Filling Session...")
        print("Sequential conversation: AI asks -> You answer -> AI confirms -> Next question")
        print("Press Ctrl+C to stop at any time.\n")
        
        # Welcome message
        welcome_text = f"Hello! I'll help you fill out this form. I need to ask you {len(self.required_fields)} questions. Let's begin!"
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
                    
                    # Confirmation
                    if i < len(self.required_fields):
                        confirmation_text = f"Thank you! I got {formatted_value}. Let's move to the next question."
                    else:
                        confirmation_text = f"Perfect! I got {formatted_value}. That's all the information I need. Thank you!"
                    
                    self.speak_text(confirmation_text)
                else:
                    print("⚠️  No speech detected, skipping this field")
                    if i < len(self.required_fields):
                        skip_text = "I didn't hear anything. Let's move to the next question."
                    else:
                        skip_text = "I didn't hear anything. That's all the questions I have. Thank you!"
                    self.speak_text(skip_text)
                
                # Clean up audio file
                try:
                    os.remove(audio_file)
                except:
                    pass
            
            print("\n🎉 Voice form filling completed!")
            self._show_summary()
            
        except KeyboardInterrupt:
            print("\n\n🛑 Voice form filling stopped by user")
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
        
        # Update fields with filled values - handle different schema structures
        if 'fields' in updated_schema:
            fields = updated_schema['fields']
        elif 'form' in updated_schema and 'fields' in updated_schema['form']:
            fields = updated_schema['form']['fields']
        elif 'sections' in updated_schema:
            fields = []
            for section in updated_schema['sections']:
                fields.extend(section.get('fields', []))
        else:
            fields = []
        
        for field in fields:
            if field['label'] in self.filled_fields:
                field['value'] = self.filled_fields[field['label']]
        
        return updated_schema

def main():
    """Example usage of the Voice Form Filler"""
    # Load a sample form schema
    sample_schema = {
        "form": {
            "fields": [
                {
                    "label": "First Name",
                    "type": "text",
                    "required": True
                },
                {
                    "label": "Last Name",
                    "type": "text",
                    "required": True
                },
                {
                    "label": "Birth Year",
                    "type": "number",
                    "required": True
                }
            ]
        }
    }
    
    # Create voice form filler
    filler = VoiceFormFiller(sample_schema)
    
    # Fill form with voice
    filler.fill_form_with_voice()
    
    # Get filled schema
    filled_schema = filler.get_filled_schema()
    print(f"\nFinal filled form data: {json.dumps(filled_schema, indent=2)}")

if __name__ == "__main__":
    main()
