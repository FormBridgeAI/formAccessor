♿ AI-Powered Accessibility Toolkit

This repository contains the research prototype developed during my time as an AI & Accessibility Research Assistant. The project focuses on improving digital accessibility for users with visual and physical impairments using AI-powered tools and human-centered design.

## Project Overview

The AI-Powered Accessibility Toolkit is designed to make complex forms and documents more accessible by automatically extracting their structure and generating filled versions with precise positioning. This tool is particularly valuable for users who may have difficulty reading or filling out traditional paper forms.

## 🚀 Key Features

### Intelligent Form Processing

- **Azure Document Intelligence Integration**: Uses Microsoft's advanced OCR and document analysis to extract form structure
- **AI-Powered Field Recognition**: Leverages OpenAI's language models to intelligently identify and map form fields
- **Precise Coordinate Extraction**: Automatically determines exact positioning for form fields using computer vision

### Accessibility-Focused Output

- **High-Contrast Form Generation**: Creates filled forms with clear, readable text positioning
- **Smart Field Mapping**: Automatically places user input in the correct locations on forms
- **Multi-Format Support**: Works with various form types including tax forms, applications, and legal documents

### Interactive Workflow

- **Guided Form Filling**: Step-by-step process for completing forms with user input
- **Schema Generation**: Automatically creates structured representations of form layouts
- **Real-Time Processing**: Immediate feedback and validation during form completion

## 🛠️ Technical Architecture

The toolkit consists of several core components:

- **`enhanced_coordinate_extractor.py`**: Azure Document Intelligence integration for precise field positioning
- **`image_generator.py`**: PIL-based image generation with intelligent field placement
- **`real_workflow.py`**: Main workflow orchestrator combining all components
- **`practice.py`**: Schema extraction and form analysis utilities
- **`interview.py`**: Interactive form filling interface

## Setup & Usage

### Prerequisites

- Python 3.7+
- Azure Document Intelligence credentials
- OpenAI API key
- Required Python packages (see requirements.txt)

### Quick Start

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Configure your Azure and OpenAI credentials
4. Run the main workflow: `python server/real_workflow.py`

## Use Cases

- **Tax Forms**: Automatically fill W-9, 1040, and other tax documents
- **Legal Documents**: Process contracts, applications, and legal forms
- **Accessibility Services**: Help users with visual impairments complete forms independently
- **Document Automation**: Streamline repetitive form-filling tasks

## Sample Output

The toolkit includes sample data demonstrating the transformation from blank forms to completed, accessible versions. Check the `sample_data/` directory for examples of input and output forms.

## Research Context

This prototype was developed as part of ongoing research into AI-assisted accessibility tools. The project explores how computer vision, natural language processing, and intelligent positioning can work together to create more inclusive digital experiences.

## Contributing

This is a research prototype, but contributions and feedback are welcome. Please feel free to open issues or submit pull requests for improvements.

## License

[Gustavus Adolphus College]

---

_Developed as part of AI & Accessibility Research at [Gustavus!]_
