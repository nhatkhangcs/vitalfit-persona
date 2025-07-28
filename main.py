import os
import chainlit as cl
from src.llm.base import AgentClient
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai import BinaryContent
from pydantic_ai.providers.google_gla import GoogleGLAProvider
from src.utils.basetools.google_calendar_tool import create_calendar_event_tool
from PyPDF2 import PdfReader
from src.utils.basetools import healthMetric_tool, search_web_tool, sendEmail_tool
from src.data.cache.memory_handler import MessageMemoryHandler

provider = GoogleGLAProvider(api_key=os.getenv("GEMINI_API_KEY"))
model = GeminiModel("gemini-2.0-flash", provider=provider)

health_tool = healthMetric_tool.create_health_metric_tool()
web_tool = search_web_tool.create_search_web_tool()
email_tool = sendEmail_tool.create_send_email_tool()
calendar_tool = create_calendar_event_tool()

validated = False
memory_handler_user = MessageMemoryHandler(max_messages=15, port=6379)
memory_handler_other = MessageMemoryHandler(max_messages=15, port=6380)

with open(
    os.path.join(os.path.dirname(__file__), "config", "prompts", "valid.txt"),
    "r",
    encoding="utf-8",
) as f:
    VALIDATOR_PROMPT = f.read()
with open(
    os.path.join(os.path.dirname(__file__), "config", "prompts", "orchestrator.txt"),
    "r",
    encoding="utf-8",
) as f:
    ORCHESTRATOR_PROMPT = f.read()
with open(
    os.path.join(os.path.dirname(__file__), "config", "prompts", "nutrition.txt"),
    "r",
    encoding="utf-8",
) as f:
    NUTRITION_PROMPT = f.read()
with open(
    os.path.join(os.path.dirname(__file__), "config", "prompts", "schedule.txt"),
    "r",
    encoding="utf-8",
) as f:
    SCHEDULE_PROMPT = f.read()

nutrition_agent = AgentClient(
    model=model, system_prompt=NUTRITION_PROMPT, tools=[health_tool, web_tool]
).create_agent()

schedule_agent = AgentClient(
    model=model, system_prompt=SCHEDULE_PROMPT, tools=[email_tool, calendar_tool]
).create_agent()

validator_agent = AgentClient(
    model=model, system_prompt=VALIDATOR_PROMPT, tools=[]
).create_agent()

orchestrator_agent = AgentClient(
    model=model, system_prompt=ORCHESTRATOR_PROMPT, tools=[]
).create_agent()


@cl.action_callback("quit")
async def on_quit_action(action):
    await cl.Message(
        content="👋 **Bạn đã kết thúc phiên trò chuyện. Cảm ơn bạn đã sử dụng Hệ thống hỗ trợ ≈!**"
    ).send()
    global validated
    validated = False
    # reset memory
    await action.remove()
    await cl.Message(
        content=f"Server 6379: {memory_handler_user.clear_memory()}"
    ).send()
    await cl.Message(
        content=f"Server 6380: {memory_handler_other.clear_memory()}"
    ).send()


@cl.set_starters
async def set_starters():
    return [
        cl.Starter(
            label="Bắt đầu trò chuyện với Hệ thống hỗ trợ sức khoẻ",
            message="Bắt đầu trò chuyện với Hệ thống hỗ trợ sức khoẻ",
            icon="public/assets/thought-tool.png",
        )
    ]


@cl.on_message
async def main(message: cl.Message):
    await cl.Message(
        content="📝 **Loading past attachments**",
    ).send()

    full_msg = []
    text_in_pdf = "=== PDF Informaion Start (If any) ===\n"

    for file in message.elements:
        if "pdf" in file.mime:
            reader = PdfReader(file.path)
            number_of_pages = len(reader.pages)
            for idx in range(number_of_pages):
                page = reader.pages[idx]
                text = page.extract_text()
                text_in_pdf += text + "\n"

        if ("png" or "jpg" or "jpeg") in file.mime:
            # Read the image file as bytes
            with open(file.path, "rb") as image_file:
                image_bytes = image_file.read()

            # Determine the media type based on file extension
            file_extension = os.path.splitext(file.path)[1].lower()
            media_type = (
                "image/png"
                if file_extension == ".png"
                else "image/jpeg" if file_extension in (".jpg", ".jpeg") else None
            )

            memory_handler_user.store_user_message(BinaryContent(data=image_bytes, media_type=media_type))
            
            full_msg.append(BinaryContent(data=image_bytes, media_type=media_type))

    text_in_pdf += "=== PDF Informaion End ==="
    global validated

    print(text_in_pdf)

    temp_full_msg = full_msg

    memory_handler_user.store_user_message(text_in_pdf + "\n" + message.content)

    message_with_context_user = memory_handler_user.get_history_message()

    actions = [
        cl.Action(
            name="quit",
            label="❌ Kết thúc",
            tooltip="Kết thúc phiên trò chuyện",
            payload={},
        )
    ]

    try:
        if not validated:
            await cl.Message(
                content="📝 **Validator Agent đang xác thực thông tin của bạn...**",
            ).send()

            full_msg.append(
                f"{message_with_context_user}'\n'CURRENT QUESTION:'\n'{text_in_pdf}'\n'{message.content}"
            )

            response = await validator_agent.run(full_msg)
            memory_handler_user.store_bot_response(response.output)

            if "ok" in str(response.output).strip().lower():
                await cl.Message(
                    content="✅ **Thông tin đã được xác thực thành công!**\n Điều hướng đến Orchestrator Agent.",
                ).send()
                # save the context to a differentn memory handler
                validated = True

                orchestrator_response = await orchestrator_agent.run(full_msg)
                memory_handler_other.store_bot_response(orchestrator_response.output)

                full_msg = temp_full_msg

                full_msg.append(
                    message_with_context_user
                    + "\n"
                    + str(orchestrator_response).strip().lower()
                    + f"\nCURRENT QUESTION:\n{text_in_pdf}\n{message.content}"
                )

                if "nutrition" in str(orchestrator_response).strip().lower():
                    await cl.Message(
                        content="✅ **Đang điều hướng đến nutrition agent**",
                    ).send()
                    nutrition_response = await nutrition_agent.run(full_msg)
                    memory_handler_other.store_bot_response(nutrition_response.output)

                    await cl.Message(
                        content=f"{nutrition_response.output}", actions=actions
                    ).send()

                elif "schedule" in str(orchestrator_response).strip().lower():
                    await cl.Message(
                        content="✅ **Đang điều hướng đến schedule agent**",
                    ).send()
                    schedule_response = await schedule_agent.run(full_msg)
                    memory_handler_other.store_bot_response(schedule_response.output)

                    await cl.Message(
                        content=f"{schedule_response.output}", actions=actions
                    ).send()

                else:
                    await cl.Message(
                        content=str(orchestrator_response.output), actions=actions
                    ).send()

            else:
                await cl.Message(content=str(response.output), actions=actions).send()

        else:
            await cl.Message(
                content="🔄 **Tôi đang xử lý thông tin của bạn...**",
            ).send()

            memory_handler_other.store_user_message(message.content)
            message_with_context_other = memory_handler_other.get_history_message()

            full_msg = temp_full_msg
            full_msg.append(
                message_with_context_user
                + "\n"
                + message_with_context_other
                + f"\nCURRENT QUESTION:\n{text_in_pdf}\n{message.content}"
            )

            orchestrator_response = await orchestrator_agent.run(full_msg)
            memory_handler_other.store_bot_response(orchestrator_response.output)

            full_msg = temp_full_msg
            full_msg.append(
                message_with_context_user
                + "\n"
                + message_with_context_other
                + str(orchestrator_response).strip().lower()
                + f"\nCURRENT QUESTION:\n{text_in_pdf}\n{message.content}"
            )

            # redirect to appropriate agents
            if "nutrition" in str(orchestrator_response).strip().lower():
                await cl.Message(
                    content="✅ **Đang điều hướng đến nutrition agent**",
                ).send()
                nutrition_response = await nutrition_agent.run(full_msg)
                memory_handler_other.store_bot_response(nutrition_response.output)
                await cl.Message(
                    content=f"{nutrition_response.output}", actions=actions
                ).send()

            elif "schedule" in str(orchestrator_response).strip().lower():
                await cl.Message(
                    content="✅ **Đang điều hướng đến schedule agent**",
                ).send()
                schedule_response = await schedule_agent.run(full_msg)
                memory_handler_other.store_bot_response(schedule_response.output)
                await cl.Message(
                    content=f"{schedule_response.output}", actions=actions
                ).send()

            else:
                await cl.Message(
                    content=str(orchestrator_response.output), actions=actions
                ).send()

    except Exception as e:
        await cl.Message(
            content=f"❌ **Lỗi:** {str(e)}\n\nVui lòng thử lại.", actions=actions
        ).send()
