from pydantic import BaseModel, Field
from google import genai
from google.genai import types
import os
import chainlit as cl
GOOGLE_AI_API = os.environ.get("GEMINI_API_KEY")

class SearchInput(BaseModel):
    query: str = Field(..., description="Search query from user")

class SearchOutput(BaseModel):
    result: str = Field(...,description="Search results containing content that will be displayed to the user")

def search_web(input: SearchInput) -> SearchOutput:
    # Configure the client
    client = genai.Client(api_key=GOOGLE_AI_API)

    # Define the grounding tool
    grounding_tool = types.Tool(
        google_search=types.GoogleSearch()
    )

    # Configure generation settings
    config = types.GenerateContentConfig(
        tools=[grounding_tool]
    )

    # Configure generation settings
    config = types.GenerateContentConfig(
        tools=[grounding_tool]
    )

    # Make the request
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=input.query,
        config=config,
    )

    return SearchOutput(result=response.text)

def create_search_web_tool():
    """
    Create a search web tool function that searches predefined URLs based on user query.

    Returns:
        A function that takes a SearchInput and returns a SearchOutput.
    """

    @cl.step(type="tools")
    async def configured_search_web_tool(input: SearchInput) -> SearchOutput:
        return search_web(input)

    return configured_search_web_tool