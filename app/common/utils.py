import base64
import datetime
import json
import os
import re
from typing import Dict
from typing import Iterable
from typing import List
from typing import Optional
from typing import Union

from dotenv import load_dotenv
from langchain.schema import Document
from openai import OpenAI

from app.common import logger
from app.common import system_prompt_structured_tool

load_dotenv()

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


def save_docs_to_jsonl(array: Iterable[Document], file_path: str) -> None:
    with open(file_path, "w") as jsonl_file:
        for doc in array:
            jsonl_file.write(doc.json() + "\n")


def load_docs_from_jsonl(file_path) -> Iterable[Document]:
    array = []
    with open(file_path) as jsonl_file:
        for line in jsonl_file:
            data = json.loads(line)
            obj = Document(**data)
            array.append(obj)
    return array


# Open the image file and encode it as a base64 string
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def extract_page_number(page_str: str) -> Optional[int]:
    """
    Extract page number from a string that may contain 'page' prefix or just a number.

    Args:
        page_str (str): String containing page number (e.g., 'page8', 'page51', '8', '51')

    Returns:
        Optional[int]: Extracted page number or None if invalid

    Examples:
        >>> extract_page_number('page8')
        8
        >>> extract_page_number('51')
        51
        >>> extract_page_number('invalid')
        None
    """
    # First try to extract number after 'page' prefix
    page_match = re.search(r"page(\d+)", page_str)
    if page_match:
        return int(page_match.group(1))

    # If no 'page' prefix found, check if the string is a number
    if page_str.isdigit():
        return int(page_str)

    return None


def metadata_filter_callable(
    companies: List[str] = None,
    quarters: List[str] = None,
    years: List[int] = None,
):
    "return a callable which takes as input the metadata dict of Document and return a bool"

    def callable_(metadata):
        if companies is not None and metadata["company"] not in companies:
            return False
        if quarters is not None and metadata["quarter"] not in quarters:
            return False
        if years is not None and metadata["year"] not in years:
            return False
        return True

    return callable_


def process_chat_completion(
    source_data: List[Dict[str, Union[int, str]]], user_query: str, model: str = "gpt-4o-mini"
) -> str:
    """
    Process chat completion with image data and return model response.

    Args:
        source_data (List[Dict]): List of dictionaries containing source data with image URLs
        user_query (str): User query to process
        model (str): Model name to use for completion

    Returns:
        str: Model response in JSON format
    """

    # Prepare the messages
    messages = [
        {
            "role": "system",
            "content": system_prompt_structured_tool.format(
                date=datetime.datetime.now().strftime("%Y-%m-%d")
            ),
        },
        {
            "role": "user",
            "content": [
                {"type": "text", "text": f"USER_QUERY: {user_query}"},
                {"type": "text", "text": "CONTEXT_SOURCES:"},
            ],
        },
    ]

    # Add image content to the user message
    for item in source_data:
        messages[1]["content"].append({"type": "text", "text": f"Image {item['index']}:"})
        messages[1]["content"].append(
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{item['context']}",
                    # "detail": "high"  # Using high detail for financial documents
                },
            }
        )

    response = client.chat.completions.create(
        model=model, messages=messages, temperature=0.0, response_format={"type": "json_object"}
    )

    logger.info(f"structured, tokens sent: {response.usage.prompt_tokens}")

    return response.choices[0].message.content


def get_base_64_string(string_path: str) -> str:
    with open(string_path) as f:
        return f.read()
