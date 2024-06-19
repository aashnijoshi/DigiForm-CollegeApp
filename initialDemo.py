import base64
import requests
import openai
import json
from openai import OpenAI

# OpenAI API Key
api_key = "sk-proj-GdBZvnCkWYMYzJ5s2hKvT3BlbkFJSNvdQkUJpIa4Z89ndvpx"

# Function to encode the image
def encode_image(image_path):
  with open(image_path, "rb") as image_file:
    return base64.b64encode(image_file.read()).decode('utf-8')

# Path to your image
image_path_aadhar = "/Users/aashnijoshi/Downloads/aadhar-1.jpeg"
image_path_grades = "/Users/aashnijoshi/Downloads/marksheet.jpeg"
image_path_collegeform = "/Users/aashnijoshi/Downloads/ADMISSIONFORM.jpg"
image_path_10thmarksheet =  "/Users/aashnijoshi/Downloads/10marksheet.PNG"
image_path_resume = "/Users/aashnijoshi/Downloads/aashniresume.PNG"
image_path_passport = "/Users/aashnijoshi/Downloads/PASSPORTT.jpg"
image_path_collegeminreqs = "/Users/aashnijoshi/Downloads/collegeminreqs.png"


# Getting the base64 string
base64_image_aadhar = encode_image(image_path_aadhar)
base64_image_grades = encode_image(image_path_grades)
base64_image_collegeform = encode_image(image_path_collegeform)
base64_image_10thmarksheet = encode_image(image_path_10thmarksheet)
base64_image_resume = encode_image(image_path_resume)
base64_image_passport = encode_image(image_path_passport)
base64_image_collegeminreqs = encode_image(image_path_collegeminreqs)

headers = {
  "Content-Type": "application/json",
  "Authorization": f"Bearer {api_key}"
}

payload_1 = {
  "model": "gpt-4o",
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "these are the documents of Aashni. can u list all the info given here about this person?"
        },
        {
          "type": "image_url",
          "image_url": {
            "url": f"data:image/jpeg;base64,{base64_image_aadhar}"
          }
        },

        {
          "type": "image_url",
          "image_url": {
            "url": f"data:image/jpeg;base64,{base64_image_passport}"
        },


        }
      ]
    },

  ],
  "max_tokens": 300
}

response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload_1)


#print(response.json()['choices'][0]['message']['content'])
#ans1 is analysis of aadhar and passport
response_json = response.json()
#print(response_json)

ans1 = response.json()['choices'][0]['message']['content']

payload_2 = {
  "model": "gpt-4o",
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "these are the grades of Aashni. it has each subject she took with the score she got in that subject. can u list all the scores of each specific subject, average of all her scores and her year of passing both 10th and 12th grade?"
        },
        {
          "type": "image_url",
          "image_url": {
            "url": f"data:image/jpeg;base64,{base64_image_10thmarksheet}"
          }
        },

        {
          "type": "image_url",
          "image_url": {
            "url": f"data:image/jpeg;base64,{base64_image_grades}"
          },

        }
      ]
    },

  ],
  "max_tokens": 3000
}

response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload_2)

#print(response.json()['choices'][0]['message']['content'])
ans2 = response.json()['choices'][0]['message']['content']
#print(ans2)
'''
payload_2_5_1 = {
    "model": "gpt-4o",
    "messages": [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "This image contains the minimum score requirement for someone to be admitted into that specific university and also the specific subjec fields that university is known to have a good course program for. Write out everything the image mentions."
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image_collegeminreqs}"
                    }
                }

            ]
        },

    ],
    "max_tokens": 700
}

response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload_2_5_1)
ans2_5_1 = response.json()['choices'][0]['message']['content']
#print(ans2_5_1)
'''



#print(ans1+ans2)

payload = {
  "model": "gpt-4o",
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "these are a list of extracurricular activites aashni participated in. can you list them out?"
        },
        {
          "type": "image_url",
          "image_url": {
            "url": f"data:image/jpeg;base64,{base64_image_resume}"
          }
        },

      ]
    }
  ],
  "max_tokens": 300
}

response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
#print(response.json()['choices'][0]['message']['content'])
ans3 = response.json()['choices'][0]['message']['content']

payload = {
  "model": "gpt-4o",
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text" : ans1+ans2,
        },
        {
          "type": "text",
          "text": "this is a college admissions form asking for various student details. fill out the form based off of the previous information. write out every single thing the form asks for and if you can't answer a specific field you can leave it blank. also, if no category certificate is attached then write 'General' in the category section. present this information in the form of a table",
        },
        {
          "type": "image_url",
          "image_url": {
            "url": f"data:image/jpeg;base64,{base64_image_collegeform}"
          }
        },

      ]
    }
  ],
  "max_tokens": 3000
}

response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
print(response.json()['choices'][0]['message']['content'])

messages = []
system_msg = "You are a college counsellor for indian universities. Suggest schools to apply to for undergraduate education based off of how much the child has scored in their exams and the minimum score requirements for various colleges. Also ask the student about their interests and act as a brilliant career counsellor."
messages.append({"role": "system", "content": system_msg})
messages.append({"role": "system", "content": ans2})
#messages.append({"role": "system", "content": ans2_5_1})
openai.api_key = "sk-proj-GdBZvnCkWYMYzJ5s2hKvT3BlbkFJSNvdQkUJpIa4Z89ndvpx"
print("Hi! I am your college counsellor. I'll be recommending colleges to you based off of your grades and interests. Tell me about your interests and hobbies!")

while input != "quit()":
    message = input()
    messages.append({"role": "user", "content": message})
    response_2_5_1 = openai.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        max_tokens=250
    )
    reply = response_2_5_1.json()
    messages.append({"role": "assistant", "content": reply})
    reply_json = json.loads(reply)
    print(reply_json['choices'][0]['message']['content'])








  
