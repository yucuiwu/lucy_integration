import json
import logging
import os
from flask import Flask, jsonify, request, render_template, session
from tb_rest_client.rest_client_pe import *
import re
import openai
from dotenv import load_dotenv

# 
load_dotenv()

# OpenAI API Configuration
openai.api_type = os.getenv('OPENAI_API_TYPE')
openai.azure_endpoint = os.getenv('OPENAI_AZURE_ENDPOINT')
openai.api_key = os.getenv('OPENAI_API_KEY')
openai.api_version = os.getenv('OPENAI_API_VERSION')


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


TB_URL = os.getenv('TB_URL')
USERNAME = os.getenv('TB_USERNAME')
PASSWORD = os.getenv('TB_PASSWORD')

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY')  

def get_danshboard():
    
    with RestClientPE(base_url=TB_URL) as rest_client:
        
        rest_client.login(username=USERNAME, password=PASSWORD) 
        dashboard = rest_client.get_user_dashboards(page_size=100, page=0)
        
        dashboard_json = json.dumps(dashboard, default=lambda o: o.__dict__)
        
        print(dashboard_json)
        
        with open('./dashboards/data.json', 'w') as json_file:
            json_file.write(dashboard_json)    


def sanitize_filename(filename):
    """
    Sanitizes the filename by removing invalid characters.
    """
    return re.sub(r'[<>:"/\\|?*\n]', '_', filename)

def get_openai_response(model, system_content, user_content):
    """
    Unified function to get responses from OpenAI API.
    
    Args:
        model (str): The OpenAI model to use
        system_content (str): The system message content
        user_content (str): The user message content
    
    Returns:
        str: The generated text response
    """
    try:
        completion = openai.chat.completions.create(
            model="gpt-4o-itm-sicu",  
            messages=[
                {"role": "system", "content": system_content},
                {"role": "user", "content": user_content}
            ],  
            temperature=0.7,
            max_tokens=800,
            top_p=0.95,
            frequency_penalty=0,
            presence_penalty=0,
            stop=None
        )
        return completion.choices[0].message.content
    except Exception as e:
        print(f"Error with OpenAI API: {e}")
        return ""
    
    
    

def get_device_info(rest_client, entity_type, entity_id):
    """
    Get device information including telemetry, title, and type.
    
    Args:
        rest_client: ThingsBoard REST client
        entity_type (str): Type of entity (usually "DEVICE")
        entity_id: Entity ID object
    
    Returns:
        tuple: (title, device_type, data, device_name) or (None, None, None, None) if error
    """
    try:
        data = rest_client.telemetry_controller.get_latest_timeseries_using_get(entity_type, entity_id)
        device_id = DeviceId(entity_id.id, entity_type)
        device = rest_client.get_device_by_id(device_id)
        attributes = rest_client.telemetry_controller.get_attributes_using_get(entity_type, entity_id)
        
        title = "N/A"
        for attr in attributes:
            if attr['key'] == 'title':
                title = attr['value']
                break
                
        if data == {} or title == "N/A":
            return None, None, None, None
            
        return title, device.type, data, device.name
    except Exception as e:
        logging.error(f"Error getting device info: {e}")
        return None, None, None, None

def site_info(dashboard, rest_client):
    """
    Get information about all devices in a site/dashboard.
    
    Args:
        dashboard: ThingsBoard dashboard object
        rest_client: ThingsBoard REST client
    
    Returns:
        dict: Dictionary mapping device titles to device types
    """
    available_devices = {}
    dashboard_dict = dashboard.to_dict()
    entity_aliases = dashboard_dict.get("configuration", {}).get("entityAliases", {})

    for key, value in entity_aliases.items():
        filter_data = value.get("filter", {})
        single_entity = filter_data.get("singleEntity", {})
        if single_entity.get("entityType") == "DEVICE":
            device_id = single_entity.get("id")
            entity_type = single_entity.get("entityType")
            entity_id = EntityId(device_id, entity_type)
            
            title, device_type, _, _ = get_device_info(rest_client, entity_type, entity_id)
            if title and device_type:
                available_devices[title] = device_type
    
    return available_devices
    
def need_tb(query, site_information):
    """
    Use OpenAI to decide whether the user's query references or requires the Thingsboard IOT monitoring System.
    
    Args:
        query (str): User's query
        site_information (dict): Dictionary of device information
    
    Returns:
        bool: True if the query needs ThingsBoard data, False otherwise
    """
    prompt = (
        "You are an intelligent IT and network assistant. "
        "You have a list of IoT devices in a site with their corresponding locations and device types:\n"
        f"{site_information}\n\n"
        "Here is the user's query:\n"
        f"'{query}'\n\n"
        "Determine if the user's query references or might reference any of the listed locations, "
        "device names, or device types (including synonyms or partial matches). "
        "For instance, if the user mentions 'door' of any sort and the list has 'Door Sensor', "
        "consider that a match. If the query references a location that contains 'room' and "
        "the site info has 'System Room' or 'Meeting Room,' treat that as referencing it. "
        "If the query references any location or device from the list (even partially), respond with ONLY 'YES'. "
        "If the query does not reference any location or device, respond with ONLY 'NO'. "
        "If the query mentions alarms in any way, respond with ONLY 'YES'. "
        "Do not provide any explanation or additional text."
    )
    
    system_content = (
        "You are an intelligent IT assistant. Decide if the user's query references "
        "any of the listed locations or IoT devices (including partial or synonymous matches)."
    )
    
    try:
        answer = get_openai_response("gpt-4", system_content, prompt).strip().upper()
        return answer == "YES"
    except Exception as e:
        logging.error(f"Error with OpenAI API: {e}")
        return False

def get_alarm_information(rest_client):
    """
    Get information about all alarms in the system.
    
    Args:
        rest_client: ThingsBoard REST client
    
    Returns:
        str: Formatted string of alarm information
    """
    alarms = rest_client.alarm_controller.get_all_alarms_using_get(10000, 0)
    data = getattr(alarms, 'data', [])
    
    if not data:
        return "No alarms found."
        
    alarm_info = ""
    for alarm_data in data:
        alarm_string = (
            f"Alarm Name: {getattr(alarm_data, 'name', 'N/A')}, "
            f"Alarm Type: {getattr(alarm_data, 'type', 'N/A')}, "
            f"Severity: {getattr(alarm_data, 'severity', 'N/A')}, "
            f"Status: {getattr(alarm_data, 'status', 'N/A')}, "
            f"Originator Name: {getattr(alarm_data, 'originator_name', 'N/A')}, "
            f"Originator Label: {getattr(alarm_data, 'originator_label', 'N/A')}, "
            f"Originator Entity Type: {getattr(getattr(alarm_data, 'originator', {}), 'entity_type', 'N/A')}, "
            f"Originator ID: {getattr(getattr(alarm_data, 'originator', {}), 'id', 'N/A')}.\n"
        )
        alarm_info += alarm_string
    
    return alarm_info

def get_devices_information(rest_client, entity_aliases, dashboard_dict):
    """
    Get detailed information about all devices in a dashboard.
    
    Args:
        rest_client: ThingsBoard REST client
        entity_aliases: Entity aliases from dashboard
        dashboard_dict: Dashboard dictionary
    
    Returns:
        tuple: (device_info_str, available_devices_list)
    """
    device_info = ""
    available_devices = []
    
    for key, value in entity_aliases.items():
        filter_data = value.get("filter", {})
        single_entity = filter_data.get("singleEntity", {})
        if single_entity.get("entityType") == "DEVICE":
            alias = value.get("alias")
            device_id = single_entity.get("id")
            entity_type = single_entity.get("entityType")
            dashboard_name = dashboard_dict.get('name', f"dashboard_{dashboard_id}")
            sanitized_name = sanitize_filename(dashboard_name)
            entity_id = EntityId(device_id, entity_type)
            
            title, device_type, data, device_name = get_device_info(rest_client, entity_type, entity_id)
            if title and device_type and data:
                available_devices.append(f"{title}, {device_type}")
                device_info += f"Label: {title}, Device: {device_name}, Device Type: {device_type}, Readings: {data}\n\n"
    
    return device_info, available_devices

def load_dashboards():
    """
    Load available dashboards from data file.
    
    Returns:
        list: List of dashboard dictionaries with id and title
    """
    with open('dashboards/data.json', 'r', encoding='utf-8') as file:
        data = json.load(file)
        dashboards = [
            {"id": item["_id"]["_id"], "title": item["_title"]}
            for item in data["_data"]
        ]
        return dashboards

@app.route('/', methods=['GET'])
def landing_page():
    """Route for the landing page displaying available dashboards."""
    get_danshboard()
    dashboards = load_dashboards()
    return render_template('landing.html', dashboards=dashboards)

@app.route('/home', methods=['GET', 'POST'])
def home():
    """Route for the main home page handling both display and API queries."""
    with RestClientPE(base_url=TB_URL) as rest_client:
        rest_client.login(username=USERNAME, password=PASSWORD)
        
        if request.method == 'GET':
            dashboard_id = request.args.get('dashboard_id', '')
            if dashboard_id:
                session['dashboard_id'] = dashboard_id    
            
            dashboard = rest_client.get_dashboard_by_id(dashboard_id)
            available_devices = site_info(dashboard, rest_client)
            
            return render_template(
                'index.html', 
                room_devices=available_devices
            )  
            
        if request.method == 'POST':
            data = request.get_json()  # Parse JSON data
            query = data.get('query')  # Extract the 'query' field
            logging.info("Logged in as: %s", USERNAME)

            dashboard_id = session.get('dashboard_id')
            dashboard_id = DashboardId(
                id=dashboard_id,
                entity_type="DASHBOARD"
            )
            dashboard = rest_client.get_dashboard_by_id(dashboard_id)
            site_information = site_info(dashboard, rest_client)
            
            # Check if we need to use ThingsBoard data for this query
            if not need_tb(query, site_information):
                # Simple query that doesn't need ThingsBoard data
                system_content = "You are a LUCY, a helpful assistant for IoT (Internet of Things) monitoring."
                generated_text = get_openai_response("gpt-4o-mini", system_content, query)
                return jsonify({
                    "response": generated_text,
                })
            
            # Query needs ThingsBoard data
            dashboard_dict = dashboard.to_dict()
            entity_aliases = dashboard_dict.get("configuration", {}).get("entityAliases", {})
            
            # Get alarm information
            alarm_info = get_alarm_information(rest_client)
            
            # Get device information
            device_info, available_devices = get_devices_information(rest_client, entity_aliases, dashboard_dict)
            
            # Create prompt for OpenAI
            prompt = f"""
            You are Lucy, an IoT monitoring assistant specialized in analyzing device telemetry and alarms from a ThingsBoard instance.
            Below is the user's question, some information about the device(s), and any relevant alarm states.
            User Question:
            {query}
            Device Information and Readings:
            {device_info}
            Site Alarms:
            {alarm_info}
            Please provide your best answer to the user's question by relevant metrics and alarms if appropriate.
            Keep the response within 5 sentences
            """
            
            system_content = "You are Lucy, an IoT monitoring assistant specialized in analyzing device telemetry and alarms from a ThingsBoard instance."
            generated_text = get_openai_response("gpt-4o-mini", system_content, prompt)
            
            logging.info("Decision AI Answer: %s", generated_text)
            
            return jsonify({
                "response": generated_text,
                "devices": available_devices
            })

# ------------------ Application Entry Point ------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=True)
