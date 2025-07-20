import os
from openai import OpenAI
import json
from dotenv import load_dotenv
from practice import extract_and_generate_schema

load_dotenv()
Client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

file_path = "/Users/asfawy/jsonTest/free-printable-w-9-forms-2018-form-resume-examples-xjkenpq3rk-free-printable-w9-2749523178.jpg"
schema = extract_and_generate_schema(file_path)
if not schema:
    print("Could not extract schema. Please check the previous output for errors.")
    exit(1)

# Find the fields array (works for both flat and sectioned schemas)
fields = []
if "fields" in schema:
    fields = schema["fields"]
elif "sections" in schema:
    for section in schema["sections"]:
        fields.extend(section.get("fields", []))

# Interview loop: prompt user for each field and fill in the value
for field in fields:
    prompt = f"Please provide your {field.get('label', 'field')}"
    if field.get('type'):
        prompt += f" (Type: {field['type']})"
    if field.get('required'):
        prompt += " [Required]"
    if field.get('options'):
        prompt += f" Options: {', '.join(field['options'])}"
    if field.get('accessibility'):
        prompt += f" Hint: {field['accessibility']}"
    user_input = input(prompt + "\n")
    field['value'] = user_input

# Print the filled schema
print("\n--- Filled Schema ---")
print(json.dumps(schema, indent=2))

with open("server/filled_final.json", "w") as f:
    json.dump(schema, f, indent=2)
