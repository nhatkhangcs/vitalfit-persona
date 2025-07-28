from typing import Optional
from pydantic import BaseModel, Field
import datetime
import chainlit as cl
from google.oauth2 import service_account
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
import os

CLIENT_SECRET_FILE = "credentials.json"
API_NAME = "calendar"
API_VERSION = "v3"
SCOPES = ['https://www.googleapis.com/auth/calendar']


class CalendarEventInput(BaseModel):
    summary: str = Field(..., description="Event title")
    description: Optional[str] = Field(None, description="Event description")
    start_time: str = Field(
        ..., description="Start time in RFC3339 format. Default year is 2025, if not specified")
    end_time: str = Field(
        ..., description="End time in RFC3339 format. Default year is 2025, if not specified")
    calendar_id: str = Field("primary", description="Google Calendar ID")


class CalendarEventOutput(BaseModel):
    success: bool
    event_id: Optional[str] = None
    message: str


def create_event(input: CalendarEventInput) -> CalendarEventOutput:
    try:
        print(f"Creating calendar event with input: {input}")
        creds = None

        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    CLIENT_SECRET_FILE, SCOPES)
                creds = flow.run_local_server(
                    port=8080, access_type='offline', prompt='consent')
                with open('token.json', 'w') as token:
                    token.write(creds.to_json())

        service = build(API_NAME, API_VERSION, credentials=creds)
        # Convert start_time and end_time to datetime objects
        start_time = datetime.datetime.fromisoformat(
            input.start_time.replace("Z", "+00:00"))
        end_time = datetime.datetime.fromisoformat(
            input.end_time.replace("Z", "+00:00"))
        event = {
            'summary': input.summary,
            'description': input.description,
            'start': {
                'dateTime': start_time.isoformat(),
                'timeZone': 'Asia/Ho_Chi_Minh',
            },
            'end': {
                'dateTime': end_time.isoformat(),
                'timeZone': 'Asia/Ho_Chi_Minh',
            },
        }
        print(f"Creating event: {event}")
        created_event = service.events().insert(
            calendarId=input.calendar_id, body=event).execute()
        print(f"Event created: {created_event.get('htmlLink')}")
        return CalendarEventOutput(success=True, event_id=created_event['id'], message="Event created successfully")
    except Exception as e:
        print(f"Error creating calendar event: {e}")
        return CalendarEventOutput(success=False, message=str(e))


def create_calendar_event_tool():
    """Create event by Google Calendar API

    Args:
        input (CalendarEventInput): User's event description

    Returns:
        CalendarEventOutput: Event's status description
    """

    @cl.step(type="tools")
    async def calendar_event_tool(input: CalendarEventInput) -> CalendarEventOutput:
        return create_event(input)

    return calendar_event_tool
