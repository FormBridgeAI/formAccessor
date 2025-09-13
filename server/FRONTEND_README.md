# Voice-Enabled Form Filling - Web Frontend

A modern web interface for the voice-enabled form filling system that allows users to upload documents and fill them out using voice or text input.

## Features

- �� **Voice Input**: Use your microphone to fill out forms with speech
- 📄 **Document Support**: Upload PDF, PNG, JPG, and other image formats
- 🤖 **AI-Powered**: Uses Azure Document Intelligence and OpenAI for form recognition
- 📱 **Responsive Design**: Works on desktop and mobile devices
- ⚡ **Real-time Processing**: Live form filling with instant feedback

## Quick Start

### 1. Start the Web Application

```bash
python run_app.py
```

This will:
- Check your environment setup
- Install required dependencies
- Start the web server on http://localhost:5000

### 2. Open in Browser

Navigate to: **http://localhost:5000**

### 3. Use the Application

1. **Select Document**: Choose from available documents in the sample_data folder
2. **Process**: Click "Process Document" to extract form fields using AI
3. **Fill Form**: Use voice input or type to fill out the form fields
4. **Complete**: Click "Complete Form" to generate the final result

## Voice Input Usage

1. Click the "🎤 Use Voice Input" button
2. Allow microphone access when prompted
3. Speak your answer clearly
4. The system will automatically transcribe and fill the field

## Supported Document Types

- PDF files (.pdf)
- Image files (.png, .jpg, .jpeg, .tiff, .bmp)

## API Endpoints

The frontend communicates with these API endpoints:

- `GET /api/documents` - List available documents
- `POST /api/process` - Process a selected document
- `GET /api/status` - Get processing status
- `GET /api/fields` - Get form fields
- `POST /api/fill-field` - Fill a specific field
- `GET /api/complete` - Complete the form
- `GET /api/reset` - Reset the session

## Browser Compatibility

- Chrome (recommended for voice input)
- Firefox
- Safari
- Edge

**Note**: Voice input requires a modern browser with Web Speech API support.

## Troubleshooting

### Voice Input Not Working
- Ensure you're using a supported browser (Chrome recommended)
- Check that microphone permissions are granted
- Try refreshing the page

### Document Processing Fails
- Verify your API keys are correctly set in the .env file
- Check that the document is in a supported format
- Ensure the document contains readable text

### Server Won't Start
- Make sure you're in the virtual environment
- Check that all dependencies are installed
- Verify your .env file has the required API keys

## Development

To run in development mode:

```bash
python app.py
```

This starts the Flask development server with auto-reload enabled.

## File Structure

```
server/
├── app.py                 # Flask web application
├── run_app.py            # Startup script
├── voice_workflow.py     # Core workflow logic
├── voice_form_filler.py  # Voice processing
├── templates/
│   └── index.html        # Main web interface
├── static/               # Static assets (CSS, JS)
└── requirements.txt      # Python dependencies
```

## Environment Variables

Make sure your `.env` file contains:

```
OPENAI_API_KEY=your_openai_key
AZURE_KEY=your_azure_key
DEEPGRAM_API_KEY=your_deepgram_key
```

## Support

If you encounter any issues:

1. Check the browser console for JavaScript errors
2. Check the terminal for Python errors
3. Verify all API keys are correct
4. Ensure all dependencies are installed

Enjoy using the Voice-Enabled Form Filling system! 🎉
