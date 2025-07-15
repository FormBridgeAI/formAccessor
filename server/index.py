import os
from sys import path
from openai import OpenAI
import json
from dotenv import load_dotenv
from sample import mock_schemas
load_dotenv()


json_schema = mock_schemas[1]
Client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def scheme_response(schema):
    messages = [{
        'role':'system',
        'content':"You are a helpful assistant guiding a user through filling out a digital form. Ask one question at a time, based on the schema fields."
    }]
    for field in schema['fields']:
        prompt = f"Please Provide your {field['label']}"
        if field.get('type'):
            prompt += f"Type : {field['type']}"
        if field.get('required'):
            prompt += 'This is required'
        if field.get('options'):
            prompt += f"These are the options {",".join(field['options'])}"
        if field.get('accessibility',{}).get('screenReaderHint'):
            prompt += f"Hint: {field['accessibility']['screenReaderHint']}"
        
        messages.append({"role":"assistant",'content':prompt})
        userInput = input(prompt + "\n")
        messages.append({'role':'user','content':userInput})

        response = Client.chat.completions.create(
            model='gpt-4.1',
            messages=messages
        )
        print('BOT', response.choices[0].message.content)
        sum_prompt = (
            F"Here is the json schema {json_schema} i want you to fill the value keys with the information obtained from the inputs of the users"
        )
        messages.append({'role':'user','content':sum_prompt})
        summary = Client.chat.completions.create(
            model='gpt-4.1',
            messages=messages
        )
        print("\n--- Completed Form ---")
        print(summary.choices[0].message.content)
# needs work with making it look better and overall not spitting back the info everytime
if __name__ == "__main__":
    scheme_response(json_schema)