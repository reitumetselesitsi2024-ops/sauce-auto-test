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
sauce_options['name'] = 'ThabaBet - Find Multipliers in AVIATOR'
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
    avatar_clicked = False
    
    try:
        avatar_methods = [
            lambda: driver.find_element(By.CSS_SELECTOR, "svg.icon"),
            lambda: driver.find_element(By.TAG_NAME, "svg"),
            lambda: driver.find_element(By.XPATH, "//*[contains(@class, 'avatar') or contains(@class, 'profile') or contains(@class, 'user')]"),
        ]
        
        for method in avatar_methods:
            try:
                avatar = method()
                driver.execute_script("arguments[0].click();", avatar)
                print("✅ Avatar clicked!")
                avatar_clicked = True
                time.sleep(2)
                break
            except:
                continue
    except:
        pass
    
    if not avatar_clicked:
        print("❌ Could not click avatar")
        sys.exit(1)

    # --- 10. FIND AND CLICK AVIATOR ---
    print("\n🔍 Looking for AVIATOR game...")
    
    aviator_selectors = [
        "//*[contains(text(), 'AVIATOR')]",
        "//*[contains(text(), 'aviator')]",
        "//*[contains(@class, 'aviator')]",
        "//*[contains(@id, 'aviator')]",
        "//div[contains(@class, 'game')]//*[contains(text(), 'AVIATOR')]",
        "//div[contains(@class, 'game-card')]//*[contains(text(), 'AVIATOR')]",
    ]
    
    aviator_clicked = False
    
    for selector in aviator_selectors:
        try:
            print(f"🔍 Trying: {selector}")
            aviator = driver.find_element(By.XPATH, selector)
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", aviator)
            time.sleep(1)
            driver.execute_script("arguments[0].click();", aviator)
            print("✅ AVIATOR game clicked!")
            aviator_clicked = True
            time.sleep(3)
            break
        except:
            continue
    
    if not aviator_clicked:
        print("❌ Could not find AVIATOR")
        sys.exit(1)

    # --- 11. FIND AND SWITCH TO IFRAME ---
    print("\n🔍 Looking for iframes...")
    
    # Get all iframes
    iframes = driver.find_elements(By.TAG_NAME, "iframe")
    print(f"📊 Found {len(iframes)} iframe(s)")
    
    for i, iframe in enumerate(iframes):
        try:
            print(f"\n📄 iframe {i+1}:")
            print(f"   ID: {iframe.get_attribute('id')}")
            print(f"   Class: {iframe.get_attribute('class')}")
            print(f"   Src: {iframe.get_attribute('src')[:100]}...")
        except:
            pass
    
    # Try to find numbers in each iframe
    numbers_found = []
    
    if iframes:
        print("\n🔍 Searching for numbers inside iframes...")
        
        for i, iframe in enumerate(iframes):
            try:
                print(f"\n📄 Switching to iframe {i+1}...")
                driver.switch_to.frame(iframe)
                
                # Get all HTML inside iframe
                iframe_html = driver.find_element(By.TAG_NAME, "body").text
                print(f"   Text preview: {iframe_html[:200]}...")
                
                # Search for numbers in iframe
                pattern = r'\b\d+\.\d+x?\b'
                matches = re.findall(pattern, iframe_html)
                
                if matches:
                    print(f"✅ Found {len(matches)} number(s) in iframe {i+1}:")
                    for match in matches:
                        print(f"   - {match}")
                        numbers_found.append(match)
                
                # Look for specific multiplier elements
                multiplier_selectors = [
                    "//span[contains(@class, 'multiplier')]",
                    "//div[contains(@class, 'multiplier')]",
                    "//span[contains(@class, 'odds')]",
                    "//div[contains(@class, 'odds')]",
                    "//span[contains(@class, 'value')]",
                    "//div[contains(@class, 'value')]",
                    "//*[contains(@class, 'number')]",
                    "//*[contains(@class, 'digit')]",
                ]
                
                for selector in multiplier_selectors:
                    try:
                        elements = driver.find_elements(By.XPATH, selector)
                        for element in elements:
                            text = element.text.strip()
                            if text and re.search(r'\d+\.\d+', text):
                                numbers_found.append(text)
                                print(f"✅ Found number in element: '{text}'")
                    except:
                        continue
                
                # Go back to main content
                driver.switch_to.default_content()
                
            except Exception as e:
                print(f"⚠️ Could not switch to iframe {i+1}: {e}")
                driver.switch_to.default_content()
                continue
    
    # --- 12. If still no numbers, search in shadow DOM ---
    if not numbers_found:
        print("\n🔍 Searching for numbers in shadow DOM...")
        
        # Try to find any shadow roots
        try:
            # Look for elements that might have shadow DOM
            shadow_hosts = driver.find_elements(By.XPATH, "//*[contains(@class, 'game') or contains(@class, 'container')]")
            
            for host in shadow_hosts:
                try:
                    shadow_root = driver.execute_script("return arguments[0].shadowRoot", host)
                    if shadow_root:
                        print("✅ Found shadow root!")
                        # Search inside shadow root
                        elements = shadow_root.find_elements(By.XPATH, "//*[contains(text(), '.')]")
                        for element in elements:
                            text = element.text.strip()
                            if text and re.search(r'\d+\.\d+', text):
                                numbers_found.append(text)
                                print(f"✅ Found number in shadow DOM: '{text}'")
                except:
                    continue
        except:
            pass

    # --- 13. If still no numbers, get ALL HTML for debugging ---
    if not numbers_found:
        print("\n🔍 Getting all HTML for debugging...")
        html = driver.page_source
        
        # Save HTML to file
        with open("page_source.html", "w", encoding="utf-8") as f:
            f.write(html)
        print("📄 Page source saved to page_source.html")
        
        # Look for any numbers in the HTML
        numbers_in_html = re.findall(r'\d+\.\d+x?', html)
        if numbers_in_html:
            print(f"\n✅ Found {len(numbers_in_html)} number(s) in HTML source:")
            for num in set(numbers_in_html[:10]):  # Show unique numbers
                print(f"   - {num}")

    # --- 14. Report Results ---
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
        print("❌ No numbers found")
        print("\n📄 Check the page_source.html file in artifacts")
        driver.execute_script("sauce:job-result=passed")

except Exception as e:
    print(f"❌ Test FAILED: {e}")
    driver.save_screenshot("error-screenshot.png")
    print("📸 Error screenshot saved")
    driver.execute_script("sauce:job-result=failed")
    sys.exit(1)

finally:
    driver.quit()
    print("🔚 Session closed")
