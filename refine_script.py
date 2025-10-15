from openai import OpenAI

client = OpenAI()  # Uses your saved API key

with open("C:\\Users\\Dylan\\Desktop\\Reminders\\DriveSummary\\drive_summary.py", "r", encoding="utf-8") as f:
    original_code = f.read()

prompt = f"""
Improve this DriveSummary script for reliability, API error handling, and efficiency.
Keep all features: TomTom routing, OpenWeather alerts, Ticketmaster events, and ntfy notifications.
Make sure it runs free after refinement (no OpenAI API calls in final version).
Code:
{original_code}
"""

response = client.responses.create(model="gpt-5", input=prompt)
print(response.output_text)