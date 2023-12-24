import json
import requests
import os
from openai import OpenAI
from prompts import formatter_prompt, assistant_instructions

OPENAI_API_KEY = os.environ['OPENAI_API_KEY']

# Init OpenAI Client
client = OpenAI(api_key=OPENAI_API_KEY)


def get_order_details(order_number):
  try:
    # Airtable API endpoint URL
    airtable_api_url = "https://api.airtable.com/v0/appOoaBhRdvfjBiUp/orderid"

    # Personal Access Token
    personal_access_token = "patz090yfBntHMvQ5.f0ec375e72406f451e684ef714c777f"+ \
  "21d51085b4ba9791c02d829a63fe82ef5"

    # Set up headers with the Personal Access Token
    headers = {
        "Authorization": f"Bearer {personal_access_token}",
        "Content-Type": "application/json"
    }

    # Set up parameters for the filter query
    params = {
        "filterByFormula": f"orderid = {order_number}"
    }

    # Make a GET request to Airtable API
    response = requests.get(airtable_api_url, headers=headers, params=params)


    if response.status_code == 200:
        data = response.json()
        if data.get('records'):
            record = data['records'][0]['fields']
            order_info = {
                'id': record.get('Orderid'),
                'status': record.get('Status'),
                'addres': record.get('addres'),
            }
            return order_info
        else:
            return f"Order with order number {order_number} not found."
    else:
        return f"Error: {response.text}"

  except Exception as e:
    print(f"Error: {e}")
    return "Error occurred while fetching order information."

def simplify_order_data(data):
  try:

    data_str = json.dumps(data, indent=2)

    # Getting formatter prompt from "prompts.py" file
    system_prompt = formatter_prompt

    completion = client.chat.completions.create(
        model="gpt-4-1106-preview",
        messages=[
            {
                "role": "system",
                "content":
                system_prompt  # Getting prompt from "prompts.py" file
            },
            {
                "role":
                "user",
                "content":
                f"Here is some data, parse and format it exactly as shown in the example: {data_str}"
            }
        ],
        temperature=0)

    simplified_data = json.loads(completion.choices[0].message.content)
    print("Simplified Data:", simplified_data)
    return simplified_data

  except Exception as e:
    print("Error simplifying data:", e)
    return None

def track_order(order_number):
  order_details = get_order_details(order_number)
  return simplify_order_data(order_details)
  
# Create or load assistant
def create_assistant(client):
  assistant_file_path = 'assistant.json'

  # If there is an assistant.json file already, then load that assistant
  if os.path.exists(assistant_file_path):
    with open(assistant_file_path, 'r') as file:
      assistant_data = json.load(file)
      assistant_id = assistant_data['assistant_id']
      print("Loaded existing assistant ID.")
  else:
    # If no assistant.json is present, create a new assistant using the below specifications

    file = client.files.create(file=open("knowledge.docx", "rb"),
                               purpose='assistants')

    assistant = client.beta.assistants.create(

        instructions=assistant_instructions,
        model="gpt-4-1106-preview",
        tools=[
            {
                "type": "retrieval"  # This adds the knowledge base as a tool
            },
            {
              "type": "function",  
            
              "function": {
                  "name": "track_order",
                  "description":
                "Track order details based on the order number.",
                  "parameters": {
                    "type": "object",
                    "properties": {
                      "orderID": {
                        "type": "string",
                        "description": "Order ID for tracking the order."
                      }
                    }
                  },
                      "required": ["orderID"]
              }
            }
        ],
        file_ids=[file.id])

    # Create a new assistant.json file to load on future runs
    with open(assistant_file_path, 'w') as file:
      json.dump({'assistant_id': assistant.id}, file)
      print("Created a new assistant and saved the ID.")

    assistant_id = assistant.id

  return assistant_id
