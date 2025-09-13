"""
Voice Agent Integration for Form Filling - Fixed Event Handlers
Integrates Deepgram Voice Agent API with the existing form filling workflow
"""

import os
import json
import time
import threading
import asyncio
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

from deepgram import (
    DeepgramClient,
    DeepgramClientOptions,
    AgentWebSocketEvents,
    AgentKeepAlive,
)
from deepgram.clients.agent.v1.websocket.options import SettingsOptions

# Load environment variables
load_dotenv("../.env")

class VoiceFormAgent:
    def __init__(self, form_schema: Dict[str, Any]):
        """
        Initialize the Voice Form Agent
        
        Args:
            form_schema: The extracted form schema from Azure Document Intelligence
        """
        self.form_schema = form_schema
        self.filled_fields = {}
        self.current_field_index = 0
        self.required_fields = []
        self.processing_complete = False
        self.audio_buffer = bytearray()
        self.file_counter = 0
        
        # Initialize Deepgram client
        self.api_key = os.getenv("DEEPGRAM_API_KEY")
        if not self.api_key:
            raise ValueError("DEEPGRAM_API_KEY environment variable is not set")
        
        config = DeepgramClientOptions(
            options={
                "keepalive": "true",
            },
        )
        self.deepgram = DeepgramClient(self.api_key, config)
        self.connection = self.deepgram.agent.websocket.v("1")
        
        # Extract required fields from schema
        self._extract_required_fields()
        
        # Setup event handlers
        self._setup_event_handlers()
    
    def _extract_required_fields(self):
        """Extract required fields from the form schema"""
        fields = self.form_schema.get('fields', [])
        if not fields and 'sections' in self.form_schema:
            for section in self.form_schema['sections']:
                fields.extend(section.get('fields', []))
        
        self.required_fields = [field for field in fields if field.get('required', False)]
        print(f"Found {len(self.required_fields)} required fields to fill")
    
    def _handle_conversation_text(self, conversation_text):
        """Handle conversation text to extract form field values"""
        text = conversation_text.content.lower()
        role = conversation_text.role
        
        print(f"Processing conversation: Role={role}, Content='{conversation_text.content}'")
        
        if role == "user" and self.current_field_index < len(self.required_fields):
            current_field = self.required_fields[self.current_field_index]
            field_label = current_field.get('label', '').lower()
            field_type = current_field.get('type', 'text')
            
            print(f"Processing field {self.current_field_index + 1}/{len(self.required_fields)}: {current_field['label']}")
            
            # Extract the actual value from the user's response
            user_value = conversation_text.content.strip()
            
            # Store the value
            self.filled_fields[current_field['label']] = user_value
            print(f"✅ Captured field '{current_field['label']}': '{user_value}'")
            
            # Move to next field
            self.current_field_index += 1
            
            # Check if we're done
            if self.current_field_index >= len(self.required_fields):
                print("🎉 All required fields have been filled!")
                self.processing_complete = True
            else:
                next_field = self.required_fields[self.current_field_index]
                print(f"Next field: {next_field['label']}")
    
    def _setup_event_handlers(self):
        """Setup Deepgram event handlers"""
        
        # Create wrapper functions that don't have conflicting parameter names
        def on_audio_data(data, **kwargs):
            self.audio_buffer.extend(data)
            print(f"Received audio data from agent: {len(data)} bytes")
        
        def on_agent_audio_done(agent_audio_done, **kwargs):
            print(f"AgentAudioDone event received")
            if len(self.audio_buffer) > 0:
                with open(f"voice_output-{self.file_counter}.wav", 'wb') as f:
                    f.write(self._create_wav_header())
                    f.write(self.audio_buffer)
                print(f"Created voice_output-{self.file_counter}.wav")
            self.audio_buffer = bytearray()
            self.file_counter += 1
        
        def on_conversation_text(conversation_text, **kwargs):
            print(f"Conversation Text: {conversation_text}")
            self._handle_conversation_text(conversation_text)
            with open("voice_chatlog.txt", 'a') as chatlog:
                chatlog.write(f"{json.dumps(conversation_text.__dict__)}\n")
        
        def on_welcome(welcome, **kwargs):
            print(f"Welcome message received: {welcome}")
            with open("voice_chatlog.txt", 'a') as chatlog:
                chatlog.write(f"Welcome message: {welcome}\n")
        
        def on_settings_applied(settings_applied, **kwargs):
            print(f"Settings applied: {settings_applied}")
            with open("voice_chatlog.txt", 'a') as chatlog:
                chatlog.write(f"Settings applied: {settings_applied}\n")
        
        def on_user_started_speaking(user_started_speaking, **kwargs):
            print(f"User Started Speaking: {user_started_speaking}")
            with open("voice_chatlog.txt", 'a') as chatlog:
                chatlog.write(f"User Started Speaking: {user_started_speaking}\n")
        
        def on_agent_thinking(agent_thinking, **kwargs):
            print(f"Agent Thinking: {agent_thinking}")
            with open("voice_chatlog.txt", 'a') as chatlog:
                chatlog.write(f"Agent Thinking: {agent_thinking}\n")
        
        def on_agent_started_speaking(agent_started_speaking, **kwargs):
            self.audio_buffer = bytearray()  # Reset buffer for new response
            print(f"Agent Started Speaking: {agent_started_speaking}")
            with open("voice_chatlog.txt", 'a') as chatlog:
                chatlog.write(f"Agent Started Speaking: {agent_started_speaking}\n")
        
        def on_close(close, **kwargs):
            print(f"Connection closed: {close}")
            with open("voice_chatlog.txt", 'a') as chatlog:
                chatlog.write(f"Connection closed: {close}\n")
        
        def on_error(error, **kwargs):
            print(f"Error: {error}")
            with open("voice_chatlog.txt", 'a') as chatlog:
                chatlog.write(f"Error: {error}\n")
        
        def on_unhandled(unhandled, **kwargs):
            print(f"Unhandled event: {unhandled}")
            with open("voice_chatlog.txt", 'a') as chatlog:
                chatlog.write(f"Unhandled event: {unhandled}\n")
        
        # Register handlers
        self.connection.on(AgentWebSocketEvents.AudioData, on_audio_data)
        self.connection.on(AgentWebSocketEvents.AgentAudioDone, on_agent_audio_done)
        self.connection.on(AgentWebSocketEvents.ConversationText, on_conversation_text)
        self.connection.on(AgentWebSocketEvents.Welcome, on_welcome)
        self.connection.on(AgentWebSocketEvents.SettingsApplied, on_settings_applied)
        self.connection.on(AgentWebSocketEvents.UserStartedSpeaking, on_user_started_speaking)
        self.connection.on(AgentWebSocketEvents.AgentThinking, on_agent_thinking)
        self.connection.on(AgentWebSocketEvents.AgentStartedSpeaking, on_agent_started_speaking)
        self.connection.on(AgentWebSocketEvents.Close, on_close)
        self.connection.on(AgentWebSocketEvents.Error, on_error)
        self.connection.on(AgentWebSocketEvents.Unhandled, on_unhandled)
        print("Voice agent event handlers registered")
    
    def _create_wav_header(self, sample_rate=24000, bits_per_sample=16, channels=1):
        """Create a WAV header with the specified parameters"""
        byte_rate = sample_rate * channels * (bits_per_sample // 8)
        block_align = channels * (bits_per_sample // 8)

        header = bytearray(44)
        # RIFF header
        header[0:4] = b'RIFF'
        header[4:8] = b'\x00\x00\x00\x00'  # File size (to be updated later)
        header[8:12] = b'WAVE'
        # fmt chunk
        header[12:16] = b'fmt '
        header[16:20] = b'\x10\x00\x00\x00'  # Subchunk1Size (16 for PCM)
        header[20:22] = b'\x01\x00'  # AudioFormat (1 for PCM)
        header[22:24] = channels.to_bytes(2, 'little')  # NumChannels
        header[24:28] = sample_rate.to_bytes(4, 'little')  # SampleRate
        header[28:32] = byte_rate.to_bytes(4, 'little')  # ByteRate
        header[32:34] = block_align.to_bytes(2, 'little')  # BlockAlign
        header[34:36] = bits_per_sample.to_bytes(2, 'little')  # BitsPerSample
        # data chunk
        header[36:40] = b'data'
        header[40:44] = b'\x00\x00\x00\x00'  # Subchunk2Size (to be updated later)

        return header
    
    def configure_agent(self):
        """Configure the Deepgram agent with form-specific settings"""
        # Load configuration from file
        with open('deepgram_config.json', 'r') as f:
            config = json.load(f)
        
        # Create settings options
        options = SettingsOptions()
        
        # Audio input configuration
        options.audio.input.encoding = config['audio']['input']['encoding']
        options.audio.input.sample_rate = config['audio']['input']['sample_rate']
        
        # Audio output configuration
        options.audio.output.encoding = config['audio']['output']['encoding']
        options.audio.output.sample_rate = config['audio']['output']['sample_rate']
        options.audio.output.container = config['audio']['output']['container']
        
        # Agent configuration
        options.agent.language = config['agent']['language']
        options.agent.listen.provider.type = config['agent']['listen']['provider']['type']
        options.agent.listen.provider.model = config['agent']['listen']['provider']['model']
        options.agent.think.provider.type = config['agent']['think']['provider']['type']
        options.agent.think.provider.model = config['agent']['think']['provider']['model']
        options.agent.think.prompt = config['agent']['think']['prompt']
        options.agent.speak.provider.type = config['agent']['speak']['provider']['type']
        options.agent.speak.provider.model = config['agent']['speak']['provider']['model']
        options.agent.greeting = config['agent']['greeting']
        
        return options
    
    def start_voice_session(self):
        """Start the voice agent session"""
        try:
            print("🎤 Starting Voice Form Filling Session...")
            
            # Configure the agent
            options = self.configure_agent()
            
            # Send Keep Alive messages
            def send_keep_alive():
                while True:
                    time.sleep(5)
                    print("Keep alive!")
                    self.connection.send(str(AgentKeepAlive()))

            # Start keep-alive in a separate thread
            keep_alive_thread = threading.Thread(target=send_keep_alive, daemon=True)
            keep_alive_thread.start()
            
            # Start the connection
            print("Starting WebSocket connection...")
            if not self.connection.start(options):
                print("Failed to start connection")
                return False
            print("WebSocket connection started successfully")
            
            return True
            
        except Exception as e:
            print(f"Error starting voice session: {str(e)}")
            return False
    
    def stop_voice_session(self):
        """Stop the voice agent session"""
        try:
            self.connection.finish()
            print("Voice session stopped")
        except Exception as e:
            print(f"Error stopping voice session: {str(e)}")
    
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
    """Example usage of the Voice Form Agent"""
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
    
    # Create voice agent
    agent = VoiceFormAgent(sample_schema)
    
    # Start voice session
    if agent.start_voice_session():
        print("Voice agent is ready! Speak to fill out the form.")
        print("Press Ctrl+C to stop...")
        
        try:
            # Keep the session running
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping voice session...")
            agent.stop_voice_session()
            
            # Get filled schema
            filled_schema = agent.get_filled_schema()
            print(f"\nFilled form data: {json.dumps(filled_schema, indent=2)}")
    else:
        print("Failed to start voice session")

if __name__ == "__main__":
    main()
