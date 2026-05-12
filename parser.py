import os, time
import instructor, tiktoken
from groq import Groq
from openai import OpenAI
from pydantic import BaseModel, HttpUrl
from typing import List
from dotenv import load_dotenv

load_dotenv()

LOCAL_MODEL_NAME = os.getenv("LOCAL_MODEL_NAME")
REMOTE_MODEL_NAME = os.getenv("REMOTE_MODEL_NAME")
base_url = os.getenv("BASE_URL")
api_key = os.getenv("API_KEY")

# Use strict JSON output to avoid parsing errors with structured data extraction
SYSTEM_PROMPT = """
You are a data extraction assistant.
Extract lead information from the given content.
Respond ONLY with a valid JSON object. No explanation, no markdown fences.
Extract ONLY the download links.
"""


class Link(BaseModel):
    url: HttpUrl


class LinkCollection(BaseModel):
    links: List[Link]


def main():
    with open("data.md", "r") as file:
        data = file.read()

    print(f"Estimated Tokens for the message: {count_tokens(SYSTEM_PROMPT + data)}")

    client, model_name = initialize_client(is_local=True)
    results = generate_output(client=client, prompt=data, model_name=model_name)
    export_output(results)


def initialize_client(is_local: bool) -> tuple[instructor.core.client.Instructor, str]:
    if is_local:
        openai_client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
        client = instructor.from_openai(openai_client, mode=instructor.Mode.JSON)
        
        model_name = LOCAL_MODEL_NAME
    else:
        client = instructor.from_groq(Groq(api_key=api_key), mode=instructor.Mode.JSON)
        model_name = REMOTE_MODEL_NAME

    return client, model_name


def generate_output(
    client: instructor.core.client.Instructor, prompt: str, model_name: str
) -> LinkCollection:
    if not model_name:
        return

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]

    # Use structured output to ensure valid JSON and automatic parsing
    response, completion = client.chat.completions.create_with_completion(
        model=model_name,
        messages=messages,
        temperature=0.0,  # Deterministic output for consistent extraction
        response_model=LinkCollection,
        max_tokens=8192,
        max_retries=0,
    )

    print("Prompt tokens:", completion.usage.prompt_tokens)
    print("Completion tokens:", completion.usage.completion_tokens)
    print("Total tokens:", completion.usage.total_tokens)

    return response


def export_output(results: LinkCollection):
    # Export URLs one per line for easier downstream processing
    with open("urls.txt", "w") as file:
        for link in results.links:
            file.writelines(str(link.url) + "\n")

    print("✅ Urls extracted successfully to urls.txt")


def count_tokens(text: str) -> int:
    # Estimate token count for cost monitoring and API limits
    encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(text))


if __name__ == "__main__":
    start_time = time.time()
    main()
    print(f"✅ Run Time is {time.time() - start_time:.2f} seconds")
