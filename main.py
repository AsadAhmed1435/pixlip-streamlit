import os
import random
import subprocess
import time
import requests
import streamlit as st
import json
from leonardo_api import Leonardo

from leonardo import process_image as process_image_leo

MIDJOURNEY_API_KEY = os.getenv("MID_JOURNEY_AUTH_TOKEN")
LEONARD_API_KEY = os.getenv("LEONARD_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
STABLE_DIFFUSION_API_KEY = os.getenv("STABLE_DIFFUSION_API_KEY")

leonardo = Leonardo(auth_token=LEONARD_API_KEY)
openai_key = OPENAI_API_KEY
stable_key = STABLE_DIFFUSION_API_KEY   

st.title("Welcome to PIXLIP AI!")
input_text = st.text_area("Please enter your prompt")
def post_image_request_midjourney(prompt: str):
    # Configuration for the POST request
    url = "https://api.imaginepro.ai/api/v1/midjourney/imagine"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {MIDJOURNEY_API_KEY}"
    }
    data = {
        "prompt": f"""{prompt}"""
    }
    # Making the POST request
    response = requests.post(url, json=data, headers=headers)
    message_id = None
    # Handling the response
    if response.status_code == 200:
        print(response.json())
        message_id = response.json()['messageId']
    else:
        print("Failed to fetch data:", response.status_code)
    return message_id
# The below function is not used as the key is not valid
def post_image_request_stable_diffusion(image_url:str, prompt: str):
    url = "https://stablediffusionapi.com/api/v3/img2img"
    payload = json.dumps({
        "key": stable_key,
        "prompt": prompt,
        "negative_prompt": None,
        "init_image": image_url,
        "width": "512",
        "height": "512",
        "samples": "1",
        "num_inference_steps": "30",
        "safety_checker": "no",
        "enhance_prompt": "yes",
        "guidance_scale": 12,
        "strength": 0.3,
        "seed": None,
        "base64": "no",
        "webhook": None,
        "track_id": None
    })
    headers = {
    'Content-Type': 'application/json'
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    response = json.loads(response.text)
    image_id = response['id']
    return image_id
def post_image_request_dalle(prompt: str):
    data = json.dumps({
    "model": "dall-e-3",
    "prompt": prompt,
    "n": 1,
    "size": "1024x1024",
    "quality": "hd",
    "response_format": "url"
    })
    curl_command = [
    "curl", "-X", "POST", "https://api.openai.com/v1/images/generations",
    "-H", "Content-Type: application/json",
    "-H", f"Authorization: Bearer {openai_key}",
    "-d", data
    ]
    response = subprocess.run(curl_command, capture_output=True, text=True, check=True)
    image_url = json.loads(response.stdout)['data'][0]['url']
    return image_url




def get_processing_button(message_id: str):
    url = "https://api.imaginepro.ai/api/v1/midjourney/button"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {MIDJOURNEY_API_KEY}"
    }
    data = {
        "messageId": message_id,
        "button": "U1"
    }
    # Making the POST request
    response = requests.post(url, json=data, headers=headers)
    # Handling the response
    if response.status_code == 200:
        print(response.json())
    else:
        print("Failed to fetch data:", response.status_code)
        print(response.text)
def get_image(message_id: str):
    headers= {
        "Authorization": f"Bearer {MIDJOURNEY_API_KEY}",
    }
    url =f"https://api.imaginepro.ai/api/v1/midjourney/message/{message_id}"
    status = None
    is_processing = True
    while status != "DONE":
        time.sleep(5)
        get_task_bar = requests.get(url, headers=headers)
        if get_task_bar.status_code == 200:
            print(get_task_bar.json())
            status = get_task_bar.json()['status']
            if status == "PROCESSING":
                print("Processing...")
                if is_processing:
                    get_processing_button(message_id)
                    is_processing = False
            elif status == "FAIL":
                print("Failed to fetch data")
                return None
            elif status == "DONE":
                print("Done")
                return get_task_bar.json()['uri']
def get_stable_image(image_id:str):
    fetch_url = f"https://stablediffusionapi.com/api/v3/fetch/{image_id}"
    headers = {
        'Content-Type': 'application/json',
    }
    fetch_data = {
        "key": stable_key
    }
    fetch_response = requests.post(url=fetch_url,headers=headers,data=json.dumps(fetch_data))
    data_dict = json.loads(fetch_response.text)
    while data_dict['status'] != "success" and data_dict['status'] != "failed":
        time.sleep(2)
        fetch_response = requests.post(url=fetch_url,headers=headers,data=json.dumps(fetch_data))
        data_dict = json.loads(fetch_response.text)
    return data_dict['output'][0]
def get_random_image():
    random_number = random.randint(2, 5)
    url = f"https://backend.exafy.io/media/tmpimages/Picture{random_number}.png"
    return url
if st.button("Submit"):
    if input_text:
        dalle_input_text = "Create a photo of a trade show booth that has a clean, professional design with a focus on minimalistic and modern aesthetics. The booth features large, illuminated modular walls with high-quality printed graphics. The booth uses subtle lighting to enhance the visibility of the text and graphics, creating a sleek and polished look. The inclusion of potted plants adds a touch of natural elements, softening the overall industrial feel. The central counter makes it a well-rounded and visually appealing presentation in an exhibition setting. The booth is about" + input_text
        mid_journey_stable_text = "Modular booth walls with integration LED backlighting makes the wall graphics appear to glow, walls with sharp edges. No other light above."+input_text
        
        with st.spinner("Processing..."):
            random_image = get_random_image()
            print(random_image)
            message_id = post_image_request_midjourney(f"{random_image} {mid_journey_stable_text}")
            dalle_image_url = post_image_request_dalle(dalle_input_text)
            leo_image_url = process_image_leo(random_image, mid_journey_stable_text, LEONARD_API_KEY)
            stable_diff_image_id = post_image_request_stable_diffusion(random_image, mid_journey_stable_text)
            if stable_diff_image_id:
                stable_image = get_stable_image(stable_diff_image_id)
                if stable_image:
                    st.title("Idea 1")
                    st.image(stable_image)
            if dalle_image_url:
                st.title("Idea 2")
                st.image(dalle_image_url)
            if leo_image_url:
                    st.title("Idea 3")
                    st.image(leo_image_url)
            if message_id:
                image_url = get_image(message_id)
                if image_url:
                    st.title("Idea 4")
                    st.image(image_url)
                
    else:
        st.write("Please enter some text to proceed.")












