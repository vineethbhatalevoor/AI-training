import re
import csv
import json
from datetime import datetime, timedelta
from typing import List, Dict, Union
from boltiotai import openai
from google.colab import files
import os

# Access the API key from Google Colab secrets
openai.api_key = os.getenv('OPENAI_API_KEY')

class Event:
    def __init__(self, title: str, date: str, description: str):
        self.title = title
        self.date = datetime.strptime(date, "%Y-%m-%d")
        self.description = description

    def __repr__(self):
        return f"Event(title={self.title}, date={self.date.strftime('%Y-%m-%d')}, description={self.description})"

def load_events_from_csv(file_path: str) -> List[Event]:
    events = []
    with open(file_path, mode='r', encoding='utf-8-sig') as file:
        reader = csv.DictReader(file)
        for row in reader:
            events.append(Event(row['title'], row['date'], row['description']))
    return events

def load_events_from_json(file_path: str) -> List[Event]:
    events = []
    with open(file_path, mode='r', encoding='utf-8') as file:
        data = json.load(file)
        for item in data:
            events.append(Event(item['title'], item['date'], item['description']))
    return events

def index_events_by_date(events: List[Event]) -> Dict[str, List[Event]]:
    indexed_events = {}
    for event in events:
        date_str = event.date.strftime('%Y-%m-%d')
        if date_str not in indexed_events:
            indexed_events[date_str] = []
        indexed_events[date_str].append(event)
    return indexed_events

def display_events(events: List[Event]):
    print("Event Name | Event Date")
    print("-" * 34)
    for event in events:
        print(f"{event.title} | {event.date.strftime('%Y-%m-%d')}")

def get_events_for_date(indexed_events: Dict[str, List[Event]], date: datetime) -> List[Event]:
    date_str = date.strftime('%Y-%m-%d')
    return indexed_events.get(date_str, [])

def parse_date(date_str: str) -> Union[datetime, None]:
    try:
        return datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        return None

def generate_response(events: List[Event], query_date: datetime) -> str:
    if not events:
        return f"No events scheduled for {query_date.strftime('%Y-%m-%d')}."
    
    event_details = "\n".join([f"{event.title} on {event.date.strftime('%Y-%m-%d')}" for event in events])
    prompt = f"The following events are scheduled for {query_date.strftime('%Y-%m-%d')}:\n{event_details}\n\nPlease provide a summary:"
    
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ]
    )

    # Debug: Print the full response object
    print("Full response object:")
    print(response)

    # Extract and return the content of the response
    if 'choices' in response:
        return response['choices'][0].get('message', {}).get('content', response['choices'][0].get('text', '')).strip()
    else:
        return "Unexpected response format. Please check the debug output."

def interpret_query(user_query: str) -> Union[datetime, None]:
    user_query = user_query.lower()
    if "tomorrow" in user_query:
        return datetime.now() + timedelta(days=1)
    elif "today" in user_query:
        return datetime.now()
    else:
        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', user_query)
        if date_match:
            return parse_date(date_match.group(1))
        return None

def main():
    uploaded = files.upload()
    events = []
    for filename in uploaded.keys():
        if filename.endswith('.csv'):
            events = load_events_from_csv(filename)
        elif filename.endswith('.json'):
            events = load_events_from_json(filename)
        else:
            print("Unsupported file type.")
            return

    indexed_events = index_events_by_date(events)
    user_query = input("Enter your query (e.g., 'What events are scheduled tomorrow?' or 'What events are scheduled on YYYY-MM-DD?'): ").strip().lower()
    
    query_date = interpret_query(user_query)
    if not query_date:
        print("Unsupported query or invalid date format. Please try again.")
        return
    
    events_for_query = get_events_for_date(indexed_events, query_date)
    
    # Display events in the format: Event Name | Event Date
    if events_for_query:
        print("Event Name | Event Date")
        print("-" * 34)
        for event in events_for_query:
            print(f"{event.title} | {event.date.strftime('%Y-%m-%d')}")

    response = generate_response(events_for_query, query_date)
    print("Response:\n" + response)

if __name__ == "__main__":
    main()
