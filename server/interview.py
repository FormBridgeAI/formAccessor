import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from practice import extract_and_generate_schema
import time

load_dotenv("../.env")
Client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

file_path = "/Users/asfawy/Downloads/free-printable-w-9-forms-2018-form-resume-examples-xjkenpq3rk-free-printable-w9-2749523178 (2).jpg"
schema = extract_and_generate_schema(file_path)
if not schema:
    print("Could not extract schema. Please check the previous output for errors.")
    exit(1)

# Flatten fields if needed
fields = []
if "fields" in schema:
    fields = schema["fields"]
elif "sections" in schema:
    for section in schema["sections"]:
        fields.extend(section.get("fields", []))

# Only required fields
required_fields = [f for f in fields if f.get('required')]

messages = [{
    'role': 'system',
    'content': (
        "You are a helpful assistant guiding a user through filling out a digital form. "
        "Ask one required field at a time, wait for the user's answer, then ask the next. "
        "When all required fields are filled, respond ONLY with the completed schema in valid JSON format."
    )
}]

for field in required_fields:
    # Let OpenAI generate the question for this field
    field_prompt = (
        f"Ask the user for the following field:\n"
        f"Label: {field.get('label','')}\n"
        f"Type: {field.get('type','')}\n"
        f"Options: {', '.join(field.get('options', [])) if field.get('options') else 'N/A'}\n"
        f"Accessibility: {field.get('accessibility','')}\n"
        f"Respond with only the question."
    )
    messages.append({'role': 'user', 'content': field_prompt})
    ai_question = Client.chat.completions.create(
        model='gpt-4-1106-preview',
        messages=messages[-6:],  # Keep context short
        max_tokens=100,
        temperature=0
    ).choices[0].message.content
    print(f"AI: {ai_question}")
    user_input = input("You: ")
    messages.append({'role': 'assistant', 'content': ai_question})
    messages.append({'role': 'user', 'content': user_input})
    field['value'] = user_input

# All required fields are filled, print the completed schema
print("\n--- Filled Schema ---")
print(json.dumps(schema, indent=2))
