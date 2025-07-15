mock_schemas = [
    {
        "formTitle": "Medical Intake Form",
        "formId": "form_001",
        "fields": [
            {
                "id": "field_01",
                "label": "Full Name",
                "type": "text",
                "required": True,
                "value": None,
                "boundingBox": {"x": 100, "y": 200, "width": 300, "height": 30},
                "grouping": {"visualGroup": "Personal Info", "logicalRule": None},
                "accessibility": {
                    "screenReaderHint": "Enter your full legal name",
                    "tabOrder": 1
                }
            },
            {
                "id": "field_02",
                "label": "Date of Birth",
                "type": "date",
                "required": True,
                "value": None,
                "boundingBox": {"x": 100, "y": 250, "width": 200, "height": 30},
                "grouping": {"visualGroup": "Personal Info", "logicalRule": None},
                "accessibility": {
                    "screenReaderHint": "Enter date in MM/DD/YYYY format",
                    "tabOrder": 2
                }
            },
            {
                "id": "field_03",
                "label": "Gender",
                "type": "radio",
                "options": ["Male", "Female", "Other"],
                "required": False,
                "value": None,
                "boundingBox": {"x": 100, "y": 300, "width": 300, "height": 60},
                "grouping": {"visualGroup": "Demographics", "logicalRule": "selectOne"},
                "accessibility": {
                    "screenReaderHint": "Select your gender",
                    "tabOrder": 3
                }
            },
            {
                "id": "field_04",
                "label": "Race",
                "type": "dropdown",
                "options": [
                    "Asian", "Black or African American", "Hispanic or Latino",
                    "Native American or Alaska Native", "Native Hawaiian or Pacific Islander",
                    "White", "Other", "Prefer not to say"
                ],
                "required": False,
                "value": None,
                "boundingBox": {"x": 100, "y": 370, "width": 300, "height": 30},
                "grouping": {"visualGroup": "Demographics", "logicalRule": None},
                "accessibility": {
                    "screenReaderHint": "Select your race or ethnicity",
                    "tabOrder": 4
                }
            },
            {
                "id": "field_05",
                "label": "Phone Number",
                "type": "tel",
                "required": True,
                "value": None,
                "boundingBox": {"x": 100, "y": 410, "width": 200, "height": 30},
                "grouping": {"visualGroup": "Contact Info", "logicalRule": None},
                "accessibility": {
                    "screenReaderHint": "Enter your phone number including area code",
                    "tabOrder": 5
                }
            },
            {
                "id": "field_06",
                "label": "Email Address",
                "type": "email",
                "required": True,
                "value": None,
                "boundingBox": {"x": 100, "y": 450, "width": 250, "height": 30},
                "grouping": {"visualGroup": "Contact Info", "logicalRule": None},
                "accessibility": {
                    "screenReaderHint": "Enter a valid email address",
                    "tabOrder": 6
                }
            },
            {
                "id": "field_07",
                "label": "Primary Care Physician",
                "type": "text",
                "required": False,
                "value": None,
                "boundingBox": {"x": 100, "y": 490, "width": 300, "height": 30},
                "grouping": {"visualGroup": "Medical Info", "logicalRule": None},
                "accessibility": {
                    "screenReaderHint": "Enter the name of your primary care physician",
                    "tabOrder": 7
                }
            },
            {
                "id": "field_08",
                "label": "Insurance Provider",
                "type": "text",
                "required": False,
                "value": None,
                "boundingBox": {"x": 100, "y": 530, "width": 300, "height": 30},
                "grouping": {"visualGroup": "Medical Info", "logicalRule": None},
                "accessibility": {
                    "screenReaderHint": "Enter your insurance provider",
                    "tabOrder": 8
                }
            },
            {
                "id": "field_09",
                "label": "Policy Number",
                "type": "text",
                "required": False,
                "value": None,
                "boundingBox": {"x": 100, "y": 570, "width": 200, "height": 30},
                "grouping": {"visualGroup": "Medical Info", "logicalRule": None},
                "accessibility": {
                    "screenReaderHint": "Enter your insurance policy number",
                    "tabOrder": 9
                }
            },
            {
                "id": "field_10",
                "label": "Allergies",
                "type": "textarea",
                "required": False,
                "value": None,
                "boundingBox": {"x": 100, "y": 610, "width": 400, "height": 60},
                "grouping": {"visualGroup": "Medical Info", "logicalRule": None},
                "accessibility": {
                    "screenReaderHint": "List any allergies you have",
                    "tabOrder": 10
                }
            },
            {
                "id": "field_11",
                "label": "Current Medications",
                "type": "textarea",
                "required": False,
                "value": None,
                "boundingBox": {"x": 100, "y": 680, "width": 400, "height": 60},
                "grouping": {"visualGroup": "Medical Info", "logicalRule": None},
                "accessibility": {
                    "screenReaderHint": "List any medications you are currently taking",
                    "tabOrder": 11
                }
            },
            {
                "id": "field_12",
                "label": "Emergency Contact Name",
                "type": "text",
                "required": True,
                "value": None,
                "boundingBox": {"x": 100, "y": 750, "width": 300, "height": 30},
                "grouping": {"visualGroup": "Emergency Contact", "logicalRule": None},
                "accessibility": {
                    "screenReaderHint": "Enter the name of your emergency contact",
                    "tabOrder": 12
                }
            },
            {
                "id": "field_13",
                "label": "Emergency Contact Phone",
                "type": "tel",
                "required": True,
                "value": None,
                "boundingBox": {"x": 100, "y": 790, "width": 200, "height": 30},
                "grouping": {"visualGroup": "Emergency Contact", "logicalRule": None},
                "accessibility": {
                    "screenReaderHint": "Enter the phone number of your emergency contact",
                    "tabOrder": 13
                }
            },
            {
                "id": "field_14",
                "label": "Reason for Visit",
                "type": "textarea",
                "required": True,
                "value": None,
                "boundingBox": {"x": 100, "y": 830, "width": 400, "height": 60},
                "grouping": {"visualGroup": "Visit Info", "logicalRule": None},
                "accessibility": {
                    "screenReaderHint": "Briefly describe the reason for your visit",
                    "tabOrder": 14
                }
            },
            {
                "id": "field_15",
                "label": "Preferred Language",
                "type": "dropdown",
                "options": ["English", "Spanish", "Chinese", "French", "Other"],
                "required": False,
                "value": None,
                "boundingBox": {"x": 100, "y": 900, "width": 200, "height": 30},
                "grouping": {"visualGroup": "Personal Info", "logicalRule": None},
                "accessibility": {
                    "screenReaderHint": "Select your preferred language for communication",
                    "tabOrder": 15
                }
            }
        ]
    },
    {
        "formTitle": "Conference Registration",
        "formId": "form_002",
        "fields": [
            {
                "id": "field_01",
                "label": "Attendee Name",
                "type": "text",
                "required": True,
                "value": None,
                "boundingBox": {"x": 50, "y": 100, "width": 250, "height": 30},
                "grouping": {"visualGroup": "Attendee Info", "logicalRule": None},
                "accessibility": {
                    "screenReaderHint": "Enter your full name as it should appear on your badge",
                    "tabOrder": 1
                }
            },
            {
                "id": "field_02",
                "label": "Email Address",
                "type": "email",
                "required": True,
                "value": None,
                "boundingBox": {"x": 50, "y": 140, "width": 250, "height": 30},
                "grouping": {"visualGroup": "Attendee Info", "logicalRule": None},
                "accessibility": {
                    "screenReaderHint": "Enter a valid email address",
                    "tabOrder": 2
                }
            },
            {
                "id": "field_03",
                "label": "Ticket Type",
                "type": "dropdown",
                "options": ["Standard", "VIP", "Student"],
                "required": True,
                "value": None,
                "boundingBox": {"x": 50, "y": 180, "width": 200, "height": 30},
                "grouping": {"visualGroup": "Ticket Info", "logicalRule": None},
                "accessibility": {
                    "screenReaderHint": "Select your ticket type",
                    "tabOrder": 3
                }
            }
        ]
    },
    {
        "formTitle": "Job Application",
        "formId": "form_003",
        "fields": [
            {
                "id": "field_01",
                "label": "Applicant Name",
                "type": "text",
                "required": True,
                "value": None,
                "boundingBox": {"x": 20, "y": 50, "width": 300, "height": 30},
                "grouping": {"visualGroup": "Personal Details", "logicalRule": None},
                "accessibility": {
                    "screenReaderHint": "Enter your full legal name",
                    "tabOrder": 1
                }
            },
            {
                "id": "field_02",
                "label": "Phone Number",
                "type": "tel",
                "required": True,
                "value": None,
                "boundingBox": {"x": 20, "y": 90, "width": 200, "height": 30},
                "grouping": {"visualGroup": "Personal Details", "logicalRule": None},
                "accessibility": {
                    "screenReaderHint": "Enter your phone number including area code",
                    "tabOrder": 2
                }
            },
            {
                "id": "field_03",
                "label": "Resume",
                "type": "file",
                "required": True,
                "value": None,
                "boundingBox": {"x": 20, "y": 130, "width": 400, "height": 30},
                "grouping": {"visualGroup": "Documents", "logicalRule": None},
                "accessibility": {
                    "screenReaderHint": "Upload your resume in PDF format",
                    "tabOrder": 3
                }
            },
            {
                "id": "field_04",
                "label": "Position Applied For",
                "type": "dropdown",
                "options": ["Engineer", "Designer", "Manager"],
                "required": True,
                "value": None,
                "boundingBox": {"x": 20, "y": 170, "width": 250, "height": 30},
                "grouping": {"visualGroup": "Job Info", "logicalRule": None},
                "accessibility": {
                    "screenReaderHint": "Select the position you are applying for",
                    "tabOrder": 4
                }
            }
        ]
    }
]

# Example: export for use in other files
__all__ = ["mock_schemas"]