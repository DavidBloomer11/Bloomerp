from playwright.sync_api import Browser, expect


def test_regular_phone_tap_does_not_reveal_sidebar_button(
    browser: Browser,
    live_server_url: str,
    test_user,
) -> None:
    """
    Use case: A user taps a normal page control on a phone while the sidebar is closed.
    Expected result: The control handles the tap and the floating sidebar button stays hidden.
    """
    # 1. Open an authenticated phone-sized page with touch support.
    test_user.is_staff = True
    test_user.save(update_fields=["is_staff"])
    context = browser.new_context(
        viewport={"width": 390, "height": 844},
        has_touch=True,
        is_mobile=True,
    )
    page = context.new_page()
    page.goto(f"{live_server_url}/login/")
    page.locator('input[name="username"]').fill("testuser")
    page.locator('input[name="password"]').fill("testpass123")
    page.get_by_role("button", name="Login").tap()
    page.wait_for_url(f"{live_server_url}/")

    # 2. Add and tap a regular control away from the sidebar activation corner.
    page.evaluate(
        """
        () => {
            const button = document.createElement('button');
            button.textContent = 'Phone action';
            button.style.position = 'fixed';
            button.style.left = '160px';
            button.style.top = '300px';
            button.addEventListener('click', () => button.dataset.clicked = 'true');
            document.body.appendChild(button);
        }
        """
    )
    action_button = page.get_by_role("button", name="Phone action")
    action_button.tap()

    # 3. Confirm the intended click ran without revealing the floating sidebar control.
    expect(action_button).to_have_attribute("data-clicked", "true")
    expect(page.locator("#sidebar-toggle-floating")).to_be_hidden()

    context.close()
