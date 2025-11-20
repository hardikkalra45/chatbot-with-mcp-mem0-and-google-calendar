# google_calendar_client.py
import datetime as dt
import os.path
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/calendar"]


class GoogleCalendarClient:
    """Google Calendar API client with enhanced functionality for chatbot integration"""
    
    def __init__(self, credentials_file: str = "D:/assignment/assignment/credentials.json", token_file: str = "token.json"):
        """
        Initialize the Google Calendar client
        
        Args:
            credentials_file: Path to the credentials JSON file
            token_file: Path to the token storage file
        """
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.creds = None
        self.service = None
        self.authenticated = False
        
    def authenticate(self) -> bool:
        """Authenticate with Google Calendar API"""
        try:
            # The file token.json stores the user's access and refresh tokens, and is
            # created automatically when the authorization flow completes for the first time.
            if os.path.exists(self.token_file):
                self.creds = Credentials.from_authorized_user_file(self.token_file, SCOPES)
            
            # If there are no (valid) credentials available, let the user log in.
            if not self.creds or not self.creds.valid:
                if self.creds and self.creds.expired and self.creds.refresh_token:
                    self.creds.refresh(Request())
                else:
                    if not os.path.exists(self.credentials_file):
                        raise FileNotFoundError(
                            f"Credentials file '{self.credentials_file}' not found. "
                            "Please download it from Google Cloud Console."
                        )
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_file, SCOPES
                    )
                    self.creds = flow.run_local_server(port=0)
                
                # Save the credentials for the next run
                with open(self.token_file, "w") as token:
                    token.write(self.creds.to_json())

            self.service = build("calendar", "v3", credentials=self.creds)
            self.authenticated = True
            return True
            
        except Exception as e:
            print(f"Authentication failed: {e}")
            self.authenticated = False
            return False
    
    def get_upcoming_events(self, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Get upcoming events from the user's calendar
        
        Args:
            max_results: Maximum number of events to return
            
        Returns:
            List of event dictionaries
        """
        if not self.authenticated:
            if not self.authenticate():
                return []
        
        try:
            now = datetime.now(tz=dt.timezone.utc).isoformat()
            
            events_result = (
                self.service.events()
                .list(
                    calendarId="en.indian#holiday@group.v.calendar.google.com",
                    timeMin=now,
                    maxResults=max_results,
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )
            
            events = events_result.get("items", [])
            return self._parse_events(events)
            
        except HttpError as error:
            print(f"An error occurred: {error}")
            return []
    
    def get_events_for_date(self, target_date: datetime, max_results: int = 50) -> List[Dict[str, Any]]:
        """
        Get events for a specific date
        
        Args:
            target_date: The date to get events for
            max_results: Maximum number of events to return
            
        Returns:
            List of event dictionaries for the specified date
        """
        if not self.authenticated:
            if not self.authenticate():
                return []
        
        try:
            # Set time range for the entire day
            start_of_day = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_day = start_of_day + timedelta(days=1)
            
            time_min = start_of_day.isoformat() + 'Z'
            time_max = end_of_day.isoformat() + 'Z'
            
            events_result = (
                self.service.events()
                .list(
                    calendarId="primary",
                    timeMin=time_min,
                    timeMax=time_max,
                    maxResults=max_results,
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )
            
            events = events_result.get("items", [])
            return self._parse_events(events)
            
        except HttpError as error:
            print(f"An error occurred: {error}")
            return []
    
    def get_events_for_date_range(self, start_date: datetime, end_date: datetime, max_results: int = 100) -> List[Dict[str, Any]]:
        """
        Get events for a date range
        
        Args:
            start_date: Start of the date range
            end_date: End of the date range
            max_results: Maximum number of events to return
            
        Returns:
            List of event dictionaries for the specified range
        """
        if not self.authenticated:
            if not self.authenticate():
                return []
        
        try:
            time_min = start_date.isoformat() + 'Z'
            time_max = end_date.isoformat() + 'Z'
            
            events_result = (
                self.service.events()
                .list(
                    calendarId="primary",
                    timeMin=time_min,
                    timeMax=time_max,
                    maxResults=max_results,
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )
            
            events = events_result.get("items", [])
            return self._parse_events(events)
            
        except HttpError as error:
            print(f"An error occurred: {error}")
            return []
    
    def get_todays_events(self) -> List[Dict[str, Any]]:
        """Get today's events"""
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        return self.get_events_for_date(today)
    
    def get_weekly_events(self) -> List[Dict[str, Any]]:
        """Get events for the current week"""
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_week = today + timedelta(days=7)
        return self.get_events_for_date_range(today, end_of_week)
    
    def get_event_details(self, event_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific event
        
        Args:
            event_id: The ID of the event to retrieve
            
        Returns:
            Event dictionary or None if not found
        """
        if not self.authenticated:
            if not self.authenticate():
                return None
        
        try:
            event = self.service.events().get(calendarId='primary', eventId=event_id).execute()
            return self._parse_single_event(event)
            
        except HttpError as error:
            print(f"An error occurred: {error}")
            return None
    
    def search_events(self, query: str, max_results: int = 20) -> List[Dict[str, Any]]:
        """
        Search events by keyword
        
        Args:
            query: Search query string
            max_results: Maximum number of events to return
            
        Returns:
            List of matching event dictionaries
        """
        if not self.authenticated:
            if not self.authenticate():
                return []
        
        try:
            now = datetime.now(tz=dt.timezone.utc).isoformat()
            
            events_result = (
                self.service.events()
                .list(
                    calendarId="primary",
                    timeMin=now,
                    maxResults=max_results,
                    singleEvents=True,
                    orderBy="startTime",
                    q=query  # Search query
                )
                .execute()
            )
            
            events = events_result.get("items", [])
            return self._parse_events(events)
            
        except HttpError as error:
            print(f"An error occurred: {error}")
            return []
    
    def get_free_busy_info(self, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """
        Get free/busy information for a time period
        
        Args:
            start_time: Start of the time period
            end_time: End of the time period
            
        Returns:
            Free/busy information dictionary
        """
        if not self.authenticated:
            if not self.authenticate():
                return {}
        
        try:
            body = {
                "timeMin": start_time.isoformat() + 'Z',
                "timeMax": end_time.isoformat() + 'Z',
                "items": [{"id": "primary"}]
            }
            
            free_busy_result = self.service.freebusy().query(body=body).execute()
            return free_busy_result
            
        except HttpError as error:
            print(f"An error occurred: {error}")
            return {}
    
    def get_calendar_list(self) -> List[Dict[str, Any]]:
        """
        Get list of available calendars
        
        Returns:
            List of calendar dictionaries
        """
        if not self.authenticated:
            if not self.authenticate():
                return []
        
        try:
            calendar_list = self.service.calendarList().list().execute()
            return calendar_list.get('items', [])
            
        except HttpError as error:
            print(f"An error occurred: {error}")
            return []
    
    def _parse_events(self, events: List[Dict]) -> List[Dict[str, Any]]:
        """Parse raw events into a standardized format"""
        parsed_events = []
        
        for event in events:
            parsed_event = self._parse_single_event(event)
            if parsed_event:
                parsed_events.append(parsed_event)
        
        return parsed_events
    
    def _parse_single_event(self, event: Dict) -> Dict[str, Any]:
        """Parse a single event into a standardized format"""
        try:
            # Parse start and end times
            start = event["start"].get("dateTime", event["start"].get("date"))
            end = event["end"].get("dateTime", event["end"].get("date"))
            
            # Convert to datetime objects if they contain time information
            start_dt = None
            end_dt = None
            
            if 'T' in start:
                start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
            else:
                start_dt = datetime.fromisoformat(start)
                
            if 'T' in end:
                end_dt = datetime.fromisoformat(end.replace('Z', '+00:00'))
            else:
                end_dt = datetime.fromisoformat(end)
            
            # Parse attendees
            attendees = []
            for attendee in event.get('attendees', []):
                attendees.append({
                    'email': attendee.get('email'),
                    'name': attendee.get('displayName'),
                    'response_status': attendee.get('responseStatus')
                })
            
            # Create standardized event dictionary
            parsed_event = {
                'id': event['id'],
                'title': event.get('summary', 'No Title'),
                'description': event.get('description', ''),
                'start_time': start,
                'end_time': end,
                'start_datetime': start_dt,
                'end_datetime': end_dt,
                'location': event.get('location', ''),
                'attendees': attendees,
                'organizer': event.get('organizer', {}).get('email', ''),
                'status': event.get('status', 'confirmed'),
                'html_link': event.get('htmlLink', ''),
                'created': event.get('created', ''),
                'updated': event.get('updated', ''),
                'is_all_day': 'date' in event['start']  # All-day event if date field is used
            }
            
            return parsed_event
            
        except Exception as e:
            print(f"Error parsing event: {e}")
            return None
    
    def format_events_for_display(self, events: List[Dict[str, Any]]) -> str:
        """
        Format events into a human-readable string
        
        Args:
            events: List of event dictionaries
            
        Returns:
            Formatted string of events
        """
        if not events:
            return "No events found."
        
        formatted = []
        for i, event in enumerate(events, 1):
            # Format time
            if event['is_all_day']:
                time_str = "All day"
            else:
                start_dt = event['start_datetime']
                time_str = start_dt.strftime("%I:%M %p")
            
            # Format event line
            event_line = f"{i}. **{event['title']}** - {time_str}"
            
            if event['location']:
                event_line += f" (📍 {event['location']})"
            
            formatted.append(event_line)
        
        return "\n".join(formatted)
    
    def get_todays_meetings_formatted(self) -> str:
        """Get today's meetings in a formatted string"""
        events = self.get_todays_events()
        return self.format_events_for_display(events)
    
    def get_weekly_schedule_formatted(self) -> str:
        """Get weekly schedule in a formatted string"""
        events = self.get_weekly_events()
        
        if not events:
            return "No events scheduled for this week."
        
        # Group events by day
        events_by_day = {}
        for event in events:
            event_date = event['start_datetime'].strftime("%Y-%m-%d")
            if event_date not in events_by_day:
                events_by_day[event_date] = []
            events_by_day[event_date].append(event)
        
        # Format by day
        formatted = []
        for date in sorted(events_by_day.keys()):
            day_events = events_by_day[date]
            day_name = day_events[0]['start_datetime'].strftime("%A, %B %d")
            
            formatted.append(f"**{day_name}:**")
            for event in sorted(day_events, key=lambda x: x['start_datetime']):
                time_str = event['start_datetime'].strftime("%I:%M %p")
                formatted.append(f"  • {time_str} - {event['title']}")
            formatted.append("")
        
        return "\n".join(formatted)
    
    def is_available(self, start_time: datetime, end_time: datetime) -> bool:
        """
        Check if the user is available during a time period
        
        Args:
            start_time: Start of time period to check
            end_time: End of time period to check
            
        Returns:
            True if available, False if busy
        """
        free_busy = self.get_free_busy_info(start_time, end_time)
        
        if not free_busy or 'calendars' not in free_busy:
            return True
        
        calendar_busy = free_busy['calendars'].get('primary', {})
        busy_slots = calendar_busy.get('busy', [])
        
        # If there are no busy slots, the user is available
        return len(busy_slots) == 0
    
    def get_next_free_slot(self, duration_minutes: int = 60) -> Optional[datetime]:
        """
        Find the next available time slot of specified duration
        
        Args:
            duration_minutes: Duration of the required slot in minutes
            
        Returns:
            Start time of the next available slot, or None if not found
        """
        now = datetime.now()
        check_end = now + timedelta(days=7)  # Look ahead 7 days
        
        # Check in 30-minute increments
        current_check = now.replace(second=0, microsecond=0)
        if current_check.minute < 30:
            current_check = current_check.replace(minute=30)
        else:
            current_check = current_check.replace(hour=current_check.hour + 1, minute=0)
        
        while current_check < check_end:
            slot_end = current_check + timedelta(minutes=duration_minutes)
            
            if self.is_available(current_check, slot_end):
                return current_check
            
            # Move to next potential slot (next hour)
            current_check += timedelta(hours=1)
        
        return None


# Standalone functions for backward compatibility
def main():
    """Shows basic usage of the Google Calendar API.
    Prints the start and name of the next 10 events on the user's calendar.
    """
    client = GoogleCalendarClient()
    
    if client.authenticate():
        events = client.get_upcoming_events(10)
        
        if not events:
            print("No upcoming events found.")
            return

        # Prints the start and name of the next 10 events
        for event in events:
            start = event["start_time"]
            print(f"{start} - {event['title']}")


if __name__ == "__main__":
    main()