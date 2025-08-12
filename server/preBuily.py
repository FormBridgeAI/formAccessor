import os
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceAdministrationClient

endpoint = 'https://aiformfilling-doc-ai.cognitiveservices.azure.com/'
key = 'CTVcKut0gFiwLBPWB5dvHfJg33Lf3OCnPLmwHl0HmmYnrT1mh0pdJQQJ99BGACYeBjFXJ3w3AAALACOGVNkh'

client = DocumentIntelligenceAdministrationClient(endpoint=endpoint, credential=AzureKeyCredential(key))

responses = {}

def callback(response):
    responses["status_code"] = response.http_response.status_code
    responses["response_body"] = response.http_response.json()

client.get_resource_details(raw_response_hook=callback)

print(f"Response status code is: {responses['status_code']}")
response_body = responses["response_body"]
print(
    f"Our resource has {response_body['customDocumentModels']['count']} custom models, "
    f"and we can have at most {response_body['customDocumentModels']['limit']} custom models."
    f"The quota limit for custom neural document models is {response_body['customNeuralDocumentModelBuilds']['quota']} and the resource has"
    f"used {response_body['customNeuralDocumentModelBuilds']['used']}. The resource quota will reset on {response_body['customNeuralDocumentModelBuilds']['quotaResetDateTime']}"
)