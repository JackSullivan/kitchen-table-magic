from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pyperclip
import time

def click_button_and_preserve_clipboard(url, button_selector):
    # Store the current clipboard content
    original_clipboard = pyperclip.paste()

    # Set up the WebDriver (Chrome in this example)
    options = webdriver.FirefoxOptions()
    driver = webdriver.Firefox(options=options)

    try:
        # Navigate to the webpage
        driver.get(url)

        # Wait for the button to be clickable and then click it
        button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, button_selector))
        )
        button.click()

        # Wait a moment for any JavaScript to execute
        time.sleep(2)

        # Get the new clipboard content
        new_clipboard = pyperclip.paste()

        print(f"Original clipboard content: {original_clipboard}")
        print(f"New clipboard content: {new_clipboard}")

    finally:
        # Close the browser
        driver.quit()

        # Restore the original clipboard content
        pyperclip.copy(original_clipboard)

# Example usage
url = "https://www.17lands.com/deck/0cc1fc10e4164357a9083b9086be55e5"
button_selector = ".sc-dicizt"
click_button_and_preserve_clipboard(url, button_selector)
