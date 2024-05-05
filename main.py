from functools import lru_cache
from fastapi import FastAPI, UploadFile
from pydantic import BaseModel
from pdf2image import convert_from_bytes
import io
from openai import OpenAI
import base64
from . import config
import json


app = FastAPI()

client = OpenAI()

with open("prompts.json", "r") as f:
    prompts = {}
    for key, value in json.load(f).items():
        new_key = tuple([k == "True" for k in key[1:-1].split(", ")])
        prompts[new_key] = value

@lru_cache
def get_settings():
    return config.Settings()


@app.get("/")
def root():
    return {"message": "Hello World"}

@app.post("/parse")
async def parse(file: UploadFile):
    
    try:
        # convert the pages to images
        pdf_bytes = file.file.read()

        images = convert_from_bytes(pdf_bytes)

        product_name_found, troubleshooting_page, page_offset = False, None, None

        troubleshooting_page = None

        def get_curr_prompt():

            key = (product_name_found or troubleshooting_page is not None, troubleshooting_page is not None, page_offset is not None)
            return prompts[key]

        info = {'troubleshooting': {}}

        for i, image in enumerate(images):
            if (troubleshooting_page is not None) and (page_offset is not None):
                page = i - page_offset
                if page < troubleshooting_page:
                    continue
                else:
                    sections = [x for x in info['toc'].keys() if x > troubleshooting_page]
                    sections.sort()
                    if page >= sections[0] and page > troubleshooting_page:
                        break
            image_bytes = io.BytesIO()
            image.save(image_bytes, format='JPEG')

            base64_image = base64.b64encode(image_bytes.getvalue()).decode('utf-8')
            
            response = client.chat.completions.create(
                model="gpt-4-turbo",
                response_format={ "type": "json_object" },
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant designed to output JSON."
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text", "text": get_curr_prompt()
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                },
                            },
                        ],
                    }
                ],
                max_tokens=1000,
            )
            try:
                json_response = json.loads(response.choices[0].message.content)
            except:
                json_response = {}

            if 'page' in json_response:
                page_offset = i - int(json_response['page'])

            json_response.pop('page', None)

            if 'product' in json_response:
                product_name_found = True
                info['product'] = json_response['product']
                if 'model' in json_response:
                    info['model'] = json_response['model']
            elif 'TROUBLESHOOTING_PAGE' in json_response:
                troubleshooting_page = int(json_response['TROUBLESHOOTING_PAGE'])
                info['toc'] = {int(k): v for k, v in json_response.items() if k.isnumeric()}
            elif 'troubleshooting' in json_response and json_response['troubleshooting'] != {}:
                if page_offset is not None:
                    page = i - page_offset
                else:
                    page = -1

                info['troubleshooting'][page] = json_response['troubleshooting']
            
        return info['troubleshooting']
    except Exception as e:
        print(e)
    return {"filename": file.filename}