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
        # Use headless mode for faster execution and no GUI
        browser = await playwright.chromium.launch(headless=True)
        page = await browser.new_page()

        print("Navigating to the site.....")
        # Wait for network idle to ensure all dynamic content has loaded
        await page.goto(site_url, wait_until="networkidle")

        html_content = await page.content()
        await browser.close()

        return html_content


def export_as_markdown(html_content: str) -> None:
    # Convert to markdown for better LLM text extraction performance
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

    # Save markdown for downstream processing by the parser
    with open("data.md", "w", encoding="utf-8") as file:
        file.write(markdown_content)
    print("✅ Data saved to data.md")


if __name__ == "__main__":
    start_time = time.time()
    main()
    print(f"✅ Analysis pipeline completed in {time.time() - start_time:.2f} seconds")
