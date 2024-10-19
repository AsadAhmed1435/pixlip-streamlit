import requests
import json
import os
import threading
import time
from datetime import datetime


def process_image(image_url, prompt, api_key):
    """Downloads an image, uploads it, and generates a new image based on the prompt."""
    
    def delete_file_after_delay(file_path, delay):
        """Deletes the specified file after a delay."""
        time.sleep(delay)
        os.remove(file_path)
        print(f"File {file_path} has been deleted.")
    
    # Download image from URL
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    image_path = f"downloaded_image_{timestamp}.jpg"
    
    response = requests.get(image_url)
    if response.status_code == 200:
        with open(image_path, 'wb') as f:
            f.write(response.content)
        print("Image downloaded successfully.")
    else:
        print("Failed to download image.")
        return None
    
    # Get upload details
    post_url = "https://cloud.leonardo.ai/api/rest/v1/init-image"
    post_payload = { "extension": "jpg" }
    post_headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": f"Bearer {api_key}"
    }
    post_response = requests.post(post_url, json=post_payload, headers=post_headers)
    upload_details = post_response.json()
    
    init_image_id = upload_details["uploadInitImage"]["id"]
    upload_details = {
        'fields': upload_details["uploadInitImage"]["fields"],
        'url': upload_details["uploadInitImage"]["url"]
    }
    
    # Upload image
    with open(image_path, 'rb') as image_file:
        files = {'file': image_file}
        response = requests.post(upload_details['url'], data=json.loads(upload_details['fields']), files=files)
    
    print(response.status_code)
    if response.status_code != 204:
        print("Failed to upload image.")
        return None
    
    # Set a timer to delete the image after 1 minute
    timer = threading.Thread(target=delete_file_after_delay, args=(image_path, 60))
    timer.daemon = True
    timer.start()
    
    # Generate new image
    url = 'https://cloud.leonardo.ai/api/rest/v1/generations'
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    data = {
        "height": 512,
        "width": 1024,
        "modelId": "aa77f04e-3eec-4034-9c07-d0f619684628",
        "prompt": prompt,
        "controlnets": [
            {
                "initImageId": init_image_id,
                "initImageType": "UPLOADED",
                "preprocessorId": 67,
                "strengthType": "High",
                "influence": 0.5
            }
        ]
    }
    
    response = requests.post(url, headers=headers, json=data)
    if response.status_code != 200:
        print("Failed to generate image.")
        return None
    
    results = response.json()
    generation_id = results['sdGenerationJob']['generationId']
    
    status = 'PENDING'
    while status == 'PENDING':
        url = f"https://cloud.leonardo.ai/api/rest/v1/generations/{generation_id}"
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            generations_by_pk = response.json()
            status = generations_by_pk['generations_by_pk']['status']
            print(f"Status: {status}")
        else:
            print("Failed to fetch data:", response.status_code)
            print(response.text)
            return None
        time.sleep(5)
    
    if status == 'COMPLETE':
        print("Image generation complete")
        final_result = generations_by_pk['generations_by_pk']['generated_images'][0]['url']
        return final_result
    else:
        print("Image generation failed.")
        return None
