import asyncio, os
from dotenv import load_dotenv
from playwright.async_api import async_playwright
from markdownify import markdownify as md

load_dotenv()


def main() -> None:
    site_url = os.getenv("SITE_URL")

    html_content = asyncio.run(fetch_page(site_url))
    export_as_markdown(html_content)


async def fetch_page(site_url: str) -> str:
    async with async_playwright() as playwright:
        # launching the browser
        browser = await playwright.chromium.launch(headless=True)
        page = await browser.new_page()

        print("Navigating to the site.....")
        await page.goto(site_url, wait_until="networkidle")

        # extracting RAW the html content
        html_content = await page.content()
        await browser.close()

        return html_content


def export_as_markdown(html_content: str) -> None:
    # converting into markdown format for easier extraction
    markdown_content = md(
        html_content,
        heading_style="ATX",
        strip=[
            "script",
            "style",
            "img",
            "svg",
            "head",
            "footer",
            "header",
            "nav",
            "aside",
        ],
    )

    # saving the data for later usage
    with open("data.md", "w", encoding="utf-8") as file:
        file.write(markdown_content)
    print("✅ Data saved to data.md")


main()
