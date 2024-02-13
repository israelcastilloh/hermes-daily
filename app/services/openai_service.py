from openai import OpenAI, AsyncOpenAI
import shelve
import time
import logging
import json
import app.decorators.auxiliary as auxiliary
import requests as req
from alive_progress import alive_it

# --------------------------------------------------------------
# PARAMS
# --------------------------------------------------------------
secrets = json.loads(auxiliary.get_secret())
OPENAI_API_KEY = secrets['openai_api_key']
OPENAI_ASSISTANT_ID = secrets['open_ai_assistant_id']
client = OpenAI(api_key=OPENAI_API_KEY)

# --------------------------------------------------------------
# UPLOAD FILE WITH PERSONAL INFO
# --------------------------------------------------------------
def upload_file(path):
    # Upload a file with an "assistants" purpose
    file = client.files.create(
        file=open("../../data/Hermes Daily.docx", "rb"), purpose="assistants"
    )

# --------------------------------------------------------------
# CREATE OPENAI ASSISTANT
# --------------------------------------------------------------

def create_assistant(file):
    """
    You currently cannot set the temperature for Assistant via the API.
    """
    assistant = client.beta.assistants.create(
        name="WhatsApp AirBnb Assistant",
        instructions="You're a helpful WhatsApp assistant. Be friendly and funny.",
        tools=[{"type": "retrieval"}],
        model="gpt-4-1106-preview",
        file_ids=[file.id],
    )
    return assistant

# --------------------------------------------------------------
# MANAGE THREADS
# --------------------------------------------------------------
# Use context manager to ensure the shelf file is closed properly
def check_if_thread_exists(wa_id):
    with shelve.open("threads_db") as threads_shelf:
        return threads_shelf.get(wa_id, None)


def store_thread(wa_id, thread_id):
    with shelve.open("threads_db", writeback=True) as threads_shelf:
        threads_shelf[wa_id] = thread_id


# --------------------------------------------------------------
# RUN ASSISTANT
# --------------------------------------------------------------
def run_assistant(thread, name):
    # Retrieve the Assistant
    assistant = client.beta.assistants.retrieve(OPENAI_ASSISTANT_ID)

    # Run the assistant
    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant.id,
        #instructions=f"Use the file as most as you can when asked",
    )

    # Wait for completion
    # https://platform.openai.com/docs/assistants/how-it-works/runs-and-run-steps#:~:text=under%20failed_at.-,Polling%20for%20updates,-In%20order%20to
    while run.status != "completed":
        # Be nice to the API
        time.sleep(0.5)
        run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)

    # Retrieve the Messages
    messages = client.beta.threads.messages.list(thread_id=thread.id)
    new_message = messages.data[0].content[0].text.value
    logging.info(f"Generated message: {new_message}")
    return new_message

# --------------------------------------------------------------
# GENERATE RESPONSE
# --------------------------------------------------------------
def generate_response(message_body, wa_id, name):

    # Check if there is already a thread_id for the wa_id
    thread_id = check_if_thread_exists(wa_id)

    # If a thread doesn't exist, create one and store it
    if thread_id is None:
        logging.info(f"Creating new thread for {name} with wa_id {wa_id}")
        thread = client.beta.threads.create()
        store_thread(wa_id, thread.id)
        thread_id = thread.id

    # Otherwise, retrieve the existing thread
    else:
        logging.info(f"Retrieving existing thread for {name} with wa_id {wa_id} - Thread: {thread_id}")
        thread = client.beta.threads.retrieve(thread_id)

    # Add message to thread
    message = client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=message_body,
    )

    # Run the assistant and get the new message
    new_message = run_assistant(thread, name)

    return new_message


# --------------------------------------------------------------
# DELETE ALL OPENAI THREADS - CAUTION!
# --------------------------------------------------------------
def delete_threads(secrets, OPENAI_API_KEY):
    # Use this command to delete the shelve dict and restore the thread functionality  
    shelf = shelve.open('threads_db')
    shelf.clear()
    shelf['0'] = list(range(10000))
    shelf.close()
    logging.info('Deleting Shelves')

    client = OpenAI(api_key=OPENAI_API_KEY)
    token = secrets['openai_api_sess']
    org = secrets['openai_api_org'] 
    url = "https://api.openai.com/v1/threads"

    headers = {
        "Authorization": f"Bearer {token}", 
        "Openai-Organization": f"{org}",
        "OpenaI-Beta": "assistants=v1"
    }

    params = {"limit": 10}
    resp = req.get(url, headers=headers, params=params)
    
    ids = [t['id'] for t in resp.json()['data']]

    while len(ids) > 0:
        for tid in alive_it(ids, force_tty=True):
            client.beta.threads.delete(tid)
            time.sleep(1)
        resp = req.get(url, headers=headers, params=params)
        ids = [t['id'] for t in resp.json()['data']]


