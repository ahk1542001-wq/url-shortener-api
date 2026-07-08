import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1280, "height": 800})
        
        print("Capturing 01.png - Login Screen")
        await page.goto("http://localhost:8000")
        await asyncio.sleep(2)  # Wait for animations
        await page.screenshot(path="screenshots/01.png")
        
        print("Capturing 02.png - Main App (after login)")
        # Authenticate
        await page.fill("#password", "your-secret-password-here")
        await page.click("#password-btn")
        await asyncio.sleep(2)
        await page.screenshot(path="screenshots/02.png")
        
        print("Capturing 03.png - Success State")
        # Create a link
        await page.fill("#url", "https://render.com/docs/free-instance-spin-down")
        await page.fill("#custom_code", "render-docs")
        await page.click("#submit-btn")
        await asyncio.sleep(2)
        await page.screenshot(path="screenshots/03.png")
        
        await browser.close()
        print("Screenshots captured successfully.")

if __name__ == "__main__":
    asyncio.run(main())
