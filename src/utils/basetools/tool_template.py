from pydantic import BaseModel
import chainlit as cl

class ToolInput(BaseModel):
    pass


class ToolOutput(BaseModel):
    pass


def my_tool(

) -> ToolOutput:
    """
    <tool description>
    Environment variables:
     (if any)
    """
    pass

def create_my_tool():
    """
    Create a tool function with <something>

    Args:
        

    Returns:
        
    """

    @cl.step(type="tools")
    async def configured_stool(input_data: ToolInput) -> ToolOutput:
        return my_tool(
 
        )

    return configured_stool
