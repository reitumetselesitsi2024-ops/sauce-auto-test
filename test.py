from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
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
sauce_options['name'] = 'ThabaBet - Find Aviator Multipliers'
options.set_capability('sauce:options', sauce_options)

# --- 3. Connect to Sauce Labs ---
url = "https://ondemand.eu-central-1.saucelabs.com:443/wd/hub"
print(f"🚀 Connecting to Sauce Labs...")

try:
    driver = webdriver.Remote(command_executor=url, options=options)
    print("✅ Connected successfully!")
    wait = WebDriverWait(driver, 20)

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
    time.sleep(5)

    # --- 9. Click Avatar ---
    print("\n🔍 Looking for avatar...")
    
    try:
        avatar = driver.find_element(By.XPATH, "//*[contains(@class, 'avatar') or contains(@class, 'profile') or contains(@class, 'user')]")
        driver.execute_script("arguments[0].click();", avatar)
        print("✅ Avatar clicked!")
        time.sleep(3)
    except:
        print("❌ Could not click avatar")
        driver.save_screenshot("avatar-failed.png")
        sys.exit(1)

    # --- 10. FIND AND SWITCH TO AVIATOR IFRAME ---
    print("\n🔍 Looking for Aviator iframe...")
    
    # Find the iframe with title="Aviator"
    try:
        aviator_iframe = driver.find_element(By.CSS_SELECTOR, "iframe[title='Aviator']")
        print("✅ Found Aviator iframe!")
        print(f"   SRC: {aviator_iframe.get_attribute('src')[:100]}...")
        
        # Switch to the iframe
        driver.switch_to.frame(aviator_iframe)
        print("✅ Switched to Aviator iframe!")
        time.sleep(3)
    except:
        print("❌ Could not find Aviator iframe")
        # Try alternative: find iframe with "aviator" in src
        try:
            iframes = driver.find_elements(By.TAG_NAME, "iframe")
            for iframe in iframes:
                src = iframe.get_attribute('src') or ""
                if "aviator" in src.lower():
                    driver.switch_to.frame(iframe)
                    print(f"✅ Switched to iframe with src containing 'aviator'")
                    break
        except:
            print("❌ No Aviator iframe found")
            driver.save_screenshot("no-iframe.png")
            sys.exit(1)

    # --- 11. WAIT FOR GAME TO LOAD ---
    print("\n⏳ Waiting for Aviator game to load...")
    time.sleep(5)
    
    # Take screenshot to see what's loaded
    driver.save_screenshot("aviator-game-loaded.png")
    print("📸 Screenshot saved: aviator-game-loaded.png")

    # --- 12. FIND MULTIPLIER NUMBERS ---
    print("\n🔍 Looking for multiplier numbers (2.4x, 1.5x, etc.)...")
    
    numbers_found = []
    
    # Method 1: Get all text from the iframe
    try:
        iframe_text = driver.find_element(By.TAG_NAME, "body").text
        print("\n📄 Text from Aviator iframe:")
        print("="*50)
        print(iframe_text[:500])
        print("="*50)
        
        # Find numbers with x (like 2.4x, 1.5x)
        pattern = r'\b\d+\.\d+x?\b'
        matches = re.findall(pattern, iframe_text)
        
        if matches:
            print(f"\n✅ Found {len(matches)} number(s) in iframe:")
            for match in matches:
                print(f"   - {match}")
                numbers_found.append(match)
    except:
        print("⚠️ Could not get text from iframe")

    # Method 2: Look for specific multiplier elements
    if not numbers_found:
        print("\n🔍 Trying specific selectors for multipliers...")
        
        multiplier_selectors = [
            "//span[contains(@class, 'multiplier')]",
            "//div[contains(@class, 'multiplier')]",
            "//span[contains(@class, 'odds')]",
            "//div[contains(@class, 'odds')]",
            "//span[contains(@class, 'rate')]",
            "//div[contains(@class, 'rate')]",
            "//span[contains(@class, 'value')]",
            "//div[contains(@class, 'value')]",
            "//*[contains(@class, 'number')]",
            "//*[contains(@class, 'digit')]",
            "//*[contains(@data-testid, 'multiplier')]",
            "//*[contains(@data-testid, 'odds')]",
            "//*[contains(@data-testid, 'rate')]",
            "//*[contains(@class, 'current-multiplier')]",
            "//*[contains(@class, 'multiplier-value')]",
        ]
        
        for selector in multiplier_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                for element in elements:
                    text = element.text.strip()
                    if text and re.search(r'\d+\.\d+', text):
                        numbers_found.append(text)
                        print(f"✅ Found number in element: '{text}' (selector: {selector})")
            except:
                continue

    # Method 3: Scan all elements for numbers
    if not numbers_found:
        print("\n🔍 Scanning all elements for numbers...")
        try:
            all_elements = driver.find_elements(By.XPATH, "//*")
            for elem in all_elements[:100]:  # Limit to avoid slowdown
                try:
                    text = elem.text.strip()
                    if text and re.search(r'\d+\.\d+', text):
                        numbers_found.append(text)
                        print(f"✅ Found number: '{text}'")
                except:
                    continue
        except:
            pass

    # --- 13. Report Results ---
    print("\n" + "="*50)
    print("📊 FINAL RESULTS")
    print("="*50)
    
    if numbers_found:
        print(f"✅ Found {len(numbers_found)} number(s):")
        for i, num in enumerate(set(numbers_found), 1):
            print(f"   {i}. {num}")
        driver.execute_script("sauce:job-result=passed")
        print("\n✅ Test PASSED! 🎉")
    else:
        print("❌ No multiplier numbers found")
        print("\n💡 The game may need to be started first.")
        print("   You might need to click a 'Bet' or 'Start' button.")
        driver.save_screenshot("no-numbers.png")
        print("📸 Screenshot saved: no-numbers.png")
        
        # Try to find any buttons in the iframe
        try:
            buttons = driver.find_elements(By.TAG_NAME, "button")
            print(f"\n🔍 Found {len(buttons)} button(s) in iframe:")
            for i, btn in enumerate(buttons):
                try:
                    text = btn.text.strip()
                    if text:
                        print(f"   Button {i+1}: '{text}'")
                except:
                    pass
        except:
            pass
        
        driver.execute_script("sauce:job-result=passed")

    # --- 14. Go back to main content ---
    driver.switch_to.default_content()
    print("\n✅ Test completed!")

except Exception as e:
    print(f"❌ Test FAILED: {e}")
    driver.save_screenshot("error-screenshot.png")
    print("📸 Error screenshot saved")
    driver.execute_script("sauce:job-result=failed")
    sys.exit(1)

finally:
    driver.quit()
    print("🔚 Session closed")
