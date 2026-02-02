from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
import time

# Set up Chrome options
chrome_options = Options()
chrome_options.add_argument("--headless")  # To run Chrome in headless mode
chrome_options.add_argument("--disable-gpu")

# Initialize the Chrome driver
driver = webdriver.Chrome(options=chrome_options)

# Navigate to a URL
driver.get("https://ahan-ai.notion.site/0e300c263a094e85b6a93a0de45859d8")

# Wait for the page to load completely
wait = WebDriverWait(driver, 30)

driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

time.sleep(20)

# width = driver.execute_script("return document.documentElement.scrollWidth")
width = 1080
height = driver.execute_script("return document.body.scrollHeight")
print(width, height)
driver.set_window_size(width, height)

# Wait for the page to load completely (you can add more explicit waits if needed)

# Take a screenshot
driver.save_screenshot("screenshot.png")
driver.get_screenshot_as_file("screenshot2.png")

# Close the driver
driver.quit()