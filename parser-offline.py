import time
import instructor
from openai import OpenAI
from pydantic import BaseModel, HttpUrl
from typing import List

openai_client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
client = instructor.from_openai(openai_client, mode=instructor.Mode.JSON)

SYSTEM_PROMPT = """
You are a data extraction assistant.
Extract lead information from the given content.
Respond ONLY with a valid JSON object. No explanation, no markdown fences.
Extract only the download links.
"""


class Link(BaseModel):
    url: HttpUrl


class LinkCollection(BaseModel):
    links: List[Link]


def main() -> None:
    with open("data.md", "r") as file:
        markdown_data = file.read()

    results = generate_output(markdown_data)

    # Save the extracted urls into a text file, separated by commas
    with open("urls.txt", "w") as file:
        urls_str = ""
        for link in results.links:
            # Convert HttpUrl to string
            urls_str += str(link.url) + ","
        # Remove the last comma before writing
        file.write(urls_str[:-1])

    print("Urls extracted successfully to urls.txt")


def generate_output(prompt: str) -> LinkCollection:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]

    response, completion = client.chat.completions.create_with_completion(
        model="deepseek-r1:32b",
        messages=messages,
        temperature=0.0,
        response_model=LinkCollection,
    )

    print("Prompt tokens:", completion.usage.prompt_tokens)
    print("Completion tokens:", completion.usage.completion_tokens)
    print("Total tokens:", completion.usage.total_tokens)

    return response


if __name__ == "__main__":
    start_time = time.time()
    main()
    end_time = time.time()
    print(f"Total execution time: {end_time - start_time:.2f} seconds")
