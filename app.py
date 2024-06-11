import base64
import json

import dotenv
import gradio as gr
import pandas as pd
from openai import OpenAI

dotenv.load_dotenv()
client = OpenAI()


def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def fillForm(identityDocument, tenthMarksheet, twelfthMarksheet):
    if identityDocument != None and tenthMarksheet != None and twelfthMarksheet != None:
        json_response = []
        df_return = []
        docs = [identityDocument, tenthMarksheet, twelfthMarksheet]
        prompts = [
            "You are a Information Extractor AI. I need you to extract the following information from the images and provide it to me in a JSON format. \
                    Information to be extracted: \
                    Full Name, \
                    Father's Name, \
                    Mother's Name, \
                    Date of Birth, \
                    Address, \
                    Aadhar Number, \
                    Gender",
            f"You are a Information Extractor AI. I need you to extract the following information from the images and provide it to me in a JSON format. \
                    Information to be extracted: \
                        Seat Number \
                        Year of Passing \
                        Subject Names with score in format: subjectname: score \
                        Total Marks obtained \
                        Percentage",
            "You are a Information Extractor AI. I need you to extract the following information from the images and provide it to me in a JSON format. \
                    Information to be extracted: \
                        Stream \
                        Seat Number \
                        Year of Passing \
                        Subject Names with score in format: subjectname: score \
                        Total Marks obtained \
                        Percentage",
        ]
        for i in range(len(docs)):
            response = client.chat.completions.create(
                model="gpt-4o",
                response_format={"type": "json_object"},
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompts[i],
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{encode_image(docs[i])}",
                                },
                            },
                        ],
                    }
                ],
            )
            json_response.append(response.choices[0].message.content.replace("\n", ""))
        print(json_response)
        for i in json_response:
            json_obj = json.loads(i)
            df = pd.json_normalize(json_obj)
            for i in df.columns:
                df = df.rename(columns={i: i.strip().replace("Subjects.", "")})
            df = df.melt(var_name="Field", value_name="Value")
            df_return.append(df)
        return df_return
    else:
        return [None, None, None]


inputs = [
    gr.File(label="identityDocument"),
    gr.File(label="tenthMarksheet"),
    gr.File(label="twelfthMarksheet"),
]
# outputs = ["json", "json", "json"]
outputs = ["dataframe", "dataframe", "dataframe"]

demo = gr.Interface(
    fillForm,
    inputs,
    outputs=outputs,
    live=True,
    allow_flagging="never",
)

demo.launch()
