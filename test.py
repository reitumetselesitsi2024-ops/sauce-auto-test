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
    print("\n" + "="*50)
    print("🔐 LOGGING IN")
    print("="*50)
    
    driver.get("https://thababet.co.ls/sign-in")
    wait.until(EC.presence_of_element_located((By.CLASS_NAME, "login-page")))
    
    email_field = wait.until(EC.presence_of_element_located((By.ID, "v-0-username")))
    email_field.clear()
    email_field.send_keys("58532178")
    print("✅ Email entered")
    
    password_field = driver.find_element(By.ID, "v-0-password")
    password_field.clear()
    password_field.send_keys("598976Lesitsi")
    print("✅ Password entered")
    
    login_button = wait.until(EC.element_to_be_clickable((By.ID, "v-0-submit-button")))
    login_button.click()
    time.sleep(5)
    print("✅ Login successful!")

    # =========================================================
    # STEP 2: GO TO AVIATOR GAME
    # =========================================================
    print("\n" + "="*50)
    print("🛸 LOADING AVIATOR GAME")
    print("="*50)
    
    driver.get("https://thababet.co.ls/spribe/8203")
    time.sleep(8)
    print("✅ Aviator game loaded!")

    # =========================================================
    # STEP 3: EXTRACT MULTIPLIERS
    # =========================================================
    print("\n" + "="*50)
    print("🎯 EXTRACTING MULTIPLIERS")
    print("="*50)
    
    # Find Aviator iframe
    iframes = driver.find_elements(By.TAG_NAME, "iframe")
    for iframe in iframes:
        src = iframe.get_attribute('src') or ""
        if "aviator" in src.lower() or "spribe" in src.lower():
            driver.switch_to.frame(iframe)
            print("✅ Switched to Aviator iframe")
            break
    
    time.sleep(2)
    
    # Get all text and find multipliers
    page_text = driver.find_element(By.TAG_NAME, "body").text
    pattern = r'\b\d+\.\d+x\b'
    multipliers = re.findall(pattern, page_text)
    
    # Clean and sort
    unique_multipliers = list(set(multipliers))
    
    # Sort by value (highest to lowest)
    sorted_multipliers = sorted(
        unique_multipliers,
        key=lambda x: float(x.replace('x', '')),
        reverse=True
    )
    
    # =========================================================
    # STEP 4: DISPLAY RESULTS
    # =========================================================
    print("\n" + "="*50)
    print("📊 RESULTS")
    print("="*50)
    
    if sorted_multipliers:
        print(f"✅ Found {len(sorted_multipliers)} unique multiplier(s)")
        print(f"🏆 Highest: {sorted_multipliers[0]}")
        print(f"🔄 Most recent: {sorted_multipliers[-1]}")
        
        print("\n📋 All multipliers:")
        for i, mult in enumerate(sorted_multipliers, 1):
            print(f"   {i}. {mult}")
        
        driver.execute_script("sauce:job-result=passed")
        print("\n✅ Test PASSED! 🎉")
    else:
        print("❌ No multipliers found")
        driver.execute_script("sauce:job-result=failed")

except Exception as e:
    print(f"❌ Test FAILED: {e}")
    driver.execute_script("sauce:job-result=failed")
    sys.exit(1)

finally:
    driver.quit()
    print("\n🔚 Session closed")
