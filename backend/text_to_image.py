import requests
import time

image_api_key = "5JKBQ0GMfj2ujVa8VzYObwcl2tgjrw"
prompt = "The content discusses the launch of a flagship product from Google that competes with the iPhone 16 and Galaxy S24. It also highlights the latest advancements in AI technology, along with the challenges and opportunities it presents now and in the future. Additionally, it mentions how 3D printing is revolutionizing sneaker design, especially in smaller brands, and discusses Chegg's layoff of 319 workers due to competition with modern AI chatbots."

def image_post_function(api_key, prompt):
    """
    To request for image creation
    """
    url = "https://api.starryai.com/creations/"
    
    headers = {
        "X-API-Key": f"{api_key}",
        "content-type": "application/json",
        "accept": "application/json"
    }
    payload = {
        "prompt": prompt,
        "model" : "lyra",
        "aspectRatio": "square",
        "images": 1,
        "steps": 15,
        "initialImageMode": "color"
    }

    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 200:
        response_json = response.json()
        return response_json
    
    else:
        return "Error in POST"
 
def image_get_function(request_id, api_key):
    """
    To receive the json containing image urls 

    """
    url_get = f"https://api.starryai.com/creations/{request_id}"
    headers_get = {
        "accept": "application/json",
        "X-API-Key": api_key
    }
    response_imageurl_containing_json = requests.get(url_get, headers=headers_get)

    return response_imageurl_containing_json.json()


def generate_image_urls(image_api_key, prompt):
    """
    Main Function to be called for image generation
    """
    try:

        response_json = image_post_function(image_api_key, prompt)
        request_id = response_json.get("id")
        print(request_id)

        # Adding some wait time so that the Image URL can be released by the API
        while True:
            response_imageurl_containing_json = image_get_function(request_id, image_api_key)
            images_urls = [image["url"] for image in response_imageurl_containing_json.get('images', [])]
            if images_urls != [None]:
                break
            time.sleep(3)
    
        return images_urls

    except Exception as e:
        print(e)




