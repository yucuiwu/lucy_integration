import os
import requests
import time
from datetime import datetime
import json
from rapidfuzz import process
import re
from typing import Tuple
import openai
from flask import Flask, make_response, render_template, request, jsonify, session
from countryinfo import CountryInfo
from dotenv import load_dotenv

load_dotenv()

# ------------------ Configuration and Constants ------------------
# Zabbix API Configuration
ZABBIX_API_TOKEN = os.getenv('ZABBIX_API_TOKEN')
ZABBIX_URL = os.getenv('ZABBIX_URL')
ZABBIX_HEADERS = {
    "Content-Type": "application/json-rpc"
}

# OpenAI API Configuration
openai.api_type = os.getenv('OPENAI_API_TYPE')
openai.azure_endpoint = os.getenv('OPENAI_AZURE_ENDPOINT')
openai.api_key = os.getenv('OPENAI_API_KEY')
openai.api_version = os.getenv('OPENAI_API_VERSION')

# Country Dashboards Mapping
DASHBOARDS = {
    "Nigeria": 130,
    "Afghanistan": 89,
    "Comoros": 855,
    "Ethiopia": 112,
    "Iran": 561,
    "Myanmar": 127,
    "North Korea": 735,
    "Mozambique": 126,
    "Rwanda": 738,
    "Sudan": 751,
    "Syria": 752,
    "Haiti": 118
}

# Infrastructure Types
INFRASTRUCTURES = [
    "OneICTbox",
    "BE6K",
    "OpenDNS",
    "UPS",
    "MSS-3",
    "VSAT",
    "AnyConnect-VPN",
    "VOIP VSAT",
]

# Weather detection keywords
# WEATHER_KEYWORDS = [
#     "weather", "forecast", "climate", "rain", "snow", "humidity", "temperature",
#     "wind", "storm", "sun", "cloud", "hail", "fog", "dew",
#     "sunny", "cloudy", "rainy", "snowy", "windy", "stormy", "hailstorm", "foggy", "dewy"
# ]

# Flask Application Setup
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY')  # Required for session management

@app.after_request
def add_ngrok_header(response):
    """Add header to skip ngrok browser warning."""
    response.headers["ngrok-skip-browser-warning"] = "true"
    return response

# ------------------ Utility Functions ------------------

def use_openai(system_content, user_content):
    """
    Make a request to OpenAI API with the given content.
    
    Args:
        system_content: The system message for GPT
        user_content: The user query for GPT
        
    Returns:
        str: The GPT-generated response or empty string on error
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

def jsonify_with_ngrok(data, status_code=200):
    """
    Create a JSON response with ngrok header.
    
    Args:
        data: The data to be converted to JSON
        status_code: HTTP status code (default: 200)
        
    Returns:
        Response: Flask response with ngrok header
    """
    response = jsonify(data)    
    response.status_code = status_code
    response.headers["ngrok-skip-browser-warning"] = "true"
    return response

def save_to_json(data, filename):
    """
    Save data to a JSON file.
    
    Args:
        data: The data to save
        filename: The path to the output file
    """
    try:
        with open(filename, "w") as file:
            json.dump(data, file, indent=4)
        print(f"Data saved to {filename}")
    except Exception as e:
        print(f"Error saving to JSON file: {e}")

def normalize(text):
    """
    Normalize text by removing non-alphanumeric characters and converting to lowercase.
    
    Args:
        text: The text to normalize
        
    Returns:
        str: Normalized text
    """
    return re.sub(r'[^a-zA-Z0-9]', '', text).lower()

# ------------------ Zabbix API Functions ------------------

def get_dashboard_info(dashboard_id, token):
    """
    Fetch dashboard information from Zabbix API.
    
    Args:
        dashboard_id: The ID of the dashboard
        token: Zabbix API token
        
    Returns:
        list: Dashboard data if successful, None otherwise
    """
    try:
        request_data = {
            "jsonrpc": "2.0",
            "method": "dashboard.get",
            "params": {
                "output": "extend",
                "dashboardids": [dashboard_id],
                "selectPages": "extend"
            },
            "auth": token,
            "id": 1
        }
        response = requests.post(ZABBIX_URL, headers=ZABBIX_HEADERS, json=request_data)
        response.raise_for_status()
        data = response.json()
        
        if "error" in data:
            print(f"Error: {data['error']['message']} - {data['error']['data']}")
            return None
        
        return data.get("result", [])
    except Exception as e:
        print(f"Error fetching dashboard info: {e}")
        return None

def get_host_info(hostid, token):
    """
    Fetch detailed information about a host device.
    
    Args:
        hostid: The ID of the host
        token: Zabbix API token
        
    Returns:
        list: Host information if successful, None otherwise
    """
    try:
        request_data = {
            "jsonrpc": "2.0",
            "method": "host.get",
            "params": {
                "output": "extend",
                "hostids": hostid,
                "selectItems": "extend",
                "selectTriggers": "extend",
                "selectInventory": "extend"
            },
            "auth": token,
            "id": 1
        }

        response = requests.post(ZABBIX_URL, headers=ZABBIX_HEADERS, json=request_data)
        response.raise_for_status()
        data = response.json()

        if "error" in data:
            print(f"Error: {data['error']['message']} - {data['error']['data']}")
            return None
            
        return data.get("result", [])
    except Exception as e:
        print(f"Error fetching host information: {e}")
        return None

def get_problems(hostid, token):
    """
    Fetch problems for a specific host.
    
    Args:
        hostid: The ID of the host
        token: Zabbix API token
        
    Returns:
        list: Problems if successful, empty list otherwise
    """
    try:
        request_data = {
            "jsonrpc": "2.0",
            "method": "problem.get",
            "params": {
                "output": "extend",
                "hostids": hostid,
                "recent": True,
                "selectAcknowledges": "extend",
                "selectTags": "extend",
                "sortfield": ["eventid"],
                "sortorder": "DESC"
            },
            "auth": token,
            "id": 1
        }
        
        response = requests.post(ZABBIX_URL, headers=ZABBIX_HEADERS, json=request_data)
        response.raise_for_status()
        data = response.json()
        
        if "error" in data:
            print(f"Error: {data['error']['message']} - {data['error']['data']}")
            return []
        
        return data.get("result", [])
    except Exception as e:
        print(f"Error fetching problems: {e}")
        return []

def get_hostid(widgets):
    """
    Extract host IDs from dashboard widgets.
    
    Args:
        widgets: List of dashboard widgets
        
    Returns:
        list: List of unique host IDs
    """
    hostids_set = set()

    for widget in widgets:
        fields = widget.get("fields", [])
        for field in fields:
            if field.get("name").startswith("hostid"):
                hostids_set.add(field.get("value"))

    return list(hostids_set)

# ------------------ AI Decision Functions ------------------

def need_nms(query: str, infrastructures: list) -> bool:
    """
    Determine if the query requires NMS (Network Management System).
    
    Args:
        query: The user's query
        infrastructures: List of infrastructure types
        
    Returns:
        bool: True if NMS is needed, False otherwise
    """
    prompt = (
        "You are an intelligent IT and network assistant.\n"
        "You have a list of possible infrastructures:\n"
        f"{infrastructures}\n\n"
        "Here is the user's query:\n"
        f"'{query}'\n\n"
        "If the user is asking about any of these infrastructures, "
        "network devices, or network monitoring details, return ONLY 'YES'.\n"
        "Otherwise, return ONLY 'NO'."
    )

    system_content = "You decide if the user query references any of the listed infrastructures or network systems."
    answer = use_openai(system_content, prompt)
    
    answer = answer.strip().upper()
    return True if "YES" in answer else False

# def is_weather_query(text: str, threshold: int = 95) -> Tuple[bool, str]:
#     """
#     Check if the query is related to weather.
    
#     Args:
#         text: The user's query
#         threshold: Matching threshold (default: 95)
        
#     Returns:
#         tuple: (is_weather, matched_term)
#     """
#     text_cleaned = re.sub(r'[^\w\s]', '', text)
#     text_lower = text_cleaned.lower()
#     words = text_lower.split()
    
#     for word in words:
#         best_match, match_score, _ = process.extractOne(word, WEATHER_KEYWORDS)
#         if match_score >= threshold:
#             return True, best_match

#     return False, ""

# def extract_city_from_query(query: str, matched_country) -> str:
#     """
#     Extract city name from query, defaulting to country capital if none found.
    
#     Args:
#         query: The user's query
#         matched_country: The country for capital fallback
        
#     Returns:
#         str: The detected city name
#     """
#     prompt = (
#         "Extract the city name from the following query. "
#         "If no city name is present, return 'Unknown'. "
#         f"Query: '{query}'"
#     )
    
#     system_content = "You are a helpful assistant for extracting Cities from text."
#     city = use_openai(system_content, prompt)
    
#     if not city or city.lower() == "unknown":
#         country = CountryInfo(matched_country)
#         city = country.capital()
        
#     return city

def resolve_host_id(country_devices_query, query):
    """
    Match user query to a specific host/device ID.
    
    Args:
        country_devices_query: String with device information
        query: The user's query
        
    Returns:
        str: Host ID if found, '-1' otherwise
    """
    prompt = (
        f"Match the user's query to a device and return ONLY the corresponding HostID.\n"
        f"Here is the list of devices:\n"
        f"{country_devices_query}\n\n"
        f"User's question: {query}\n\n"
        "Return ONLY the HostID as a number. If no match is found, return -1."
    )

    system_content = "You are an intelligent IT and network assistant."
    return use_openai(system_content, prompt)
    
def match_country(query, dashboards):
    """
    Match user query to a country and return the dashboard ID.
    
    Args:
        query: The user's query
        dashboards: Dictionary mapping countries to dashboard IDs
        
    Returns:
        int: Dashboard ID if matched, -1 otherwise
    """
    prompt = (
        f"Match the user's query to a country and return ONLY the corresponding dashboard ID.\n"
        f"Here is the list of countries with their dashboard IDs:\n"
        f"{dashboards}\n\n"
        f"User's query: {query}\n\n"
        "Return ONLY the dashboard ID as a number. If no match is found, return -1."
    )

    system_content = "You are an intelligent assistant that matches queries to countries."
    answer = use_openai(system_content, prompt)
    
    return int(answer) if answer and (answer.isdigit() or answer == "-1") else -1

# ------------------ Route Handlers ------------------

@app.route('/', methods=['GET'])
def landing_page():
    """Render the landing page with dashboard options."""
    return render_template('landing.html', dashboards=DASHBOARDS)

@app.route('/home', methods=['GET', 'POST'])
def home():
    """
    Handle GET requests to display the dashboard 
    and POST requests to process user queries.
    """
    # Handle GET requests to display the dashboard
    if request.method == 'GET':
        dashboard_id = request.args.get('dashboard_id', '')
        if dashboard_id:
            session['dashboard_id'] = dashboard_id
            
        country_devices = {}
        device_name = ""
        dashboard_info = get_dashboard_info(dashboard_id, ZABBIX_API_TOKEN)
        
        if dashboard_info:
            for dashboard in dashboard_info:
                for page in dashboard.get("pages", []):
                    name = page.get("name")
                    widgets = page.get("widgets")
                    hostid = ""
                    hostids = get_hostid(widgets)
                    
                    if len(hostids) > 1:
                        print("Multiple Hosts on One Device: name")
                    if hostids == []:
                        continue
                        
                    hostid = hostids[0]
                    country_devices[name] = hostid
    
        return render_template(
            'index.html', 
            chosen_dashboard=session.get('dashboard_id', ''),
            country_devices=country_devices
        )

    # Handle POST requests for user queries
    if request.method == 'POST':
        data = request.get_json()
        query = data.get('query')
                  
        if not query:
            return jsonify_with_ngrok({"error": "Query is required"}, 400)
        
        chosen_dash_id = session.get('dashboard_id', None)
        
        # Check if query requires NMS
        need_nms_data = need_nms(query, INFRASTRUCTURES)
        
        if need_nms_data == False:
            system_content = "You are Lucy, a network monitoring assistant specialized in analyzing device information for the UNDP ITM."
            generated_text = use_openai(system_content, query)
            return jsonify_with_ngrok({"response": generated_text}, 200)
       
        # Get dashboard and country information
        matched_country = ""
        for country, dashboard_id in DASHBOARDS.items():
            if dashboard_id == chosen_dash_id:
                matched_country = country
                break
                     
        dashboard_id = chosen_dash_id
        dashboard_info = get_dashboard_info(dashboard_id, ZABBIX_API_TOKEN)
        
        if dashboard_info:
            print("Saved Dashboard")
        else:
            print("Failed to retrieve dashboard info.")
            exit(1)
            
        # Extract device information from dashboard
        country_devices = {}
        device_name = ""
        for dashboard in dashboard_info:
            for page in dashboard.get("pages", []):
                name = page.get("name")
                widgets = page.get("widgets")
                hostid = ""
                hostids = get_hostid(widgets)
                
                if len(hostids) > 1:
                    print("Multiple Hosts on One Device: name")
                if hostids == []:
                    continue
                    
                hostid = hostids[0]
                country_devices[name] = hostid
                
        # Build query for host resolution
        country_devices_query = ""
        for key, value in country_devices.items(): 
            country_devices_query = country_devices_query + f"Device: {key}, HostID: {value}. \n"
        
        hostid = resolve_host_id(country_devices_query, query)
        if hostid == '-1':
            return jsonify({
                "response": f"That device cannot be found in {matched_country}",
            })
        
        # Get device name from hostid
        for devicename, host_id in country_devices.items():
            if host_id == hostid:
                device_name = devicename
                break
            
        # Check if we need to fetch problems
        problems_flag = False
        for widget in page.get("widgets", []):
            if widget.get("type") == 'problems':
                problems_flag = True

        # Fetch host information and problems
        hostinfo = get_host_info(hostid, ZABBIX_API_TOKEN)

        if problems_flag:
            probleminfo = get_problems(hostid, ZABBIX_API_TOKEN)

        # Extract device details
        inventory_infomation = hostinfo[0].get("inventory")
        description = hostinfo[0].get("description")
        inventory_name = hostinfo[0].get("inventory")["name"]
        inventory_model = hostinfo[0].get("inventory")["model"]
        location = hostinfo[0].get("inventory")["location"]
        notes = hostinfo[0].get("inventory")["notes"]
        device_infomation = f"Device Name: {device_name}, Device Model: {inventory_model}, Description: {description}, Location: {location}"

        # Process device problems
        device_problems = []
        for problem in probleminfo:
            if problem.get("acknowledges") == []:
                device_problems.append(f"Problem: {problem.get('name')} Severity: {problem.get('severity')}")
            else:
                device_problem = f"Problem: {problem.get('name')} Severity: {problem.get('severity')}"
                acknowledges = problem.get("acknowledges")
                for ack in acknowledges:
                    if not (ack.get("action") == "4" and ack.get("new_severity") == "0"):
                        device_problem = device_problem + f" Detail: {ack.get('message')}"
                        device_problems.append(device_problem)

        # Process device metrics
        device_metrics = []
        host_metrics = hostinfo[0].get("items")
        for metric in host_metrics:
            metric_name = f"Metric Name: {metric['name_resolved']}, " 
            metric_desc = f"Description: {metric['description']}, "
            metric_value = f"Value: {metric['lastvalue']}"
            if metric_desc == "Description: , ":
                device_metrics.append(metric_name + metric_value)
            else:
                device_metrics.append(metric_name + metric_desc + metric_value)

        # Prepare data for GPT prompt
        possible_metrics_str = "\n".join(device_metrics) 
        problems_str = "\n".join(device_problems) if device_problems else "No current problems."
        
        # Create prompt for GPT to analyze the device data
        prompt = f"""
        You are an expert at analyzing network infrastructure data.
        Below is the user question, some information about a device, and a list of potential metrics you can reference.
        User Question:
        {query}
        Device Information:
        {device_infomation}
        Device Problems:
        {problems_str}
        Here is a list of the metrics and their values, find a metric and value pair that matches the query
        {possible_metrics_str}
        Please provide your best answer to the user's question by relevant metrics from the list above.
        
        Keep the response within 5 sentences
        """
        
        # Get response from GPT
        system_content = "You are a helpful assistant for network monitoring."
        generated_text = use_openai(system_content, prompt)
        print("Decision AI Answer")
        print(generated_text)
        
        return jsonify({
            "response": generated_text,
        })
        
    # Default return for other cases
    return render_template('index.html')

# ------------------ Application Entry Point ------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=True)
