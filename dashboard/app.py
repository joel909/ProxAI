import asyncio
import os
from pathlib import Path

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from inputs.terminal_ui import (
    WRITE_CONFIRM_DENY,
    WRITE_CONFIRM_YES,
    reset_permission_handler,
    set_permission_handler,
)
from openAI_manager import OpenAIManager
from openAI_manager.request_llm_reply_with_tools_list import build_input_messages
from setup_flow.fetch_config_files import fetch_config_file
from storage import ChatHistoryManager
from storage.get_provider_info import get_provider_info
from storage.conversations import get_conversation_messages, list_conversations


STATIC_DIR = Path(__file__).resolve().parent / "static"
TRUE_VALUES = {"1", "true", "yes"}


def _configured_allowed_emails():
    return {
        email.strip().casefold()
        for email in os.environ.get("PROXAI_ALLOWED_EMAILS", "").split(",")
        if email.strip()
    }


def access_denial(headers):
    require_access = os.environ.get(
        "PROXAI_REQUIRE_CLOUDFLARE_ACCESS", "false"
    ).casefold() in TRUE_VALUES
    jwt = headers.get("cf-access-jwt-assertion", "")
    email = headers.get("cf-access-authenticated-user-email", "").casefold()
    allowed_emails = _configured_allowed_emails()

    if require_access and not jwt:
        return "Cloudflare Access authentication is required."
    if allowed_emails and email not in allowed_emails:
        return "This Cloudflare Access identity is not allowed."
    return None


def _create_manager(conversation_id=None):
    providers = get_provider_info()
    if not providers:
        raise RuntimeError("No LLM provider is configured. Run the CLI setup first.")
    provider = providers[0]
    return OpenAIManager(
        provider.api_token,
        ChatHistoryManager(conversation_id=conversation_id),
        provider.default_model,
        provider.warning_token_limit,
    ), provider


def _permission_handler(auto_approve):
    def decide(**_request):
        return WRITE_CONFIRM_YES if auto_approve else WRITE_CONFIRM_DENY

    return decide


def _request_reply(manager, prompt, auto_approve, on_tool_call):
    previous_messages = get_conversation_messages(
        manager.chat_history_manager.conversation_id
    )

    def build_dashboard_messages(current_prompt, system_configuration):
        input_messages = build_input_messages(current_prompt, system_configuration)
        if previous_messages:
            input_messages[-1:-1] = previous_messages
        return input_messages

    token = set_permission_handler(_permission_handler(auto_approve))
    try:
        return manager.request_llm_reply(
            prompt,
            on_tool_call=on_tool_call,
            system_configuration=fetch_config_file(),
            custom_build_input_messages_function=build_dashboard_messages,
        )
    finally:
        reset_permission_handler(token)


app = FastAPI(title="ProxAI Dashboard", docs_url=None, redoc_url=None)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.middleware("http")
async def protect_dashboard(request: Request, call_next):
    denial = access_denial(request.headers)
    if denial:
        return JSONResponse({"error": denial}, status_code=401)
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    return response


@app.get("/")
async def dashboard():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/status")
async def status(request: Request):
    providers = get_provider_info()
    provider = providers[0] if providers else None
    return {
        "ready": provider is not None,
    }


@app.get("/api/conversations")
async def conversations():
    return {"conversations": list_conversations()}


@app.get("/api/conversations/{conversation_id}")
async def conversation(conversation_id: str):
    return {
        "id": conversation_id,
        "messages": get_conversation_messages(conversation_id),
    }


@app.websocket("/ws/chat")
async def chat(websocket: WebSocket):
    denial = access_denial(websocket.headers)
    if denial:
        await websocket.close(code=4401, reason=denial)
        return

    await websocket.accept()
    try:
        manager, provider = _create_manager()
    except Exception as exc:
        await websocket.send_json({"type": "error", "message": str(exc)})
        await websocket.close(code=1011)
        return

    await websocket.send_json(
        {
            "type": "session",
            "conversation_id": manager.chat_history_manager.conversation_id,
        }
    )
    loop = asyncio.get_running_loop()

    try:
        while True:
            payload = await websocket.receive_json()
            if payload.get("type") == "reset":
                manager, provider = _create_manager()
                await websocket.send_json(
                    {
                        "type": "reset_complete",
                        "conversation_id": manager.chat_history_manager.conversation_id,
                    }
                )
                continue
            if payload.get("type") == "select_conversation":
                conversation_id = str(payload.get("conversation_id", "")).strip()
                if not conversation_id:
                    continue
                messages = get_conversation_messages(conversation_id)
                if not messages:
                    await websocket.send_json(
                        {"type": "error", "message": "Conversation was not found."}
                    )
                    continue
                manager, provider = _create_manager(conversation_id)
                await websocket.send_json(
                    {
                        "type": "history",
                        "conversation_id": conversation_id,
                        "messages": messages,
                    }
                )
                continue
            if payload.get("type") != "prompt":
                continue

            prompt = str(payload.get("prompt", "")).strip()
            if not prompt:
                continue
            auto_approve = bool(payload.get("auto_approve", False))
            await websocket.send_json({"type": "thinking"})

            def on_tool_call(tool_name, event="started"):
                loop.call_soon_threadsafe(
                    asyncio.create_task,
                    websocket.send_json(
                        {"type": "tool", "name": tool_name, "status": event}
                    ),
                )

            try:
                response = await asyncio.to_thread(
                    _request_reply,
                    manager,
                    prompt,
                    auto_approve,
                    on_tool_call,
                )
                await websocket.send_json(
                    {
                        "type": "response",
                        "content": response or "Request cancelled.",
                        "conversation_id": manager.chat_history_manager.conversation_id,
                    }
                )
            except Exception as exc:
                await websocket.send_json({"type": "error", "message": str(exc)})
    except WebSocketDisconnect:
        return
