from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential
from openai import OpenAI
import json
import os
import re
from dotenv import load_dotenv

load_dotenv()
Client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Azure setup
endpoint = 'https://aiformfilling-doc-ai.cognitiveservices.azure.com/'
key = 'CTVcKut0gFiwLBPWB5dvHfJg33Lf3OCnPLmwHl0HmmYnrT1mh0pdJQQJ99BGACYeBjFXJ3w3AAALACOGVNkh'
client = DocumentIntelligenceClient(endpoint=endpoint, credential=AzureKeyCredential(key))

def extract_and_generate_schema(file_path):
    # Analyze document with Azure
    with open(file_path, "rb") as f:
        poller = client.begin_analyze_document(
            model_id="prebuilt-layout",
            body=f,
            content_type="image/jpeg"
        )
    result = poller.result()

    # Collect all lines from the document
    lines = []
    for page in result.pages:
        for line in page.lines:
            lines.append(line.content)

    # Prompt OpenAI to create a schema from the lines
    messages = [
        {
            'role': 'system',
            'content': (
                "You are an assistant that takes lines from a scanned form and reconstructs a JSON form schema. "
                "Return ONLY valid JSON in your response. For each section of the form, have a value section that will be filled in later. "
                "Make sure to adjust for questions that require select-if questions and for questions that have conditions. "
                "Each field should have these sections: type, required, options, accessibility, and value."
            )
        },
        {
            'role': 'user',
            'content': (
                "Here are the lines from the form:\n" +
                "\n".join(lines) +
                "\nPlease return ONLY valid JSON in the schema format."
            )
        }
    ]

    response = Client.chat.completions.create(
        model='gpt-4-1106-preview',
        messages=messages,
        max_tokens=2048,
        temperature=0
    )
    answer = response.choices[0].message.content

    
    if answer.strip().startswith("```"):
        answer = re.sub(r"^```[a-zA-Z]*\n?", "", answer.strip())
        answer = re.sub(r"\n?```$", "", answer.strip())

    print("Raw OpenAI output:")
    print(repr(answer))  # Shows if it's empty or not JSON

    try:
        structured = json.loads(answer)
        return structured
    except Exception as e:
        print("Could not parse model output as JSON. Raw output:")
        print(answer)
        print("Error:", e)
        return None

if __name__ == "__main__":
    file_path = "/Users/asfawy/jsonTest/free-printable-w-9-forms-2018-form-resume-examples-xjkenpq3rk-free-printable-w9-2749523178.jpg"
    schema = extract_and_generate_schema(file_path)
    if schema:
        with open(os.path.join("server", "filled.json"), "w") as f:
            json.dump(schema, f, indent=2)
        print("Structured schema saved to server/filled.json")


