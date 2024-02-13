from app.services.openai_service import generate_response
import app.services.spotify_retrieve as spotify_retrieve
import app.decorators.auxiliary as auxiliary
from flask import current_app, jsonify
import requests
import logging
import json
import re


#---------------------------------------------
# SEND INITIAL WHATSAPP TEMPLATE
#---------------------------------------------

def send_template_message(input_phonenumber, secrets):

    url = f"https://graph.facebook.com/v18.0/{secrets['whatsapp_phonenumber']}/messages"

    headers = {
        "Authorization": f"Bearer {secrets['whatsapp_token']}",
        "Content-Type": "application/json",
    }

    data = {
        "messaging_product": "whatsapp",
        "to": f"{input_phonenumber}",
        "type": "template",
           "template": {
                 "name": "initial_message", 
                 "language": { "code": "es_MX"} 
        }
    }
    
    response = requests.post(url, headers=headers, json=data)
    log_http_response(response)


def log_http_response(response):
    logging.info(f"Status: {response.status_code}")
    #logging.info(f"Content-type: {response.headers.get('content-type')}")
    #logging.info(f"Body: {response.text}")


def get_text_message_body(recipient, text):
    return json.dumps(
        {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient,
            "type": "text",
            "text": {"preview_url": False, "body": text},
        }
    )


def send_message(data):
    headers = {"Content-type": "application/json",
                "Authorization": f"Bearer {current_app.config['ACCESS_TOKEN']}"
                }

    url = f"https://graph.facebook.com/{current_app.config['VERSION']}/{current_app.config['PHONE_NUMBER_ID']}/messages"

    try:
        response = requests.post(
            url, data=data, headers=headers, timeout=10
        )  # 10 seconds timeout as an example
        response.raise_for_status()  # Raises an HTTPError if the HTTP request returned an unsuccessful status code
    except requests.Timeout:
        logging.error("Timeout occurred while sending message")
        return jsonify({"status": "error", "message": "Request timed out"}), 408
    except (
        requests.RequestException
    ) as e:  # This will catch any general request exception
        logging.error(f"Request failed due to: {e}")
        return jsonify({"status": "error", "message": "Failed to send message"}), 500
    else:
        # Process the response as normal
        log_http_response(response)
        return response


def process_text_for_whatsapp(text):
    # Remove brackets
    pattern = r"\【.*?\】"
    # Substitute the pattern with an empty string
    text = re.sub(pattern, "", text).strip()
    # Pattern to find double asterisks including the word(s) in between
    pattern = r"\*\*(.*?)\*\*"
    # Replacement pattern with single asterisks
    replacement = r"*\1*"
    # Substitute occurrences of the pattern with the replacement
    whatsapp_style_text = re.sub(pattern, replacement, text)
    return whatsapp_style_text

#---------------------------------------------
# Process Whatsapp Message
#---------------------------------------------
def process_whatsapp_message(body):
    secrets = json.loads(auxiliary.get_secret())
    wa_id = body["entry"][0]["changes"][0]["value"]["contacts"][0]["wa_id"]
    name = body["entry"][0]["changes"][0]["value"]["contacts"][0]["profile"]["name"]
    message = body["entry"][0]["changes"][0]["value"]["messages"][0]

#---------------------------------------------
# OpenAI Integration
#---------------------------------------------
    def generate_open_ai_respone(message_body, wa_id, name):    
        response = generate_response(message_body, wa_id, name)
        return response
    
#-----------------------------------------------------------------------------------------
# SEND RESPONSE TO WHATSAPP BACK
#-----------------------------------------------------------------------------------------
    def process_and_send_message(response, wa_id): 
        response = process_text_for_whatsapp(response)
        data = get_text_message_body(wa_id, response) #current_app.config["RECIPIENT_WAID"]
        send_message(data)


#-----------------------------------------------------------------------------------------
# HANDLE BUTTON INPUT OR OPEN TEXT PROMPT
#-----------------------------------------------------------------------------------------
        
# -------------------------------------------- OPEN PROMPT - HELLO ------------------------------------------
    if message['type'] != 'button':
        prompt = f'Is this message a hello message of any kind: "{message["text"]["body"]}". Answer with True or False only.'
        response = generate_open_ai_respone(prompt, wa_id, name).replace(".", "")
        if response == 'True':
            send_template_message(message['from'], secrets)
# -------------------------------------------- OPEN PROMPT ---------------------------------------------------
        else:
            prompt = message["text"]["body"]
            response = generate_open_ai_respone(prompt, wa_id, name)
# -------------------------------------------- OPEN PROMPT FOR - MUSIC -------------------------------------
            try: 
                response = response.replace("```json", '').replace("```", "")
                if 'artist' in json.loads(response).keys() and 'title' in json.loads(response).keys():
                    response = spotify_retrieve.get_song_url(response, secrets)
            except:
                pass
            process_and_send_message(response, wa_id)

# --------------------------------------------- BUTTON PROMPT ------------------------------------------  
    else: 
        payload = message['button']['payload']
# -------------------------------------------- SPOTIFY REQUEST ----------------------------------------------
        if  payload == 'Spotify':
            prompt = "recommend me a single song, just give me title and artist, " \
            "don't give extra text. response in json exactly as 'title' and 'artist'"
            response = generate_open_ai_respone(prompt, wa_id, name)
            response = spotify_retrieve.get_song_url(response, secrets)
# -------------------------------------------- GYM ROUTINE REQUEST --------------------------------------------
        elif payload == 'Fitness':
            prompt = 'Dame una rutina de cuerpo completo enfocada en generar masa muscular con alto volumen'
            response = generate_open_ai_respone(prompt, wa_id, name)
# -------------------------------------------- FOOD REQUEST --------------------------------------------
        elif payload == 'Food':
            prompt = 'Dame una receta alta en proteinas. Que contenga variedades de verduras' \
                    'Dame la receta completa con ingredientes y como preparla' \
                    'Asegurate que tenga balanceado carbohidratos, carnes y verduras y que sea nutritiva'
            response = generate_open_ai_respone(prompt, wa_id, name)

        process_and_send_message(response, wa_id)



def is_valid_whatsapp_message(body):
    """
    Check if the incoming webhook event has a valid WhatsApp message structure.
    """
    return (
        body.get("object")
        and body.get("entry")
        and body["entry"][0].get("changes")
        and body["entry"][0]["changes"][0].get("value")
        and body["entry"][0]["changes"][0]["value"].get("messages")
        and body["entry"][0]["changes"][0]["value"]["messages"][0]
    )
