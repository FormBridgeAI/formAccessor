require('dotenv').config({path:"server/.env"})
const dotenv = require('dotenv')
const OpenAI = require('openai')
const openai = new OpenAI({
    apiKey:process.env.OPENAI_API_KEY
})
const jsonSchema = {
  "formTitle": "Medical Intake Form",
  "formId": "form_001",
  "fields": [
    {
      "id": "field_01",
      "label": "Full Name",
      "type": "text",
      "value": null,
      "required": true,
      "boundingBox": {
        "x": 100,
        "y": 200,
        "width": 300,
        "height": 30
      },
      "grouping": {
        "visualGroup": "Personal Info",
        "logicalRule": null
      },
      "accessibility": {
        "screenReaderHint": "Enter your full legal name",
        "tabOrder": 1
      }
    },
    {
      "id": "field_02",
      "label": "Date of Birth",
      "type": "date",
      "value": null,
      "required": true,
      "boundingBox": {
        "x": 100,
        "y": 250,
        "width": 200,
        "height": 30
      },
      "grouping": {
        "visualGroup": "Personal Info",
        "logicalRule": null
      },
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
      "value": null,
      "required": false,
      "boundingBox": {
        "x": 100,
        "y": 300,
        "width": 300,
        "height": 60
      },
      "grouping": {
        "visualGroup": "Demographics",
        "logicalRule": "selectOne"
      },
      "accessibility": {
        "screenReaderHint": "Select one Race option",
        "options": [
    "Asian",
    "Black or African American",
    "Hispanic or Latino",
    "Native American or Alaska Native",
    "Native Hawaiian or Pacific Islander",
    "White",
    "Two or More Races",
    "Prefer not to say"
  ],
  "value":null,
  "required":false,
        "tabOrder": 3
      }
    }]
}
const messages =[{ role: 'user', content: `You are a helpful assistant guiding someone through filling out a digital form. Ask only one clear and friendly question at a time based on the fields in this JSON schema. Prioritize required fields first, and wait for user input before continuing.

when finshed with the form send it back to the user completely filled out in a neat form Here is the JSON schema:

${JSON.stringify(jsonSchema, null, 2)}` }]
  

async function getResponse(){
    try {
    const response = await openai.chat.completions.create({
      model: 'gpt-4',
      messages : messages,
    });


    const repy = response.choices[0].message.content
    console.log(`BOT:${repy}`)
    messages.push({role:'assistant',content:repy})
    messages.push({role:'user',content:"Youdahe Asfaw"})
    const followUp = await openai.chat.completions.create({
        model: 'gpt-4',
        messages:messages
    })

    const DOBreply = followUp.choices[0].message.content
    console.log(`BOT:${DOBreply}`)
    messages.push({role:'assistant',content:DOBreply})
    messages.push({role:'user',content:"04/29/2006"})
    const DOB = await openai.chat.completions.create({model:'gpt-4',messages:messages})
    console.log(DOB.choices[0].message.content)

    const gender = await openai.chat.completions.create({model:'gpt-4',messages:messages})

    const GenderReply = gender.choices[0].message.content
    console.log(`BOT:${GenderReply}`)
    messages.push({role:'assistant',content:GenderReply})
    messages.push({role:'user',content:"Male"})
    const genderResponse = await openai.chat.completions.create({model:'gpt-4',messages:messages})
    console.log(genderResponse.choices[0].message.content)

   // const race = await.openai.chat.completions
    
  } catch (error) {
    console.error("Error getting response:", error);
  }
}


getResponse()