import os
import instructor
from groq import Groq
from pydantic import BaseModel, HttpUrl
from typing import List
from dotenv import load_dotenv

# Load environment variables from a .env file (e.g., API keys, model names)
load_dotenv()

# Retrieve necessary configuration from environment variables
model_name = os.getenv("MODEL_NAME")
base_url = os.getenv("BASE_URL")
api_key = os.getenv("API_KEY")

# Initialize the Instructor client with Groq as the LLM backend.
# The 'from_groq' method wraps the standard Groq client to add support
# for returning structured Pydantic models (using JSON mode).
client = instructor.from_groq(Groq(api_key=api_key), mode=instructor.Mode.JSON)

# Instructions provided to the LLM to dictate its behavior,
# ensuring it outputs only valid JSON representing download links.
SYSTEM_PROMPT = """
You are a data extraction assistant.
Extract lead information from the given content.
Respond ONLY with a valid JSON object. No explanation, no markdown fences.
Extract only the download links.
"""


# Define the Pydantic schema for a single extracted link.
# HttpUrl automatically validates that the extracted string is a properly formatted URL.
class Link(BaseModel):
    url: HttpUrl


# Define the top-level schema representing a collection of links.
# This structure tells the LLM that we expect a JSON object with a 'links' array.
class LinkCollection(BaseModel):
    links: List[Link]


def main() -> None:
    # Read the raw markdown content that we want to parse
    with open("data.md", "r") as file:
        markdown_data = file.read()

    # Have the LLM process the markdown data to extract the links
    results = generate_output(markdown_data)

    # Save the extracted links into a text file, separated by commas
    with open("links.txt", "w") as file:
        for link in results.links:
            # Convert HttpUrl to string
            urls_str = str(link.url) + ","
        # Remove the last comma before writing
        file.write(urls_str[:-1])

    print("Links extracted successfully to links.txt")


def generate_output(prompt: str) -> LinkCollection:
    # Construct the message history for the AI conversation
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]

    # Make the API call to Groq using the Instructor wrapper.
    # The 'response_model' parameter dictates the required JSON schema,
    # and Instructor handles parsing the LLM's raw text response into python objects.
    response, completion = client.chat.completions.create_with_completion(
        model=model_name,
        messages=messages,
        temperature=0.0,  # 0.0 makes the model more deterministic and focused on extraction
        response_model=LinkCollection,
    )

    print("Prompt tokens:", completion.usage.prompt_tokens)
    print("Completion tokens:", completion.usage.completion_tokens)
    print("Total tokens:", completion.usage.total_tokens)

    return response


# Execute the script
main()
