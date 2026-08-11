from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementNotInteractableException
import os
import sys
import time

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
sauce_options['name'] = 'ThabaBet - Avatar Click Fixed'
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

    # --- 8. Wait for Login to Complete ---
    print("⏳ Waiting for login to complete...")
    time.sleep(3)  # Give time for redirect
    
    # --- 9. Find and Click the Avatar Icon (Multiple Strategies) ---
    avatar_clicked = False
    
    # Strategy 1: Click the SVG icon directly using JavaScript
    try:
        print("🔍 Trying JavaScript click on SVG icon...")
        avatar_svg = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "svg.icon")))
        driver.execute_script("arguments[0].click();", avatar_svg)
        print("✅ Avatar clicked using JavaScript!")
        avatar_clicked = True
        time.sleep(1)
    except:
        print("⚠️ Strategy 1 failed, trying next...")
    
    # Strategy 2: Find the parent container and click it
    if not avatar_clicked:
        try:
            print("🔍 Trying to click parent container...")
            avatar_parent = driver.find_element(By.XPATH, "//*[contains(@class, 'avatar') or contains(@class, 'profile') or contains(@class, 'user')]")
            driver.execute_script("arguments[0].click();", avatar_parent)
            print("✅ Avatar parent clicked!")
            avatar_clicked = True
            time.sleep(1)
        except:
            print("⚠️ Strategy 2 failed, trying next...")
    
    # Strategy 3: Find by data attributes
    if not avatar_clicked:
        try:
            print("🔍 Trying to find by data attributes...")
            avatar_data = driver.find_element(By.XPATH, "//*[contains(@data-testid, 'avatar') or contains(@data-testid, 'profile')]")
            driver.execute_script("arguments[0].click();", avatar_data)
            print("✅ Avatar found by data attribute!")
            avatar_clicked = True
            time.sleep(1)
        except:
            print("⚠️ Strategy 3 failed, trying next...")
    
    # Strategy 4: Try clicking the first SVG on the page (if it's the avatar)
    if not avatar_clicked:
        try:
            print("🔍 Trying to click first SVG...")
            svg_elements = driver.find_elements(By.TAG_NAME, "svg")
            for svg in svg_elements:
                if "icon" in svg.get_attribute("class"):
                    driver.execute_script("arguments[0].click();", svg)
                    print("✅ Clicked on SVG with 'icon' class!")
                    avatar_clicked = True
                    break
        except:
            print("⚠️ Strategy 4 failed")
    
    # --- 10. If all strategies failed, take a screenshot for debugging ---
    if not avatar_clicked:
        print("❌ Could not find or click avatar icon")
        driver.save_screenshot("avatar-debug.png")
        print("📸 Screenshot saved as 'avatar-debug.png'")
        
        # Try to find what's on the page
        page_source = driver.page_source
        print("\n📄 Searching for avatar-related elements in page source...")
        
        # Check for any elements that might be the avatar
        possible_selectors = [
            "avatar", "profile", "user", "account", 
            "dropdown", "menu", "profile-menu"
        ]
        
        found_elements = []
        for selector in possible_selectors:
            elements = driver.find_elements(By.XPATH, f"//*[contains(translate(@class, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{selector}')]")
            if elements:
                found_elements.append(f"{selector}: {len(elements)} found")
        
        if found_elements:
            print("📋 Found these elements:")
            for element in found_elements:
                print(f"   - {element}")
        else:
            print("⚠️ No avatar-related elements found on the page")
    else:
        print("✅ Avatar clicked successfully!")
        
        # Wait for any menu/dropdown to appear
        time.sleep(2)
        print("✅ Check the video to see what opened!")

    # --- 11. Report Success ---
    if avatar_clicked:
        driver.execute_script("sauce:job-result=passed")
        print("✅ Test PASSED! 🎉")
    else:
        driver.execute_script("sauce:job-result=failed")
        print("❌ Test FAILED - Could not click avatar")

except Exception as e:
    print(f"❌ Test FAILED: {e}")
    driver.save_screenshot("error-screenshot.png")
    print("📸 Error screenshot saved")
    driver.execute_script("sauce:job-result=failed")
    sys.exit(1)

finally:
    driver.quit()
    print("🔚 Session closed")
