# Lucy IoT Monitoring Assistant

Lucy is an AI-powered chatbot application built with [Flask](https://flask.palletsprojects.com/) and [ThingsBoard](https://thingsboard.io/) REST APIs. It provides real-time insights into IoT infrastructure and smart facilities by fetching telemetry and alarm data from a ThingsBoard instance. Lucy can answer natural-language questions about device status, alarms, and other operational details at various smart facilities and sites.

---

## Table of Contents

1. [Features](#features)  
2. [Architecture Overview](#architecture-overview)  
3. [Prerequisites](#prerequisites)  
4. [Installation](#installation)  
5. [Configuration](#configuration)  
6. [Running the Application](#running-the-application)  
7. [Usage](#usage)  
8. [Project Structure](#project-structure)  
9. [Additional Notes](#additional-notes)  

---

## Features

- **AI Chatbot (Lucy)**  
  - Uses an OpenAI model to answer questions about IoT devices, telemetry, and alarms.
  - Decides if a user query requires IoT data from ThingsBoard or a more general AI response.

- **ThingsBoard Integration**  
  - Fetches real-time telemetry data from devices managed in ThingsBoard.
  - Displays a dynamic list of devices and device types.
  - Retrieves alarm information from the ThingsBoard instance.

- **Dashboards Selector**  
  - A landing page that presents a list of available dashboards (sites).
  - Clicking a dashboard leads to a chat interface with Lucy.

- **Material Design-Inspired UI**  
  - A user-friendly, minimalistic UI for chat and data selection.
  - Split-screen with side panels for device listings and chat.

---

## Architecture Overview

1. **Flask (Python Backend)**  
   - Exposes routes (`/` for dashboard selection, `/home` for the main chat page).  
   - Authenticates with ThingsBoard (UNDP IoT instance) via the [tb-rest-client](https://github.com/thingsboard/python_tb_rest_client).  
   - Calls OpenAI’s API for chat completions.  

2. **Frontend Templates** (HTML/CSS/JavaScript)  
   - Served by Flask using Jinja2 templates.
   - Two main templates:
     1. **landing.html** – Displays site/dashboards list with a search feature.
     2. **index.html** – The chat UI with side panels for devices and user interaction.

3. **ThingsBoard**  
   - Manages IoT devices, telemetry data, and alarms.
   - The app queries the REST API for real-time info.  
   - Device & alarm data are integrated into Lucy’s responses.

4. **OpenAI**  
   - Processes user queries in natural language.
   - Decides if a query should be answered from IoT data or a more general chatbot response.
   - Summarizes device telemetry and alarm states in a user-friendly manner.

---

## Prerequisites

- **Python 3.8+**  
- **pip** (Python package manager)
- **Git** (optional, if you are cloning from a repository)

Additionally, you need:

1. **ThingsBoard REST Client** credentials:
   - `TB_URL` (ThingsBoard base URL; for example, `https://dashboard.iot.undp.org`)
   - `USERNAME` / `PASSWORD` (valid credentials to log in)
2. **OpenAI API Key** with permissions to use the GPT-based model.

---

## Installation

1. **Clone or Download** this repository:
   ```bash
   git clone https://github.com/your-org/your-repo.git
   cd your-repo
Create a virtual environment (recommended):

bash


python -m venv venv
source venv/bin/activate  # Linux/Mac
# or venv\Scripts\activate on Windows
Install Python dependencies:

bash


pip install -r requirements.txt
Make sure the requirements.txt includes:

tb-rest-client
Flask
openai
Any other necessary dependencies
(Optional) Environment Variables
You can set environment variables in your shell or a .env file. See Configuration for details.

Configuration
Inside the Python code (app.py), you’ll find the following variables:

python


TB_URL = "https://dashboard.iot.undp.org"
USERNAME = "cph@undp.org"
PASSWORD = "12345678"
openai_client = OpenAI(api_key="sk-...<YOUR_API_KEY>...")
Steps to configure:

ThingsBoard URL
Change TB_URL to match your instance ("https://dashboard.iot.undp.org" or any other valid TB URL).

ThingsBoard Credentials
Update USERNAME and PASSWORD with valid credentials.

OpenAI Key
Replace the placeholder "sk-...<YOUR_API_KEY>..." with your actual OpenAI API key.
Alternatively, load it from an environment variable:

python


import os
openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
Then set it externally:

bash


export OPENAI_API_KEY="sk-..."
Flask Secret Key
The application sets app.secret_key = "suiiie". Change it to a secure random string for production.

Running the Application
Activate your virtual environment (if not already):

bash


source venv/bin/activate
Run the Flask app:

bash


python app.py
By default, it listens on 0.0.0.0:8080 in debug mode.

Open your browser and navigate to:

arduino


http://localhost:8080
(Or the host/port you used.)

Usage
1. Landing Page (Dashboards)
The homepage (/) lists dashboards retrieved from dashboards/data.json.
You can search for a site using the search box.
Clicking a dashboard title takes you to /home?dashboard_id=<ID> and sets that site’s context in the session.
2. Chat Interface
On the /home page, a Material Design-like layout appears:

Left side panel: (currently displaying a UNDP logo).
Center: Chat box (Lucy’s conversation).
Right side panel: List of available devices from the selected site.
Ask Lucy about:

Alarms in the system (e.g., “Are there any current alarms?”).
Device telemetry (e.g., “What is the temperature sensor reading?”).
General questions (Lucy decides if an IoT data lookup is needed).
Lucy’s logic:

Checks if your query references any device or alarm.
If yes, Lucy fetches telemetry from ThingsBoard (and alarms) to form a detailed response.
If no, Lucy provides a general GPT-based answer.
3. Viewing Alarms
If the site has active alarms, Lucy includes them in the conversation.
If no active alarms, Lucy will respond accordingly.
Project Structure
Here’s a simplified view of the main files/folders:

php


.
├── app.py                      # Main Flask application
├── requirements.txt            # Python dependencies
├── dashboards
│   └── data.json               # Contains dashboard metadata
├── templates
│   ├── landing.html            # Landing page to select dashboards
│   └── index.html              # Chat page template
└── static
    └── images
        └── undplogo.png       # Example image (UNDP logo)
app.py
Contains Flask routes (/, /home) and chatbot logic.
Authenticates with ThingsBoard, fetches telemetry, and calls OpenAI’s GPT model.
dashboards/data.json
Stores data about available dashboards (sites).
landing.html
Jinja2 template for listing dashboards with a search box.
index.html
Jinja2 template for the chat interface, side panels, and user input.
Additional Notes
Production Considerations

Disable debug=True in app.run() for production.
Use a production-ready web server (e.g., gunicorn, uWSGI).
Keep your OpenAI API key secure (avoid committing .env or secrets).
ThingsBoard Alarms

The code fetches “all” alarms up to 10000 entries. You can adjust this limit or filter by severity/status/time.
Extensibility

Modify the AI logic in need_tb() or the final prompt for specialized responses.
Parse timeseries values more thoroughly if you have complex IoT data.
Front-End Enhancements

The HTML/CSS is intentionally minimal. Consider using Vue, React, or a more advanced Material UI kit.
Logging

Python’s built-in logging is used. Adjust the log level or add detailed logs as needed.
We hope Lucy helps you explore real-time IoT data with AI-powered intelligence! If you have questions or issues, please reach out or open a ticket.