import csv
import json
from datetime import datetime, timedelta
from typing import List, Dict, Union
import openai

# Define your OpenAI API key here
openai.api_key = 'YOUR_OPENAI_API_KEY'

# Define a class to represent an event
class Event:
    def __init__(self, title: str, date: str, description: str):
        self.title = title
        self.date = datetime.strptime(date, "%Y-%m-%d")
        self.description = description

    def __repr__(self):
        return f"Event(title={self.title}, date={self.date.strftime('%Y-%m-%d')}, description={self.description})"

# Function to load events from a CSV file
def load_events_from_csv(file_path: str) -> List[Event]:
    events = []
    with open(file_path, mode='r', encoding='utf-8-sig') as file:
        reader = csv.DictReader(file)
        for row in reader:
            events.append(Event(row['title'], row['date'], row['description']))
    return events

# Function to load events from a JSON file
def load_events_from_json(file_path: str) -> List[Event]:
    events = []
    with open(file_path, mode='r', encoding='utf-8') as file:
        data = json.load(file)
        for item in data:
            events.append(Event(item['title'], item['date'], item['description']))
    return events

# Function to index events by date
def index_events_by_date(events: List[Event]) -> Dict[str, List[Event]]:
    indexed_events = {}
    for event in events:
        date_str = event.date.strftime('%Y-%m-%d')
        if date_str not in indexed_events:
            indexed_events[date_str] = []
        indexed_events[date_str].append(event)
    return indexed_events

# Function to display events in a calendar-like output
def display_events(events: List[Event]):
    print("Event Name | Event Date")
    print("-" * 34)
    for event in events:
        print(f"{event.title} | {event.date.strftime('%Y-%m-%d')}")

# Function to get events for a specific date
def get_events_for_date(indexed_events: Dict[str, List[Event]], date: datetime) -> List[Event]:
    date_str = date.strftime('%Y-%m-%d')
    return indexed_events.get(date_str, [])

# Function to parse a date string in the format YYYY-MM-DD
def parse_date(date_str: str) -> Union[datetime, None]:
    try:
        return datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        return None

# Function to generate a response using GPT-3 based on retrieved events
def generate_response(events: List[Event], query_date: datetime) -> str:
    if not events:
        return f"No events scheduled for {query_date.strftime('%Y-%m-%d')}."
    
    event_details = "\n".join([f"{event.title} on {event.date.strftime('%Y-%m-%d')}" for event in events])
    prompt = f"The following events are scheduled for {query_date.strftime('%Y-%m-%d')}:\n{event_details}\n\nPlease provide a summary:"
    
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        max_tokens=150
    )
    
    return response.choices[0].text.strip()

# Main function to handle user queries
def main():
    # Load events from a file (CSV or JSON)
    events = load_events_from_csv('events.csv') # Replace with 'events.json' for JSON file
    # events = load_events_from_json('events.json') # Uncomment for JSON file

    # Index events by date
    indexed_events = index_events_by_date(events)

    # Handle user query
    user_query = input("Enter your query (e.g., 'What events are scheduled tomorrow?' or 'What events are scheduled on YYYY-MM-DD?'): ").strip().lower()
    if "tomorrow" in user_query:
        query_date = datetime.now() + timedelta(days=1)
    else:
        # Extract date from the query
        date_str = user_query.split("on")[-1].strip()
        query_date = parse_date(date_str)
        if not query_date:
            print("Unsupported query or invalid date format. Please try again.")
            return

    # Retrieve relevant events
    events_for_query = get_events_for_date(indexed_events, query_date)

    # Generate a response
    response = generate_response(events_for_query, query_date)
    print(response)

if __name__ == "__main__":
    main()