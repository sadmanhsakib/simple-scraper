"""
Module for extracting structural data from Markdown content using LLMs.

This module utilizes the Instructor library to enforce structured output (JSON)
via Pydantic models. It supports both local (Ollama) and remote (Groq) LLM backends.
"""

import os
import time
from typing import List, Optional, Tuple
import instructor
import tiktoken
from groq import Groq
from openai import OpenAI
from pydantic import BaseModel, HttpUrl
from dotenv import load_dotenv

load_dotenv()

LOCAL_MODEL_NAME = os.getenv("LOCAL_MODEL_NAME")
REMOTE_MODEL_NAME = os.getenv("REMOTE_MODEL_NAME")
API_KEY = os.getenv("API_KEY")

# Strict instructions to ensure the LLM focuses purely on data extraction
# and does not include conversational filler which could break JSON parsing.
SYSTEM_PROMPT = """
You are a data extraction assistant.
Respond ONLY with a valid JSON object. No explanation, no markdown fences.
Extract ONLY the download links.
"""


class Link(BaseModel):
    """Schema for a single extracted URL."""

    url: HttpUrl


class LinkCollection(BaseModel):
    """Container for multiple extracted links, used to enforce structured LLM output."""

    links: List[Link]


def main(is_local: bool = False) -> None:
    """
    Main execution flow for text parsing and data extraction.

    Loads scraped markdown, chunks it to fit within context limits,
    processes each chunk through the LLM, and exports the final results.
    """
    input_path = "data/webpage.md"
    if not os.path.exists(input_path):
        print(f"❌ Input file not found: {input_path}")
        return

    with open(input_path, "r", encoding="utf-8") as file:
        data = file.read()

    # Determine chunk size based on model context limits.
    # Remote models often handle larger contexts more efficiently.
    if is_local:
        chunks = chunk_text(data)
    else:
        chunks = chunk_text(data, max_tokens=6000)

    print(f"Total chunks to process: {len(chunks)}")

    client, model_name = initialize_client(is_local=is_local)
    all_links = []

    for i, chunk in enumerate(chunks):
        print(
            f"Processing chunk {i+1}/{len(chunks)} (Estimated tokens: {count_tokens(chunk)})"
        )
        results = generate_output(client=client, prompt=chunk, model_name=model_name)
        if results and results.links:
            all_links.extend(results.links)

    # Consolidate and export all extracted results to a persistent file.
    final_collection = LinkCollection(links=all_links)
    export_output(final_collection)


def initialize_client(is_local: bool) -> Tuple[instructor.Instructor, Optional[str]]:
    """
    Configures the API client and selects the appropriate model.

    If local, it connects to a local Ollama instance.
    If remote, it uses the Groq API for high-performance inference.
    """
    if is_local:
        # Connect to local Ollama server via OpenAI-compatible endpoint
        openai_client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
        client = instructor.from_openai(openai_client, mode=instructor.Mode.JSON)
        model_name = LOCAL_MODEL_NAME
    else:
        # Use Groq for faster remote execution
        client = instructor.from_groq(Groq(api_key=API_KEY), mode=instructor.Mode.JSON)
        model_name = REMOTE_MODEL_NAME

    return client, model_name


def generate_output(
    client: instructor.Instructor, prompt: str, model_name: str
) -> Optional[LinkCollection]:
    """
    Sends a prompt to the LLM and returns a structured Pydantic object.

    Enforces a strict schema using the Instructor library to ensure
    the output is always a valid LinkCollection.
    """
    if not model_name:
        print("⚠️ Model name not configured.")
        return None

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]

    # Temperature is set to 0.0 to ensure maximum consistency and
    # minimize 'hallucinations' in the extracted data.
    try:
        response, completion = client.chat.completions.create_with_completion(
            model=model_name,
            messages=messages,
            temperature=0.0,
            response_model=LinkCollection,
            max_tokens=8192,
            max_retries=0,  # retries should be 3 for production
        )

        print(
            f"Usage: P:{completion.usage.prompt_tokens} C:{completion.usage.completion_tokens} T:{completion.usage.total_tokens}"
        )
        return response
    except Exception as e:
        print(f"❌ Error during generation: {e}")
        return None


def export_output(results: LinkCollection) -> None:
    """
    Saves the extracted URLs to a text file.

    Outputs one URL per line to simplify integration with downstream
    tools like download managers or web crawlers.
    """
    output_path = "data/urls.txt"
    with open(output_path, "w", encoding="utf-8") as file:
        for link in results.links:
            file.write(str(link.url) + "\n")

    print(f"✅ Urls extracted successfully to {output_path}")


def count_tokens(text: str) -> int:
    """
    Estimates the number of tokens in a string using the tiktoken library.

    This is essential for monitoring API costs and ensuring that
    prompts stay within the model's maximum context window.
    """
    encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(text))


def chunk_text(text: str, max_tokens: int = 1500) -> List[str]:
    """
    Splits long text into smaller chunks based on token count.

    The chunking logic attempts to split at line breaks to preserve
    the structural context of the markdown content.
    """
    lines = text.splitlines()
    chunks = []
    current_chunk = []
    current_tokens = 0

    for line in lines:
        # Add 1 for the newline character that would be added back by join()
        line_tokens = count_tokens(line) + 1

        # Handle edge case where a single line exceeds the max tokens.
        if line_tokens > max_tokens:
            if current_chunk:
                chunks.append("\n".join(current_chunk))
                current_chunk = []
                current_tokens = 0
            chunks.append(line)
            continue

        if current_tokens + line_tokens > max_tokens:
            chunks.append("\n".join(current_chunk))
            current_chunk = [line]
            current_tokens = line_tokens
        else:
            current_chunk.append(line)
            current_tokens += line_tokens

    if current_chunk:
        chunks.append("\n".join(current_chunk))

    return chunks


if __name__ == "__main__":
    start_time = time.time()
    main()
    print(f"✅ Run Time is {time.time() - start_time:.2f} seconds")
