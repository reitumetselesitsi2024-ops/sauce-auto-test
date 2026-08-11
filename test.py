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
sauce_options['name'] = 'ThabaBet - Aviator Multipliers'
options.set_capability('sauce:options', sauce_options)

# --- 3. Connect to Sauce Labs ---
url = "https://ondemand.eu-central-1.saucelabs.com:443/wd/hub"
print(f"🚀 Connecting to Sauce Labs...")

try:
    driver = webdriver.Remote(command_executor=url, options=options)
    print("✅ Connected successfully!")
    wait = WebDriverWait(driver, 20)

    # =========================================================
    # STEP 1: LOGIN
    # =========================================================
    print("\n" + "="*60)
    print("🔐 STEP 1: LOGGING IN")
    print("="*60)
    
    driver.get("https://thababet.co.ls/sign-in")
    print("📄 Loaded ThabaBet login page")
    wait.until(EC.presence_of_element_located((By.CLASS_NAME, "login-page")))
    
    email_field = wait.until(EC.presence_of_element_located((By.ID, "v-0-username")))
    email_field.clear()
    email_field.send_keys("58532178")
    print("✅ Entered email/mobile number")
    
    password_field = driver.find_element(By.ID, "v-0-password")
    password_field.clear()
    password_field.send_keys("598976Lesitsi")
    print("✅ Entered password")
    
    login_button = wait.until(EC.element_to_be_clickable((By.ID, "v-0-submit-button")))
    login_button.click()
    print("✅ Clicked login button")
    time.sleep(5)
    print("✅ Login completed!")

    # =========================================================
    # STEP 2: GO DIRECTLY TO AVIATOR GAME
    # =========================================================
    print("\n" + "="*60)
    print("🛸 STEP 2: GOING TO AVIATOR GAME")
    print("="*60)
    
    driver.get("https://thababet.co.ls/spribe/8203")
    time.sleep(8)
    print("✅ Aviator game page loaded!")
    
    driver.save_screenshot("aviator-page-loaded.png")
    print("📸 Screenshot saved: aviator-page-loaded.png")

    # =========================================================
    # STEP 3: EXTRACT MULTIPLIERS FROM IFRAME
    # =========================================================
    print("\n" + "="*60)
    print("🎯 STEP 3: EXTRACTING MULTIPLIERS (numbers with 'x')")
    print("="*60)
    
    multipliers_found = []
    
    # Find and switch to the Aviator iframe
    print("\n🔍 Looking for Aviator iframe...")
    iframes = driver.find_elements(By.TAG_NAME, "iframe")
    print(f"📊 Found {len(iframes)} iframe(s)")
    
    for i, iframe in enumerate(iframes):
        try:
            iframe_src = iframe.get_attribute('src') or ""
            if "aviator" in iframe_src.lower() or "spribe" in iframe_src.lower():
                print(f"✅ Found Aviator iframe! (iframe {i+1})")
                driver.switch_to.frame(iframe)
                print("✅ Switched to Aviator iframe!")
                break
        except:
            continue
    else:
        print("❌ Could not find Aviator iframe!")
        sys.exit(1)
    
    # Wait for content to load
    time.sleep(3)
    
    # Get all text from the iframe
    iframe_text = driver.find_element(By.TAG_NAME, "body").text
    print("\n📄 Text from Aviator iframe:")
    print("="*50)
    print(iframe_text[:500])
    print("="*50)
    
    # --- Extract ONLY numbers with 'x' at the end (multipliers) ---
    pattern = r'\b\d+\.\d+x\b'
    matches = re.findall(pattern, iframe_text)
    
    if matches:
        print(f"\n✅ Found {len(matches)} multiplier(s):")
        for match in matches:
            print(f"   - {match}")
            multipliers_found.append(match)
    
    # --- Also look for elements with 'x' in them ---
    print("\n🔍 Searching for multiplier elements...")
    try:
        # Look for elements containing 'x'
        elements_with_x = driver.find_elements(By.XPATH, "//*[contains(text(), 'x')]")
        for element in elements_with_x:
            text = element.text.strip()
            if text and re.search(r'\d+\.\d+x', text):
                multipliers_found.append(text)
                print(f"   ✅ Found: '{text}'")
    except:
        pass
    
    # Go back to main content
    driver.switch_to.default_content()

    # =========================================================
    # STEP 4: PROCESS AND SORT MULTIPLIERS
    # =========================================================
    print("\n" + "="*60)
    print("📊 STEP 4: SORTED MULTIPLIERS (Highest to Lowest)")
    print("="*60)
    
    # Remove duplicates
    unique_multipliers = list(set(multipliers_found))
    print(f"✅ Found {len(unique_multipliers)} unique multiplier(s)")
    
    # Parse and sort
    multiplier_values = []
    for mult in unique_multipliers:
        try:
            # Remove 'x' and convert to float
            value = float(mult.replace('x', ''))
            multiplier_values.append((value, mult))
        except:
            pass
    
    # Sort from highest to lowest
    multiplier_values.sort(reverse=True)
    
    print("\n🏆 MULTIPLIERS (Highest to Lowest):")
    for i, (value, text) in enumerate(multiplier_values, 1):
        print(f"   {i}. {text} ({value}x)")
    
    # Show top 10
    print("\n🔥 TOP 10 HIGHEST MULTIPLIERS:")
    for i, (value, text) in enumerate(multiplier_values[:10], 1):
        print(f"   #{i}: {text}")
    
    # =========================================================
    # STEP 5: RESULTS
    # =========================================================
    print("\n" + "="*60)
    print("📊 FINAL RESULTS")
    print("="*60)
    
    if multiplier_values:
        highest = multiplier_values[0]
        print(f"🎯 Highest multiplier: {highest[1]} ({highest[0]}x)")
        print(f"📊 Total unique multipliers found: {len(multiplier_values)}")
        driver.execute_script("sauce:job-result=passed")
        print("\n✅ Test PASSED! 🎉")
    else:
        print("❌ No multipliers found")
        driver.save_screenshot("no-multipliers.png")
        driver.execute_script("sauce:job-result=passed")

except Exception as e:
    print(f"❌ Test FAILED: {e}")
    driver.save_screenshot("error-screenshot.png")
    print("📸 Error screenshot saved")
    driver.execute_script("sauce:job-result=failed")
    sys.exit(1)

finally:
    driver.quit()
    print("\n🔚 Session closed")
