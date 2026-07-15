#!/usr/bin/env python3
"""Capture the documentation screenshot set from a seeded Swoosh instance."""

import os
from pathlib import Path

from playwright.sync_api import Page, sync_playwright


BASE_URL = os.getenv("SWOOSH_SCREENSHOT_URL", "http://127.0.0.1:8002")
ADMIN_USERNAME = os.getenv("SWOOSH_DOCS_ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("SWOOSH_DOCS_ADMIN_PASSWORD")
DEMO_USERNAME = os.getenv("SWOOSH_DOCS_DEMO_USERNAME", "swoosh-demo")
DEMO_PASSWORD = os.getenv("SWOOSH_DOCS_DEMO_PASSWORD")
OUTPUT_DIR = Path(os.getenv("SWOOSH_SCREENSHOT_DIR", "screenshots"))


def require_credentials() -> None:
    missing = []
    if not ADMIN_PASSWORD:
        missing.append("SWOOSH_DOCS_ADMIN_PASSWORD")
    if not DEMO_PASSWORD:
        missing.append("SWOOSH_DOCS_DEMO_PASSWORD")
    if missing:
        raise SystemExit(
            f"Missing required environment variables: {', '.join(missing)}"
        )


def settle(page: Page) -> None:
    page.wait_for_load_state("networkidle")
    page.evaluate("document.activeElement && document.activeElement.blur()")
    page.wait_for_timeout(350)


def capture(page: Page, filename: str, *, full_page: bool = False) -> None:
    settle(page)
    page.screenshot(
        path=str(OUTPUT_DIR / filename),
        full_page=full_page,
        animations="disabled",
    )


def focus_and_capture(page: Page, selector: str, filename: str) -> None:
    page.locator(selector).scroll_into_view_if_needed()
    page.wait_for_timeout(250)
    capture(page, filename)


def login(page: Page, username: str, password: str) -> None:
    page.goto(BASE_URL)
    page.locator("#nav-login-btn").click()
    page.wait_for_timeout(450)
    page.locator("#username").fill(username)
    page.locator("#password").fill(password)
    page.locator("#password-btn").click()
    page.wait_for_timeout(600)


def open_profile(page: Page, profile_name: str = "swoosh-student") -> None:
    page.get_by_label(f"Open {profile_name} Link Tree profile").click()
    page.wait_for_timeout(600)


def capture_admin(browser, viewport: dict, suffix: str) -> None:
    context = browser.new_context(viewport=viewport)
    page = context.new_page()
    page.emulate_media(reduced_motion="reduce")

    page.goto(BASE_URL)
    capture(page, f"01_landing_{suffix}.png")
    page.locator("#nav-login-btn").click()
    capture(page, f"02_login_{suffix}.png")

    page.locator("#username").fill(ADMIN_USERNAME)
    page.locator("#password").fill(ADMIN_PASSWORD)
    page.locator("#password-btn").click()
    page.wait_for_timeout(3300)
    capture(page, f"03_admin_users_{suffix}.png")

    page.get_by_role("button", name=f"Manage {DEMO_USERNAME}").click()
    page.wait_for_timeout(500)
    capture(page, f"04_admin_user_management_{suffix}.png")
    page.locator(
        "#nav-admin-detail-back:visible, #top-nav-admin-back:visible"
    ).first.click()
    page.wait_for_timeout(350)

    page.locator("#admin-add-user-btn").click()
    capture(page, f"04_admin_create_user_{suffix}.png")

    context.close()


def capture_user(
    browser, viewport: dict, suffix: str, create_final_profile: bool
) -> None:
    context = browser.new_context(viewport=viewport)
    page = context.new_page()
    page.emulate_media(reduced_motion="reduce")
    login(page, DEMO_USERNAME, DEMO_PASSWORD)

    capture(page, f"05_feature_selection_{suffix}.png")
    page.locator("#select-tree-feature").click()
    page.wait_for_timeout(650)
    capture(page, f"06_profile_selection_{suffix}.png")

    if create_final_profile:
        page.locator("#add-profile-btn").click()
        page.locator("#new-profile-username").fill("study-links")
        capture(page, f"07_create_profile_{suffix}.png")
        page.locator("#cancel-create-profile-btn").click()
        page.wait_for_timeout(350)

    page.locator("#back-to-features-ps").click()
    page.locator("#select-standalone-feature").click()
    page.wait_for_timeout(650)
    capture(page, f"08_shortener_{suffix}.png")
    focus_and_capture(page, "#my-links-card", f"09_portfolio_{suffix}.png")

    page.locator(".qr-link-btn").first.click()
    capture(page, f"10_qr_modal_{suffix}.png")
    page.locator("#close-qr-modal-btn").click()

    page.locator(".edit-btn").first.click()
    capture(page, f"11_edit_link_{suffix}.png")
    page.locator("#cancel-edit-btn").click()

    page.locator('[data-tab="analytics"]:visible').first.click()
    page.wait_for_timeout(600)
    capture(page, f"12_shortener_analytics_{suffix}.png")

    page.locator(
        "#sidebar-back-features:visible, .back-features-btn:visible"
    ).first.click()
    page.locator("#select-tree-feature").click()
    page.wait_for_timeout(550)
    open_profile(page)

    capture(page, f"13_tree_share_{suffix}.png")
    page.locator('[data-tab="profile"]:visible').first.click()
    page.wait_for_timeout(600)
    capture(page, f"14_profile_settings_{suffix}.png")

    page.locator('[data-tab="analytics"]:visible').first.click()
    page.wait_for_timeout(600)
    capture(page, f"15_tree_analytics_{suffix}.png")

    public_page = context.new_page()
    public_page.set_viewport_size(viewport)
    public_page.emulate_media(reduced_motion="reduce")
    public_page.goto(f"{BASE_URL}/u/swoosh-student")
    capture(public_page, f"16_public_tree_{suffix}.png")

    context.close()


def main() -> None:
    require_credentials()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for screenshot in OUTPUT_DIR.glob("*.png"):
        screenshot.unlink()

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="chrome", headless=True)
        desktop = {"width": 1440, "height": 900}
        mobile = {"width": 390, "height": 844}

        capture_admin(browser, desktop, "desktop")
        capture_user(browser, desktop, "desktop", create_final_profile=True)
        capture_admin(browser, mobile, "mobile")
        capture_user(browser, mobile, "mobile", create_final_profile=False)

        browser.close()


if __name__ == "__main__":
    main()
