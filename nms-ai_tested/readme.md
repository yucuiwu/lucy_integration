# NMS-AI: Lucy Network Monitoring Assistant

This repository contains a Flask-based web application named **Lucy**, a network monitoring assistant designed to integrate with Zabbix. Lucy provides real-time insights into network infrastructure and smart facilities, allowing users to query device information, problems, metrics, and more.

---

## Table of Contents
1. [Overview](#overview)  
2. [Features](#features)  
3. [Directory Structure](#directory-structure)  
4. [Prerequisites](#prerequisites)  
5. [Installation](#installation)  
6. [Running the Application Locally](#running-the-application-locally)  
7. [Using Docker](#using-docker)  
8. [Usage](#usage)  
9. [Customization](#customization)  
10. [License](#license)

---

## Overview

Lucy is a chatbot-style interface that connects to Zabbix via the Zabbix API. It provides:

1. **Device Lists and Dashboards**  
   Lists available devices in a chosen country dashboard.

2. **Real-time Queries**  
   Retrieve device metrics, current problems, and diagnostic information.

3. **Material Design-Inspired UI**  
   Attractive chat interface with a side panel for the country/device list.

Lucy is designed to be deployed as a web application. You can run it on your local machine or within a Docker container.

---

## Features

- **Landing Page**  
  Users can select a country from a scrollable list. Each country corresponds to a specific Zabbix dashboard ID.

- **Chat Interface**  
  A real-time chat interface for querying devices, retrieving metrics, and viewing open problems.

- **Zabbix Integration**  
  Lucy connects to the Zabbix API to fetch host information, metrics, problems, and other device data.

- **OpenAI Integration**  
  Uses OpenAI’s model (in the code labeled as `gpt-4o-mini`) to interpret user queries and decide whether to fetch data from the NMS or provide a general answer.

- **Searchable Country List**  
  A simple JavaScript-based country search feature for quickly finding the desired country.

---

## Directory Structure

```plaintext
nms-ai
├── static/
│   └── images/
│       └── undplogo.png
│       └── ...
├── templates/
│   └── index.html          # Chat interface page
│   └── landing.html        # Landing page for country selection
├── app.py                  # Main Flask application
├── Dockerfile              # Docker configuration
├── NMS-Report.docx         # Project documentation (Word document)
├── requirements.txt        # Python dependencies
└── tempCodeRunnerFile.py   # Temporary file (optional, for development)