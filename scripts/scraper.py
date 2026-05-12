"""
Module for scraping web content and converting it to Markdown.

This script uses Playwright to handle dynamic content and converts the resulting 
HTML into a clean Markdown format suitable for LLM processing.
"""

import asyncio
import os
import time
from dotenv import load_dotenv
from playwright.async_api import async_playwright
from markdownify import markdownify as md

load_dotenv()


def main() -> None:
    site_url = os.getenv("SITE_URL")

    html_content = asyncio.run(fetch_page(site_url))
    
    if html_content:
        export_as_markdown(html_content)
    else:
        print("❌ No HTML content found")


async def fetch_page(site_url: str) -> str:
    """
    Asynchronously fetches the HTML content of a given URL.
    
    Uses Playwright to ensure that dynamic (JavaScript-rendered) content is 
    fully loaded before capturing the page content.
    """
    async with async_playwright() as playwright:
        # Headless mode is used to run the browser in the background without a GUI,
        # which is more efficient for automated scraping tasks.
        browser = await playwright.chromium.launch(headless=True)
        page = await browser.new_page()

        print("Navigating to the site.....")
        
        # 'networkidle' is used to wait until there are no more than 2 network 
        # connections for at least 500ms. This ensures that most dynamic/lazy 
        # content (like images or data via XHR) has finished loading.
        await page.goto(site_url, wait_until="networkidle")

        html_content = await page.content()
        await browser.close()

        return html_content


def export_as_markdown(html_content: str) -> None:
    """
    Converts HTML content to Markdown and saves it to a file.
    
    Markdown is preferred over HTML for LLM processing because it preserves 
    structural information (headings, lists) while significantly reducing 
    token usage by removing unnecessary tags.
    """
    # Removing non-textual or layout-heavy tags to reduce noise and focus 
    # the LLM on the core content of the page.
    markdown_content = md(
        html_content,
        heading_style="ATX",
        strip=[
            "script", "style", "img", "svg", "head", 
            "footer", "header", "nav", "aside",
        ],
    )

    # Save the processed content for the parser module to read.
    # UTF-8 encoding ensures that special characters are handled correctly.
    data_dir = "data"
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        
    with open(os.path.join(data_dir, "webpage.md"), "w", encoding="utf-8") as file:
        file.write(markdown_content)
    print(f"✅ Data saved to {os.path.join(data_dir, 'webpage.md')}")


if __name__ == "__main__":
    start_time = time.time()
    main()
    print(f"✅ Run Time is {time.time() - start_time:.2f} seconds")
