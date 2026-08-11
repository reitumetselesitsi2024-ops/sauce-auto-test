from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import sys
import time
import re
import json
from selenium.webdriver.common.action_chains import ActionChains

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
sauce_options['name'] = 'ThabaBet - Debug After Avatar'
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
        # Try multiple methods to find avatar
        avatar_methods = [
            ("svg.icon", By.CSS_SELECTOR),
            ("svg", By.TAG_NAME),
            ("//*[contains(@class, 'avatar') or contains(@class, 'profile') or contains(@class, 'user')]", By.XPATH),
            ("//*[contains(@id, 'avatar') or contains(@id, 'profile')]", By.XPATH),
            ("//button[contains(@aria-label, 'profile')]", By.XPATH),
            ("//img[contains(@alt, 'avatar') or contains(@alt, 'profile')]", By.XPATH),
        ]
        
        for selector, by in avatar_methods:
            try:
                if by == By.CSS_SELECTOR:
                    avatar = driver.find_element(by, selector)
                else:
                    avatar = driver.find_element(by, selector)
                driver.execute_script("arguments[0].click();", avatar)
                print(f"✅ Avatar clicked using selector: {selector}")
                avatar_clicked = True
                time.sleep(3)
                break
            except:
                continue
    except:
        pass
    
    if not avatar_clicked:
        print("❌ Could not click avatar")
        driver.save_screenshot("avatar-failed.png")
        sys.exit(1)

    # ============================================================
    # --- 10. DEBUG: FIND EVERYTHING ON THE PAGE ---
    # ============================================================
    
    print("\n" + "="*60)
    print("🔍 DEBUGGING: SCANNING PAGE AFTER AVATAR CLICK")
    print("="*60)
    
    # --- A. Save full page HTML ---
    print("\n📄 Saving full page HTML...")
    html = driver.page_source
    with open("page_after_avatar.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("✅ HTML saved to page_after_avatar.html")
    
    # --- B. Find ALL clickable elements ---
    print("\n🔍 Finding ALL clickable elements...")
    
    all_elements = []
    
    # Get all buttons
    buttons = driver.find_elements(By.TAG_NAME, "button")
    print(f"📊 Found {len(buttons)} buttons")
    for i, btn in enumerate(buttons[:10]):  # First 10
        try:
            text = btn.text.strip()
            if text:
                print(f"   Button {i+1}: '{text[:50]}'")
                all_elements.append({'type': 'button', 'text': text})
        except:
            pass
    
    # Get all links
    links = driver.find_elements(By.TAG_NAME, "a")
    print(f"\n📊 Found {len(links)} links")
    for i, link in enumerate(links[:10]):  # First 10
        try:
            text = link.text.strip()
            href = link.get_attribute('href')
            if text:
                print(f"   Link {i+1}: '{text[:50]}' -> {href[:50] if href else 'N/A'}")
                all_elements.append({'type': 'link', 'text': text, 'href': href})
        except:
            pass
    
    # Get all divs with clickable roles
    clickable_divs = driver.find_elements(By.XPATH, "//div[@role='button' or contains(@class, 'clickable')]")
    print(f"\n📊 Found {len(clickable_divs)} clickable divs")
    for i, div in enumerate(clickable_divs[:10]):
        try:
            text = div.text.strip()
            if text:
                print(f"   Div {i+1}: '{text[:50]}'")
                all_elements.append({'type': 'clickable_div', 'text': text})
        except:
            pass
    
    # --- C. Find GAME elements ---
    print("\n🔍 Searching for GAME-related elements...")
    
    game_keywords = ['game', 'aviator', 'crash', 'sky', 'casino', 'lottery', 'bet', 'spin', 'rapid', 'horse', 'virtual']
    game_elements = []
    
    for keyword in game_keywords:
        try:
            elements = driver.find_elements(By.XPATH, f"//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{keyword}')]")
            if elements:
                print(f"   Found {len(elements)} element(s) containing '{keyword}'")
                for elem in elements[:5]:
                    try:
                        text = elem.text.strip()
                        if text:
                            print(f"      - '{text[:60]}'")
                            game_elements.append({'keyword': keyword, 'text': text, 'element': elem})
                    except:
                        pass
        except:
            continue
    
    # --- D. Check for iframes ---
    print("\n🔍 Checking for iframes...")
    iframes = driver.find_elements(By.TAG_NAME, "iframe")
    print(f"📊 Found {len(iframes)} iframe(s)")
    
    for i, iframe in enumerate(iframes):
        try:
            src = iframe.get_attribute('src') or 'N/A'
            id_val = iframe.get_attribute('id') or 'N/A'
            class_val = iframe.get_attribute('class') or 'N/A'
            print(f"   iframe {i+1}:")
            print(f"      ID: {id_val}")
            print(f"      Class: {class_val}")
            print(f"      Src: {src[:100]}")
            
            # Try to switch to iframe and get content
            try:
                driver.switch_to.frame(iframe)
                iframe_text = driver.find_element(By.TAG_NAME, "body").text
                print(f"      Content preview: {iframe_text[:100]}...")
                
                # Search for numbers in iframe
                pattern = r'\d+\.\d+'
                matches = re.findall(pattern, iframe_text)
                if matches:
                    print(f"      ✅ Found numbers: {matches[:5]}")
                
                driver.switch_to.default_content()
            except:
                print("      ⚠️ Could not access iframe content")
                driver.switch_to.default_content()
        except Exception as e:
            print(f"   iframe {i+1}: Error - {e}")
    
    # --- E. Find any numbers anywhere ---
    print("\n🔍 Searching for numbers in page text...")
    body_text = driver.find_element(By.TAG_NAME, "body").text
    pattern = r'\d+\.\d+'
    numbers = re.findall(pattern, body_text)
    
    if numbers:
        print(f"✅ Found {len(numbers)} number(s) in page text:")
        unique_numbers = list(set(numbers))
        for num in unique_numbers[:20]:
            print(f"   - {num}")
    else:
        print("❌ No numbers found in page text")
    
    # --- F. Check shadow DOM ---
    print("\n🔍 Checking for shadow DOM...")
    try:
        # Look for elements that might have shadow roots
        possible_shadow_hosts = driver.find_elements(By.XPATH, "//*[contains(@class, 'game') or contains(@class, 'container') or contains(@class, 'wrapper')]")
        shadow_found = False
        
        for host in possible_shadow_hosts[:10]:
            try:
                shadow_root = driver.execute_script("return arguments[0].shadowRoot", host)
                if shadow_root:
                    shadow_found = True
                    print(f"✅ Found shadow root on element: {host.get_attribute('class')}")
                    # Try to get content
                    try:
                        shadow_text = shadow_root.text
                        if shadow_text:
                            print(f"   Shadow content preview: {shadow_text[:100]}")
                    except:
                        pass
            except:
                continue
        
        if not shadow_found:
            print("❌ No shadow DOM found")
    except:
        print("⚠️ Could not check shadow DOM")

    # --- G. Take screenshot ---
    driver.save_screenshot("debug_after_avatar.png")
    print("\n📸 Screenshot saved: debug_after_avatar.png")
    
    # --- H. Try to find ANY clickable game element and click it ---
    print("\n🔍 Trying to click on any game-related element...")
    
    # Try clicking on elements that might be games
    game_selectors = [
        "//*[contains(text(), 'Sports')]",
        "//*[contains(text(), 'Betting')]",
        "//*[contains(text(), 'Crash')]",
        "//*[contains(text(), 'Casino')]",
        "//*[contains(text(), 'Lotto')]",
        "//div[contains(@class, 'game')]",
        "//div[contains(@role, 'button')]",
    ]
    
    clicked_anything = False
    for selector in game_selectors:
        try:
            print(f"🔍 Trying to click: {selector}")
            elem = driver.find_element(By.XPATH, selector)
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elem)
            time.sleep(0.5)
            driver.execute_script("arguments[0].click();", elem)
            print(f"✅ Clicked: {selector}")
            clicked_anything = True
            time.sleep(2)
            break
        except:
            continue
    
    if clicked_anything:
        # Take screenshot after clicking
        driver.save_screenshot("debug_after_click.png")
        print("📸 Screenshot saved: debug_after_click.png")
    
    # --- I. Final report ---
    print("\n" + "="*60)
    print("📊 DEBUG SUMMARY")
    print("="*60)
    print(f"✅ Total buttons found: {len(buttons)}")
    print(f"✅ Total links found: {len(links)}")
    print(f"✅ Total iframes found: {len(iframes)}")
    print(f"✅ Game-related elements found: {len(game_elements)}")
    print(f"✅ Numbers found in page text: {len(numbers)}")
    print("\n📄 Full HTML saved to: page_after_avatar.html")
    print("📸 Screenshot saved to: debug_after_avatar.png")
    
    driver.execute_script("sauce:job-result=passed")
    print("\n✅ Test COMPLETED! Check the HTML file and screenshots for debugging.")

except Exception as e:
    print(f"❌ Test FAILED: {e}")
    driver.save_screenshot("error-screenshot.png")
    print("📸 Error screenshot saved")
    driver.execute_script("sauce:job-result=failed")
    sys.exit(1)

finally:
    driver.quit()
    print("🔚 Session closed")
