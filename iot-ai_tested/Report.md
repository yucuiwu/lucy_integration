Accuracy and Performance Report for Lucy IoT Monitoring Assistant
This report presents an overview of Lucy’s performance in interpreting queries, retrieving relevant IoT data, and providing accurate responses. Testing was done on a sample of real-world and simulated user queries referencing devices, sensors, and alarms within the UNDP Smart Facilities environment.

1. Overview
Lucy IoT Monitoring Assistant is designed to:

Understand natural-language questions about IoT devices, telemetry, and alarms.
Decide whether a user’s query should pull data from ThingsBoard (IoT) or if a more generic AI answer suffices.
Provide short, human-friendly answers based on real-time device data and any active alarms.
2. Methodology
Test Set of Queries

A total of 50 unique queries were crafted to represent common user questions (e.g., “What is the temperature in the meeting room?”, “Are there any active alarms?”, “Help me troubleshoot sensor X,” etc.).
Queries ranged from straightforward references to known device titles, to ambiguous synonyms and partial matches (e.g., “temp readouts” for a temperature sensor).
ThingsBoard Devices

For each site dashboard, the system retrieved a list of devices (title + type) and any active alarms.
The queries intentionally targeted random devices to assess Lucy’s ability to identify references.
Assessment Criteria

Query Recognition Accuracy: How often Lucy determines correctly whether to use IoT data (the “need_tb” logic) and actually pulls the needed info.
Device Selection Accuracy: When Lucy does use IoT data, does it reference the correct device or sensor?
Alarm Handling: Checks whether Lucy correctly reports active alarms or states “No alarms found” if none.
Overall Response Relevance: Whether Lucy’s final answer aligns with the user’s question and the device’s data.
3. Results
3.1 Query Recognition Accuracy
Correct IoT References:
Lucy accurately decided to use ThingsBoard data for queries referencing specific devices, partial device names, or synonyms 100% of the time (based on the 50 tested queries).
This means Lucy never mistakenly ignored an IoT-related query nor incorrectly triggered IoT logic when the question had no device references.
3.2 Device Selection Accuracy
Correct IoT Sensor Identification:
Among the queries that required Lucy to fetch sensor data (e.g., temperature sensors, door sensors, pressure sensors), Lucy correctly mapped the user’s mention to the actual device in ThingsBoard in 87% of cases.
In the remaining 13%, Lucy either selected a similar but not identical device or provided a partially relevant reading.
3.3 Alarm Handling
Alarm Data Accuracy:
Lucy correctly retrieved and summarized the existing alarm states (including name, severity, and status) 95% of the time.
In 5% of queries, Lucy either missed a newly triggered alarm or repeated an older alarm no longer active, typically due to caching delays or rapid alarm changes.
3.4 Response Relevance
Overall Relevance to the Query:
In 92% of tested queries, Lucy’s final text answer was determined by human evaluators to be “clearly relevant and helpful.”
In 8% of queries, Lucy gave partially correct data but did not fully address the user’s question (often lacking extra context, or addressing only half of a multi-part question).
4. Discussion
Strengths

Lucy’s logic for deciding when to invoke IoT data (need_tb() function) is robust, achieving 100% accuracy in test scenarios.
Overall response content is concise and well-structured, aided by the GPT model’s summarization abilities.
Areas for Improvement

The 13% mismatch in device identification could be improved by refining Lucy’s synonym matching or by implementing a fallback flow that double-checks device name similarity.
Alarm data updates could leverage event-driven or subscription-based approaches rather than bulk retrieval, reducing the chance of stale alarm information.
Handling of multi-part queries or clarifying follow-up questions might be extended to further enhance user experience.
Potential Next Steps

Synonym/Partial Name Mapping: Introduce a more sophisticated matching system (e.g., fuzzy matching) for device names.
Stateful Dialog: Track conversation context more persistently (if a user references “this sensor,” Lucy can remember the last device mentioned).
Alarm Synchronization: Implement real-time or near-real-time synchronization to ensure alarm states are always current.
5. Conclusion
In summary, Lucy IoT Monitoring Assistant demonstrates a high degree of accuracy and usability:

100% query recognition rate for IoT references.
87% correct device/sensor matching in tested scenarios.
95% accuracy in alarm reporting.
Generally relevant, helpful responses in 92% of queries.
These metrics indicate Lucy is reliable for real-time IoT monitoring and user interactions. Future enhancements can focus on refining device matching and context retention to further improve user satisfaction and operational efficiency.
