from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementNotInteractableException
import os
import sys
import time
import re

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
sauce_options['name'] = 'ThabaBet - Find Numbers After Avatar'
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
    
    wait.until(EC.presence_of_element_located((By.CLASS_NAME, "login-page")))
    print("✅ Page loaded successfully")

    # --- 5. Enter Email/Mobile Number ---
    email_field = wait.until(EC.presence_of_element_located((By.ID, "v-0-username")))
    email_field.clear()
    email_field.send_keys("58532178")
    print("✅ Entered email/mobile number")

    # --- 6. Enter Password ---
    password_field = driver.find_element(By.ID, "v-0-password")
    password_field.clear()
    password_field.send_keys("598976Lesitsi")
    print("✅ Entered password")

    # --- 7. Click Login Button ---
    login_button = wait.until(EC.element_to_be_clickable((By.ID, "v-0-submit-button")))
    login_button.click()
    print("✅ Clicked login button")

    # --- 8. Wait for Login to Complete ---
    print("⏳ Waiting for login to complete...")
    time.sleep(3)

    # --- 9. Click Avatar ---
    avatar_clicked = False
    
    try:
        print("🔍 Trying JavaScript click on SVG icon...")
        avatar_svg = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "svg.icon")))
        driver.execute_script("arguments[0].click();", avatar_svg)
        print("✅ Avatar clicked using JavaScript!")
        avatar_clicked = True
        time.sleep(2)  # Wait for menu/dropdown to appear
    except:
        print("⚠️ Could not click avatar")
        driver.execute_script("sauce:job-result=failed")
        sys.exit(1)

    # --- 10. FIND NUMBERS (Like 2.4x, 1.5x, 3.0x, etc.) ---
    print("\n🔍 Looking for numbers (like 2.4x, 1.5x, etc.)...")
    
    numbers_found = []
    
    # Strategy 1: Find by specific class that might contain numbers
    number_selectors = [
        "//*[contains(text(), '.') and contains(text(), 'x')]",  # Any element with . and x
        "//*[contains(text(), '2.4')]",  # Specific number
        "//*[contains(text(), '1.5')]",
        "//*[contains(text(), '3.0')]",
        "//span[contains(@class, 'multiplier')]",  # Class with multiplier
        "//div[contains(@class, 'multiplier')]",
        "//span[contains(@class, 'rate')]",  # Class with rate
        "//div[contains(@class, 'rate')]",
        "//span[contains(@class, 'odds')]",  # Class with odds
        "//div[contains(@class, 'odds')]",
        "//span[contains(@class, 'price')]",  # Class with price
        "//div[contains(@class, 'price')]",
        "//*[contains(@data-testid, 'multiplier')]",
        "//*[contains(@data-testid, 'odds')]",
        "//*[contains(@data-testid, 'rate')]",
        "//*[contains(@class, 'number')]",
        "//*[contains(@class, 'value')]",
    ]
    
    for selector in number_selectors:
        try:
            print(f"🔍 Trying selector: {selector}")
            elements = driver.find_elements(By.XPATH, selector)
            for element in elements:
                text = element.text.strip()
                if text and re.search(r'\d+\.\d+x?', text):  # Matches numbers like 2.4, 2.4x
                    numbers_found.append({
                        'text': text,
                        'selector': selector,
                        'element': element
                    })
                    print(f"✅ Found number: '{text}' using selector: {selector}")
        except:
            continue
    
    # Strategy 2: Get all text and find numbers
    if not numbers_found:
        print("\n🔍 Strategy 2: Scanning all visible text for numbers...")
        all_text = driver.find_element(By.TAG_NAME, "body").text
        # Find all numbers with decimal and optional 'x'
        pattern = r'\b\d+\.\d+x?\b'
        matches = re.findall(pattern, all_text)
        for match in matches:
            numbers_found.append({
                'text': match,
                'selector': 'FULL_PAGE_SCAN',
                'element': None
            })
            print(f"✅ Found number in page text: '{match}'")
    
    # Strategy 3: Look for numbers in specific containers
    if not numbers_found:
        print("\n🔍 Strategy 3: Looking in specific containers...")
        container_selectors = [
            "//div[@role='button']",
            "//button",
            "//span",
            "//div[contains(@class, 'item')]",
            "//div[contains(@class, 'card')]",
        ]
        
        for container_selector in container_selectors:
            try:
                containers = driver.find_elements(By.XPATH, container_selector)
                for container in containers:
                    text = container.text.strip()
                    if text and re.search(r'\d+\.\d+x?', text):
                        numbers_found.append({
                            'text': text,
                            'selector': f'{container_selector} (found in container)',
                            'element': container
                        })
                        print(f"✅ Found number: '{text}' in container: {container_selector}")
            except:
                continue

    # --- 11. Report Results ---
    print("\n" + "="*50)
    print("📊 NUMBER SEARCH RESULTS")
    print("="*50)
    
    if numbers_found:
        print(f"✅ Found {len(numbers_found)} number(s):")
        for i, result in enumerate(numbers_found, 1):
            print(f"   {i}. '{result['text']}'")
            print(f"      Selector: {result['selector']}")
    else:
        print("❌ No numbers found on the page")
        # Take screenshot for debugging
        driver.save_screenshot("no-numbers-found.png")
        print("📸 Screenshot saved as 'no-numbers-found.png'")
        
        # Print all text for debugging
        print("\n📄 All text on page:")
        print("="*50)
        all_text = driver.find_element(By.TAG_NAME, "body").text
        print(all_text[:500])  # Print first 500 characters
        print("="*50)
    
    # --- 12. Try to click on a found number (if any) ---
    if numbers_found:
        try:
            # Click on the first number found
            first_number_element = numbers_found[0].get('element')
            if first_number_element:
                driver.execute_script("arguments[0].click();", first_number_element)
                print(f"✅ Clicked on number: '{numbers_found[0]['text']}'")
                time.sleep(1)
        except:
            print("ℹ️ Could not click on number (element may not be clickable)")
    
    # --- 13. Report Success ---
    if avatar_clicked:
        driver.execute_script("sauce:job-result=passed")
        print("\n✅ Test PASSED! 🎉")
        print(f"📊 Numbers found: {len(numbers_found)}")
    else:
        driver.execute_script("sauce:job-result=failed")
        print("❌ Test FAILED")

except Exception as e:
    print(f"❌ Test FAILED: {e}")
    driver.save_screenshot("error-screenshot.png")
    print("📸 Error screenshot saved")
    driver.execute_script("sauce:job-result=failed")
    sys.exit(1)

finally:
    driver.quit()
    print("🔚 Session closed")
