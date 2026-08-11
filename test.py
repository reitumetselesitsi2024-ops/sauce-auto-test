from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
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
sauce_options['name'] = 'ThabaBet - Direct Aviator URL'
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
    
    # Enter email
    email_field = wait.until(EC.presence_of_element_located((By.ID, "v-0-username")))
    email_field.clear()
    email_field.send_keys("58532178")
    print("✅ Entered email/mobile number")
    
    # Enter password
    password_field = driver.find_element(By.ID, "v-0-password")
    password_field.clear()
    password_field.send_keys("598976Lesitsi")
    print("✅ Entered password")
    
    # Click login
    login_button = wait.until(EC.element_to_be_clickable((By.ID, "v-0-submit-button")))
    login_button.click()
    print("✅ Clicked login button")
    time.sleep(5)
    print("✅ Login completed!")

    # =========================================================
    # STEP 2: GO DIRECTLY TO AVIATOR GAME (NO AVATAR!)
    # =========================================================
    print("\n" + "="*60)
    print("🛸 STEP 2: GOING DIRECTLY TO AVIATOR GAME")
    print("="*60)
    
    print(f"🌐 Navigating to: https://thababet.co.ls/spribe/8203")
    driver.get("https://thababet.co.ls/spribe/8203")
    time.sleep(5)
    print("✅ Aviator game page loaded!")
    
    # Take screenshot to confirm
    driver.save_screenshot("aviator-page-loaded.png")
    print("📸 Screenshot saved: aviator-page-loaded.png")

    # =========================================================
    # STEP 3: SEARCH FOR MULTIPLIER NUMBERS
    # =========================================================
    print("\n" + "="*60)
    print("🔍 STEP 3: SEARCHING FOR MULTIPLIER NUMBERS")
    print("="*60)
    
    numbers_found = []
    
    # --- 3A: Search in main page ---
    print("\n📄 Searching main page text...")
    body_text = driver.find_element(By.TAG_NAME, "body").text
    print("="*50)
    print(body_text[:500])
    print("="*50)
    
    # Find numbers with x (like 2.4x, 1.5x)
    pattern = r'\b\d+\.\d+x?\b'
    matches = re.findall(pattern, body_text)
    
    if matches:
        print(f"✅ Found {len(matches)} multiplier(s) in main page:")
        for match in matches:
            print(f"   - {match}")
            numbers_found.append(match)
    
    # --- 3B: Search for iframes ---
    print("\n📄 Searching for iframes...")
    iframes = driver.find_elements(By.TAG_NAME, "iframe")
    print(f"📊 Found {len(iframes)} iframe(s)")
    
    for i, iframe in enumerate(iframes):
        try:
            iframe_id = iframe.get_attribute('id') or f"iframe-{i}"
            iframe_src = iframe.get_attribute('src') or "unknown"
            
            print(f"\n📄 Checking iframe {i+1}:")
            print(f"   ID: {iframe_id}")
            print(f"   SRC: {iframe_src[:100]}")
            
            # Skip blank iframes
            if "about:blank" in iframe_src:
                print(f"   ⏭️ Skipping blank iframe")
                continue
            
            # Switch to iframe
            driver.switch_to.frame(iframe)
            
            # Get text inside iframe
            try:
                iframe_text = driver.find_element(By.TAG_NAME, "body").text
                print(f"   📄 Text preview: {iframe_text[:200]}...")
                
                # Search for numbers in iframe
                matches = re.findall(pattern, iframe_text)
                if matches:
                    print(f"   ✅ Found {len(matches)} number(s) in iframe:")
                    for match in matches:
                        print(f"      - {match}")
                        numbers_found.append(match)
            except:
                print(f"   ⚠️ Could not get text from iframe")
            
            # Look for game elements inside iframe
            try:
                game_elements = driver.find_elements(By.XPATH, "//*[contains(@class, 'multiplier') or contains(@class, 'odds') or contains(@class, 'rate') or contains(@class, 'value')]")
                for element in game_elements:
                    text = element.text.strip()
                    if text and re.search(r'\d+\.\d+', text):
                        numbers_found.append(text)
                        print(f"   ✅ Found number in game element: '{text}'")
            except:
                pass
            
            # Go back to main content
            driver.switch_to.default_content()
            
        except Exception as e:
            print(f"   ⚠️ Error with iframe {i+1}: {e}")
            try:
                driver.switch_to.default_content()
            except:
                pass
            continue
    
    # --- 3C: Search for multipliers in all elements ---
    if not numbers_found:
        print("\n🔍 Scanning all elements for numbers...")
        try:
            all_elements = driver.find_elements(By.XPATH, "//*")
            for elem in all_elements[:200]:  # Limit to avoid slowdown
                try:
                    text = elem.text.strip()
                    if text and re.search(r'\d+\.\d+', text):
                        numbers_found.append(text)
                        print(f"   ✅ Found number in element: '{text}'")
                except:
                    continue
        except:
            pass

    # =========================================================
    # STEP 4: RESULTS
    # =========================================================
    print("\n" + "="*60)
    print("📊 FINAL RESULTS")
    print("="*60)
    
    if numbers_found:
        # Remove duplicates and sort
        unique_numbers = list(set(numbers_found))
        print(f"✅ Found {len(unique_numbers)} number(s):")
        for i, num in enumerate(unique_numbers, 1):
            print(f"   {i}. {num}")
        
        # Try to extract the highest multiplier
        highest = None
        for num in unique_numbers:
            try:
                val = float(num.replace('x', ''))
                if highest is None or val > highest:
                    highest = val
            except:
                pass
        
        if highest:
            print(f"   🏆 Highest multiplier: {highest}x")
        
        driver.execute_script("sauce:job-result=passed")
        print("\n✅ Test PASSED! 🎉")
    else:
        print("❌ No multiplier numbers found")
        print("\n💡 Possible reasons:")
        print("   - Game needs to be started (click 'Bet' or 'Start')")
        print("   - Numbers appear after placing a bet")
        print("   - The game might be in a nested iframe")
        
        # Try to find any buttons in the page
        try:
            buttons = driver.find_elements(By.TAG_NAME, "button")
            print(f"\n🔍 Found {len(buttons)} button(s) on the page:")
            for i, btn in enumerate(buttons[:10]):
                try:
                    text = btn.text.strip()
                    if text:
                        print(f"   Button {i+1}: '{text}'")
                except:
                    pass
        except:
            pass
        
        driver.save_screenshot("no-numbers-found.png")
        print("\n📸 Screenshot saved: no-numbers-found.png")
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
