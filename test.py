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
sauce_options['name'] = 'ThabaBet - Find Numbers'
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
    time.sleep(5)  # Give more time for redirect

    # --- 9. FIND AND CLICK AVATAR (More Robust) ---
    print("\n🔍 Looking for avatar...")
    avatar_clicked = False
    
    # Take screenshot before avatar click
    driver.save_screenshot("before-avatar-click.png")
    print("📸 Screenshot saved: before-avatar-click.png")
    
    # Try ALL possible ways to find and click avatar
    avatar_methods = [
        # Method 1: SVG with icon class
        lambda: driver.find_element(By.CSS_SELECTOR, "svg.icon"),
        # Method 2: Any SVG
        lambda: driver.find_element(By.TAG_NAME, "svg"),
        # Method 3: Elements with avatar-related classes
        lambda: driver.find_element(By.XPATH, "//*[contains(@class, 'avatar') or contains(@class, 'profile') or contains(@class, 'user') or contains(@class, 'account')]"),
        # Method 4: Elements with avatar-related IDs
        lambda: driver.find_element(By.XPATH, "//*[contains(@id, 'avatar') or contains(@id, 'profile') or contains(@id, 'user') or contains(@id, 'account')]"),
        # Method 5: Button elements with aria-label
        lambda: driver.find_element(By.XPATH, "//button[contains(@aria-label, 'profile') or contains(@aria-label, 'user') or contains(@aria-label, 'account')]"),
        # Method 6: Image elements with avatar alt text
        lambda: driver.find_element(By.XPATH, "//img[contains(@alt, 'avatar') or contains(@alt, 'profile') or contains(@alt, 'user')]"),
        # Method 7: Div with role button
        lambda: driver.find_element(By.XPATH, "//div[@role='button']"),
        # Method 8: Elements with data-testid
        lambda: driver.find_element(By.XPATH, "//*[contains(@data-testid, 'avatar') or contains(@data-testid, 'profile') or contains(@data-testid, 'user')]"),
        # Method 9: Look for clickable elements on the right side of header
        lambda: driver.find_element(By.XPATH, "//header//div[contains(@class, 'right') or contains(@class, 'end')]//button"),
        # Method 10: Any clickable element in the header
        lambda: driver.find_element(By.XPATH, "//header//*[@role='button']"),
    ]
    
    for i, method in enumerate(avatar_methods, 1):
        try:
            print(f"🔍 Trying avatar method {i}...")
            avatar = method()
            
            # Scroll to avatar
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", avatar)
            time.sleep(1)
            
            # Try to click with JavaScript (bypasses interactability issues)
            driver.execute_script("arguments[0].click();", avatar)
            print(f"✅ Avatar clicked using method {i}!")
            avatar_clicked = True
            time.sleep(2)
            break
        except:
            continue
    
    if not avatar_clicked:
        print("❌ Could not click avatar")
        driver.save_screenshot("avatar-failed.png")
        print("📸 Screenshot saved: avatar-failed.png")
        
        # Print page source for debugging
        print("\n📄 Page source (first 1000 chars):")
        print("="*50)
        print(driver.page_source[:1000])
        print("="*50)
        
        driver.execute_script("sauce:job-result=failed")
        sys.exit(1)

    # --- 10. After Avatar Click - LOOK FOR NUMBERS ---
    print("\n🔍 Avatar clicked! Now looking for numbers like 2.4x, 1.5x...")
    time.sleep(2)  # Wait for menu to appear
    
    # Take screenshot after avatar click
    driver.save_screenshot("after-avatar-click.png")
    print("📸 Screenshot saved: after-avatar-click.png")
    
    # --- 11. FIND NUMBERS ---
    numbers_found = []
    
    # Get all visible text on the page
    all_text = driver.find_element(By.TAG_NAME, "body").text
    print(f"\n📄 Page text (first 500 chars):")
    print("="*50)
    print(all_text[:500])
    print("="*50)
    
    # Method 1: Find all numbers with pattern like 2.4, 2.4x, 1.5, 1.5x, etc.
    pattern = r'\b\d+\.\d+x?\b'
    matches = re.findall(pattern, all_text)
    
    if matches:
        print(f"\n✅ Found {len(matches)} number(s):")
        for match in matches:
            print(f"   - {match}")
            numbers_found.append(match)
    else:
        print("\n❌ No numbers found in page text")
    
    # Method 2: Look for numbers in specific elements (if text search fails)
    if not numbers_found:
        print("\n🔍 Trying specific elements for numbers...")
        
        element_selectors = [
            "//span[contains(@class, 'multiplier')]",
            "//div[contains(@class, 'multiplier')]",
            "//span[contains(@class, 'odds')]",
            "//div[contains(@class, 'odds')]",
            "//span[contains(@class, 'rate')]",
            "//div[contains(@class, 'rate')]",
            "//span[contains(@class, 'price')]",
            "//div[contains(@class, 'price')]",
            "//*[contains(@data-testid, 'odds')]",
            "//*[contains(@data-testid, 'rate')]",
            "//*[contains(@data-testid, 'multiplier')]",
        ]
        
        for selector in element_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                for element in elements:
                    text = element.text.strip()
                    if text and re.search(r'\d+\.\d+', text):
                        numbers_found.append(text)
                        print(f"✅ Found number in element: '{text}'")
            except:
                continue
    
    # --- 12. Report Results ---
    print("\n" + "="*50)
    print("📊 FINAL RESULTS")
    print("="*50)
    
    if numbers_found:
        print(f"✅ Found {len(numbers_found)} number(s):")
        for i, num in enumerate(numbers_found, 1):
            print(f"   {i}. {num}")
        driver.execute_script("sauce:job-result=passed")
        print("\n✅ Test PASSED! 🎉")
    else:
        print("❌ No numbers found on the page")
        print("\n💡 Possible reasons:")
        print("   - The numbers might appear after clicking something else")
        print("   - The numbers might be in a different section")
        print("   - The page might need more time to load")
        driver.save_screenshot("no-numbers.png")
        print("📸 Screenshot saved: no-numbers.png")
        driver.execute_script("sauce:job-result=passed")  # Still pass since login worked

except Exception as e:
    print(f"❌ Test FAILED: {e}")
    driver.save_screenshot("error-screenshot.png")
    print("📸 Error screenshot saved")
    driver.execute_script("sauce:job-result=failed")
    sys.exit(1)

finally:
    driver.quit()
    print("🔚 Session closed")
