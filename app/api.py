import base64
import datetime
import os
from io import BytesIO
from typing import List
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi import HTTPException
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from langchain.agents import AgentExecutor
from langchain.agents import create_tool_calling_agent
from langchain.agents.agent import RunnableAgent
from langchain_core.messages import AIMessage
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

from app.common import logger
from app.common import MODEL_AGENT
from app.common import OPENAI_API_KEY
from app.common import system_prompt
from app.common.structured_tools import StructuredTool
from app.common.unstructured_tools import UnstructuredTool

load_dotenv()

app = FastAPI()

# Get API keys from environment and split into list
API_KEYS = set(os.getenv("API_KEYS", "").split(","))


# HTTPS enforcement middleware for production
@app.middleware("http")
async def enforce_https(request: Request, call_next):
    if os.getenv("environment") == "production":
        if request.url.scheme != "https":
            return JSONResponse(
                status_code=403, content={"detail": "HTTPS is required in production"}
            )
    return await call_next(request)


# Configure CORS with more specific settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],  # Be more specific about methods
    allow_headers=["*"],
    max_age=3600,
)


# Add API key validation middleware
@app.middleware("http")
async def validate_api_key(request: Request, call_next):
    if request.url.path == "/api/health":
        return await call_next(request)

    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return JSONResponse(
            status_code=401, content={"detail": "Missing or invalid Authorization header"}
        )

    api_key = auth_header.split(" ")[1]
    if api_key not in API_KEYS:
        return JSONResponse(status_code=403, content={"detail": "Invalid API key"})

    return await call_next(request)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=422,
        content={"detail": "Invalid request format"},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred"},
    )


# Initialize the chat components
prompt_template = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt.format(date=datetime.datetime.now().strftime("%Y-%m-%d"))),
        ("placeholder", "{chat_history}"),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ]
)

llm = ChatOpenAI(
    model=MODEL_AGENT,
    api_key=OPENAI_API_KEY,
)

tools = [UnstructuredTool(), StructuredTool()]
runnable = create_tool_calling_agent(llm, tools, prompt_template)
agent = RunnableAgent(runnable=runnable)
agent_executor = AgentExecutor(
    agent=agent, tools=tools, verbose=True, return_intermediate_steps=True
)


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: List[Message]


class Image(BaseModel):
    base64: str
    caption: str


class ChatResponse(BaseModel):
    role: str
    content: str
    images: Optional[List[Image]] = None


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        # Extract the last user message and convert previous messages to chat history
        chat_history = []
        for msg in request.messages[:-1]:  # All messages except the last one
            if msg.role == "user":
                chat_history.append(HumanMessage(content=msg.content))
            elif msg.role == "assistant":
                chat_history.append(AIMessage(content=msg.content))

        # Get the last user message
        user_message = request.messages[-1].content

        # Prepare input for the agent
        input_ = {
            "chat_history": chat_history,
            "input": user_message,
        }

        # Execute the agent
        result = agent_executor.invoke(input=input_)

        # Process the result
        response_content = ""
        images = []

        if isinstance(result["output"], dict):
            response_content = result["output"]["result"]

            # Convert PIL images to base64 strings
            if "image" in result["output"]:
                for img in result["output"]["image"]:
                    buffered = BytesIO()
                    img.save(buffered, format="PNG")
                    img_base64 = base64.b64encode(buffered.getvalue()).decode()

                    caption = f"{img.info['file_name']} - Page {img.info['page']}"
                    images.append(Image(base64=img_base64, caption=caption))

        else:
            response_content = result["output"]

        return ChatResponse(
            role="assistant", content=response_content, images=images if images else None
        )

    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Make the health check more informative
@app.get("/api/health")
async def health_check():
    try:
        # Add any critical dependencies check here
        return {"status": "healthy", "timestamp": datetime.datetime.now().isoformat()}
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JSONResponse(status_code=503, content={"status": "unhealthy", "detail": str(e)})
