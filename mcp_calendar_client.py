from typing import List, Optional
from datetime import datetime, timedelta

from pydantic import BaseModel, Field
from mcp.server.fastmcp import FastMCP
import logging

# configure module logger
logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)

# Import the calendar client
from calendar_tools import GoogleCalendarClient

# Initialize data stores
calendar_client = GoogleCalendarClient()

# Calendar Models
class DateInput(BaseModel):
    date: str = Field(description="Date in YYYY-MM-DD format")

class DateRangeInput(BaseModel):
    start_date: str = Field(description="Start date in YYYY-MM-DD format")
    end_date: str = Field(description="End date in YYYY-MM-DD format")

class SearchEventsInput(BaseModel):
    query: str = Field(description="Search query for events")
    max_results: int = Field(default=20, description="Maximum number of results")

class TimeSlotInput(BaseModel):
    start_time: str = Field(description="Start time in ISO format")
    end_time: str = Field(description="End time in ISO format")

class DurationInput(BaseModel):
    duration_minutes: int = Field(default=60, description="Duration in minutes")

# Initialize MCP server
server = FastMCP(name="personal-assistant")

# Authentication endpoint
@server.tool(name="authenticate_calendar", description="Authenticate with Google Calendar")
def authenticate_calendar() -> dict:
    """Authenticate with Google Calendar service"""
    try:
        success = calendar_client.authenticate()
        if success:
            return {"status": "success", "message": "Successfully authenticated with Google Calendar"}
        else:
            return {"status": "error", "message": "Failed to authenticate with Google Calendar"}
    except Exception as e:
        return {"status": "error", "message": f"Authentication error: {str(e)}"}

# Calendar Tools
@server.tool(name="get_todays_events", description="Get today's events and meetings")
def get_todays_events() -> dict:
    """Get all events scheduled for today"""
    try:
        if not calendar_client.authenticated:
            auth_result = calendar_client.authenticate()
            if not auth_result:
                return {"status": "error", "message": "Authentication required"}
        
        events = calendar_client.get_todays_events()
        formatted_events = calendar_client.format_events_for_display(events)
        
        return {
            "status": "success",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "events": events,
            "formatted_output": formatted_events
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to fetch today's events: {str(e)}"}

@server.tool(name="get_weekly_events", description="Get events for the current week")
def get_weekly_events() -> dict:
    """Get all events scheduled for the current week"""
    try:
        if not calendar_client.authenticated:
            auth_result = calendar_client.authenticate()
            if not auth_result:
                return {"status": "error", "message": "Authentication required"}
        
        formatted_schedule = calendar_client.get_weekly_schedule_formatted()
        events = calendar_client.get_weekly_events()
        logger.info(f"Weekly events retrieved: {events}")
        return {
            "status": "success",
            "period": "current_week",
            "events": events,
            "formatted_output": formatted_schedule
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to fetch weekly events: {str(e)}"}

@server.tool(name="get_events_for_date", description="Get events for a specific date")
def get_events_for_date(data: DateInput) -> dict:
    """Get events for a specific date (YYYY-MM-DD format)"""
    try:
        if not calendar_client.authenticated:
            auth_result = calendar_client.authenticate()
            if not auth_result:
                return {"status": "error", "message": "Authentication required"}
        
        target_date = datetime.strptime(data.date, "%Y-%m-%d")
        events = calendar_client.get_events_for_date(target_date)
        formatted_events = calendar_client.format_events_for_display(events)
        
        return {
            "status": "success",
            "date": data.date,
            "events": events,
            "formatted_output": formatted_events
        }
    except ValueError:
        return {"status": "error", "message": "Invalid date format. Please use YYYY-MM-DD"}
    except Exception as e:
        return {"status": "error", "message": f"Failed to fetch events: {str(e)}"}

@server.tool(name="get_upcoming_events", description="Get upcoming events")
def get_upcoming_events(data: Optional[dict] = None) -> dict:
    """Get upcoming events (default: next 10 events)"""
    try:
        if not calendar_client.authenticated:
            auth_result = calendar_client.authenticate()
            if not auth_result:
                return {"status": "error", "message": "Authentication required"}
        
        max_results = 10
        if data and 'max_results' in data:
            max_results = data['max_results']
        
        events = calendar_client.get_upcoming_events(max_results)
        formatted_events = calendar_client.format_events_for_display(events)
        
        return {
            "status": "success",
            "max_results": max_results,
            "events": events,
            "formatted_output": formatted_events
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to fetch upcoming events: {str(e)}"}

@server.tool(name="search_events", description="Search events by keyword")
def search_events(data: SearchEventsInput) -> dict:
    """Search events using keywords"""
    try:
        if not calendar_client.authenticated:
            auth_result = calendar_client.authenticate()
            if not auth_result:
                return {"status": "error", "message": "Authentication required"}
        
        events = calendar_client.search_events(data.query, data.max_results)
        formatted_events = calendar_client.format_events_for_display(events)
        
        return {
            "status": "success",
            "query": data.query,
            "events_found": len(events),
            "events": events,
            "formatted_output": formatted_events
        }
    except Exception as e:
        return {"status": "error", "message": f"Search failed: {str(e)}"}

@server.tool(name="check_availability", description="Check if user is available during a time slot")
def check_availability(data: TimeSlotInput) -> dict:
    """Check availability for a specific time period"""
    try:
        if not calendar_client.authenticated:
            auth_result = calendar_client.authenticate()
            if not auth_result:
                return {"status": "error", "message": "Authentication required"}
        
        start_time = datetime.fromisoformat(data.start_time)
        end_time = datetime.fromisoformat(data.end_time)
        
        is_available = calendar_client.is_available(start_time, end_time)
        
        return {
            "status": "success",
            "start_time": data.start_time,
            "end_time": data.end_time,
            "available": is_available,
            "message": "Available" if is_available else "Busy"
        }
    except Exception as e:
        return {"status": "error", "message": f"Availability check failed: {str(e)}"}

@server.tool(name="get_next_free_slot", description="Find the next available time slot")
def get_next_free_slot(data: DurationInput) -> dict:
    """Find the next available time slot of specified duration"""
    try:
        if not calendar_client.authenticated:
            auth_result = calendar_client.authenticate()
            if not auth_result:
                return {"status": "error", "message": "Authentication required"}
        
        next_slot = calendar_client.get_next_free_slot(data.duration_minutes)
        
        if next_slot:
            return {
                "status": "success",
                "duration_minutes": data.duration_minutes,
                "next_available_slot": next_slot.isoformat(),
                "message": f"Next available {data.duration_minutes}-minute slot: {next_slot.strftime('%Y-%m-%d %H:%M')}"
            }
        else:
            return {
                "status": "success",
                "duration_minutes": data.duration_minutes,
                "next_available_slot": None,
                "message": f"No available {data.duration_minutes}-minute slot found in the next 7 days"
            }
    except Exception as e:
        return {"status": "error", "message": f"Failed to find free slot: {str(e)}"}

@server.tool(name="get_calendar_status", description="Check calendar connection status")
def get_calendar_status() -> dict:
    """Check if calendar is connected and authenticated"""
    try:
        # Test authentication by trying to get calendar list
        calendars = calendar_client.get_calendar_list()
        
        return {
            "status": "success",
            "authenticated": calendar_client.authenticated,
            "calendars_accessible": len(calendars) > 0,
            "message": "Calendar connected successfully" if calendar_client.authenticated else "Calendar not authenticated"
        }
    except Exception as e:
        return {
            "status": "error",
            "authenticated": False,
            "message": f"Calendar connection error: {str(e)}"
        }
    
def main():
    server.run(transport='stdio')

if __name__ == "__main__":
    main()    