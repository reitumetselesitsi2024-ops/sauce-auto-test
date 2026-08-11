from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import sys

# --- 1. Get Credentials from GitHub Secrets ---
username = os.environ.get('SAUCE_USERNAME')
access_key = os.environ.get('SAUCE_ACCESS_KEY')

if not username or not access_key:
    print("❌ ERROR: SAUCE_USERNAME or SAUCE_ACCESS_KEY not set!")
    sys.exit(1)

print(f"✅ Credentials found for user: {username}")

# --- 2. Configure Sauce Labs ---
options = ChromeOptions()
options.browser_version = 'latest'
options.platform_name = 'Windows 11'

sauce_options = {}
sauce_options['username'] = username
sauce_options['accessKey'] = access_key
sauce_options['build'] = 'GitHub-Actions-Build'
sauce_options['name'] = 'ThabaBet Login Test'
options.set_capability('sauce:options', sauce_options)

# --- 3. Connect to Sauce Labs ---
url = "https://ondemand.eu-central-1.saucelabs.com:443/wd/hub"
print(f"🚀 Connecting to Sauce Labs...")

try:
    driver = webdriver.Remote(command_executor=url, options=options)
    print("✅ Connected successfully!")
    wait = WebDriverWait(driver, 15)

    # --- 4. Navigate to ThabaBet Login Page ---
    driver.get("https://thababet.co.ls/sign-in")
    print("📄 Loaded ThabaBet login page")
    
    # Wait for page to load
    wait.until(EC.presence_of_element_located((By.CLASS_NAME, "login-page")))
    print("✅ Page loaded successfully")

    # --- 5. Enter Email/Mobile Number ---
    # Find the email/username input field
    email_field = wait.until(EC.presence_of_element_located((By.ID, "v-0-username")))
    email_field.clear()
    email_field.send_keys("58532178")  # <-- CHANGE THIS!
    print("✅ Entered email/mobile number")

    # --- 6. Enter Password ---
    password_field = driver.find_element(By.ID, "v-0-password")
    password_field.clear()
    password_field.send_keys("598976Lesitsi")  # <-- CHANGE THIS!
    print("✅ Entered password")

    # --- 7. Click Login Button ---
    login_button = wait.until(EC.element_to_be_clickable((By.ID, "v-0-submit-button")))
    login_button.click()
    print("✅ Clicked login button")

    # --- 8. Verify Login Success ---
    # Wait for something that appears after login
    # This could be a dashboard element, user profile, etc.
    try:
        # Wait for any element that indicates successful login
        # You'll need to inspect the page after login to find a unique element
        # For now, we'll wait for a URL change or a specific element
        wait.until(EC.url_contains("dashboard"))  # Adjust this based on the actual URL after login
        print("✅ Login successful! Redirected to dashboard.")
        driver.execute_script("sauce:job-result=passed")
    except:
        # If the above fails, check if there's an error message
        try:
            error_element = driver.find_element(By.CLASS_NAME, "error-message")  # Adjust class name
            print(f"❌ Login failed: {error_element.text}")
            driver.execute_script("sauce:job-result=failed")
        except:
            # If we can't find success or error, check page title
            page_title = driver.title
            print(f"ℹ️ Page title after login attempt: {page_title}")
            if "Login" not in page_title:
                print("✅ Login likely successful!")
                driver.execute_script("sauce:job-result=passed")
            else:
                print("❌ Still on login page — login may have failed")
                driver.execute_script("sauce:job-result=failed")

except Exception as e:
    print(f"❌ Test FAILED: {e}")
    driver.execute_script("sauce:job-result=failed")
    sys.exit(1)

finally:
    driver.quit()
    print("🔚 Session closed")
