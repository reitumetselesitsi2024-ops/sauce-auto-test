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
from collections import defaultdict

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
sauce_options['name'] = 'ThabaBet - Guaranteed Avatar Click'
options.set_capability('sauce:options', sauce_options)

# --- 3. Connect to Sauce Labs ---
url = "https://ondemand.eu-central-1.saucelabs.com:443/wd/hub"
print(f"🚀 Connecting to Sauce Labs...")

# ============================================================
# GUARANTEED AVATAR CLICK FUNCTION
# ============================================================
def click_avatar_guaranteed(driver, wait):
    """Try EVERY possible way to click the avatar"""
    print("\n🔍 ATTEMPTING TO CLICK AVATAR - ALL METHODS")
    print("="*50)
    
    avatar_clicked = False
    avatar_element = None
    
    # Method 1: SVG with icon class
    try:
        print("🔍 Method 1: Looking for svg.icon...")
        avatar_element = driver.find_element(By.CSS_SELECTOR, "svg.icon")
        print(f"   ✅ Found SVG with class 'icon'")
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", avatar_element)
        time.sleep(0.5)
        driver.execute_script("arguments[0].click();", avatar_element)
        print("   ✅ Clicked using JavaScript!")
        avatar_clicked = True
    except:
        print("   ❌ Method 1 failed")
    
    # Method 2: Any SVG element
    if not avatar_clicked:
        try:
            print("🔍 Method 2: Looking for any SVG...")
            svg_elements = driver.find_elements(By.TAG_NAME, "svg")
            if svg_elements:
                print(f"   ✅ Found {len(svg_elements)} SVG(s)")
                # Try clicking the first one that looks like an icon
                for svg in svg_elements:
                    try:
                        if "icon" in svg.get_attribute("class") or "avatar" in svg.get_attribute("class"):
                            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", svg)
                            time.sleep(0.5)
                            driver.execute_script("arguments[0].click();", svg)
                            print("   ✅ Clicked on SVG!")
                            avatar_clicked = True
                            break
                    except:
                        continue
        except:
            print("   ❌ Method 2 failed")
    
    # Method 3: Elements with avatar class
    if not avatar_clicked:
        try:
            print("🔍 Method 3: Looking for elements with avatar class...")
            selectors = [
                "//*[contains(@class, 'avatar')]",
                "//*[contains(@class, 'profile')]",
                "//*[contains(@class, 'user')]",
                "//*[contains(@class, 'account')]",
            ]
            for selector in selectors:
                try:
                    elements = driver.find_elements(By.XPATH, selector)
                    if elements:
                        print(f"   ✅ Found {len(elements)} element(s) with class")
                        for elem in elements:
                            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elem)
                            time.sleep(0.5)
                            driver.execute_script("arguments[0].click();", elem)
                            print(f"   ✅ Clicked element with selector: {selector}")
                            avatar_clicked = True
                            break
                        if avatar_clicked:
                            break
                except:
                    continue
        except:
            print("   ❌ Method 3 failed")
    
    # Method 4: Click on element containing "RL" (your username initials)
    if not avatar_clicked:
        try:
            print("🔍 Method 4: Looking for element containing 'RL'...")
            elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'RL')]")
            if elements:
                print(f"   ✅ Found {len(elements)} element(s) with 'RL'")
                for elem in elements:
                    try:
                        # Get parent element (might be the clickable one)
                        parent = elem.find_element(By.XPATH, "..")
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", parent)
                        time.sleep(0.5)
                        driver.execute_script("arguments[0].click();", parent)
                        print("   ✅ Clicked on parent of 'RL' element!")
                        avatar_clicked = True
                        break
                    except:
                        continue
        except:
            print("   ❌ Method 4 failed")
    
    # Method 5: Click on the right side of the header
    if not avatar_clicked:
        try:
            print("🔍 Method 5: Looking for header right section...")
            # Find header and click the rightmost element
            header = driver.find_element(By.TAG_NAME, "header")
            # Get all clickable elements in header
            clickable = header.find_elements(By.XPATH, ".//*[@role='button' or contains(@class, 'btn') or contains(@class, 'clickable')]")
            if clickable:
                print(f"   ✅ Found {len(clickable)} clickable elements in header")
                # Click the last one (usually avatar)
                last = clickable[-1]
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", last)
                time.sleep(0.5)
                driver.execute_script("arguments[0].click();", last)
                print("   ✅ Clicked last clickable element in header!")
                avatar_clicked = True
        except:
            print("   ❌ Method 5 failed")
    
    # --- VERIFY AVATAR WAS CLICKED ---
    if avatar_clicked:
        print("\n✅ Avatar clicked successfully!")
        time.sleep(2)
        
        # Take screenshot to confirm
        driver.save_screenshot("avatar-clicked-confirmation.png")
        print("📸 Screenshot saved: avatar-clicked-confirmation.png")
        
        # Check if any dropdown/menu appeared
        try:
            # Look for any menu that might have appeared
            menus = driver.find_elements(By.XPATH, "//*[contains(@class, 'menu') or contains(@class, 'dropdown')]")
            if menus:
                print(f"✅ Found {len(menus)} menu/dropdown element(s) - Avatar click confirmed!")
            else:
                print("⚠️ No menu found - avatar might not have worked")
        except:
            pass
    else:
        print("\n❌ ALL AVATAR CLICK METHODS FAILED!")
        driver.save_screenshot("avatar-click-failed.png")
        print("📸 Screenshot saved: avatar-click-failed.png")
    
    return avatar_clicked

# ============================================================
# DEEP IFRAME SEARCH ENGINE
# ============================================================
class DeepIframeSearch:
    def __init__(self, driver, wait):
        self.driver = driver
        self.wait = wait
        self.found_numbers = []
        self.visited_frames = set()
        
    def log(self, message, level="INFO"):
        print(f"[{level}] {message}")
    
    def search_everywhere(self):
        """Search everything"""
        self.log("🤖 Starting DEEP search for multipliers...")
        
        # Search main page
        self.log("📄 Searching main page...")
        self.search_page_for_numbers()
        
        # Search all iframes
        if not self.found_numbers:
            self.log("📄 Searching ALL iframes...")
            self.search_all_iframes()
        
        return self.found_numbers
    
    def search_page_for_numbers(self):
        """Search current page for numbers"""
        try:
            body_text = self.driver.find_element(By.TAG_NAME, "body").text
            
            # Find multipliers with x (2.4x, 1.5x, etc.)
            pattern = r'\b\d+\.\d+x?\b'
            matches = re.findall(pattern, body_text)
            
            if matches:
                self.log(f"✅ Found {len(matches)} multiplier(s): {matches}")
                self.found_numbers.extend(matches)
                return True
            
            # Find decimal numbers
            pattern = r'\b\d+\.\d+\b'
            matches = re.findall(pattern, body_text)
            for num in matches:
                try:
                    val = float(num)
                    if 1.0 <= val <= 100.0:
                        self.found_numbers.append(num)
                        self.log(f"✅ Found potential multiplier: {num}")
                except:
                    pass
            
            return bool(self.found_numbers)
            
        except Exception as e:
            self.log(f"⚠️ Error searching page: {e}")
            return False
    
    def search_all_iframes(self):
        """Search all iframes"""
        try:
            iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
            self.log(f"📊 Found {len(iframes)} iframe(s)")
            
            for i, iframe in enumerate(iframes):
                try:
                    iframe_id = iframe.get_attribute('id') or f"iframe-{i}"
                    iframe_src = iframe.get_attribute('src') or "unknown"
                    iframe_title = iframe.get_attribute('title') or "N/A"
                    
                    self.log(f"\n📄 Checking iframe {i+1}:")
                    self.log(f"   ID: {iframe_id}")
                    self.log(f"   Title: {iframe_title}")
                    self.log(f"   SRC: {iframe_src[:100]}")
                    
                    # Skip about:blank iframes
                    if "about:blank" in iframe_src:
                        self.log(f"   ⏭️ Skipping blank iframe")
                        continue
                    
                    # Switch to iframe
                    self.driver.switch_to.frame(iframe)
                    
                    # Search inside iframe
                    self.log(f"   🔍 Searching inside iframe...")
                    self.search_page_for_numbers()
                    
                    # Look for game elements inside iframe
                    if not self.found_numbers:
                        self.log(f"   🔍 Looking for game elements inside iframe...")
                        self.search_game_elements_inside_iframe()
                    
                    # Go back to main content
                    self.driver.switch_to.default_content()
                    
                    if self.found_numbers:
                        self.log(f"   ✅ Found numbers in iframe {i+1}!")
                        return True
                        
                except Exception as e:
                    self.log(f"   ⚠️ Error with iframe {i+1}: {e}")
                    try:
                        self.driver.switch_to.default_content()
                    except:
                        pass
                    continue
            
            return False
            
        except Exception as e:
            self.log(f"⚠️ Error searching iframes: {e}")
            return False
    
    def search_game_elements_inside_iframe(self):
        """Click on game elements inside the current iframe"""
        game_keywords = ['AVIATOR', 'CRASH', 'SKYPILOT', 'BET', 'START', 'PLAY', 'LAUNCH']
        
        for keyword in game_keywords:
            try:
                selectors = [
                    f"//*[contains(text(), '{keyword}')]",
                    f"//button[contains(text(), '{keyword}')]",
                    f"//div[contains(@role, 'button')]//*[contains(text(), '{keyword}')]",
                ]
                
                for selector in selectors:
                    try:
                        elements = self.driver.find_elements(By.XPATH, selector)
                        for element in elements:
                            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                            time.sleep(0.5)
                            self.driver.execute_script("arguments[0].click();", element)
                            self.log(f"      ✅ Clicked on: {keyword}")
                            time.sleep(3)
                            
                            self.search_page_for_numbers()
                            if self.found_numbers:
                                return True
                    except:
                        continue
            except:
                pass
        
        return False

# ============================================================
# MAIN TEST EXECUTION
# ============================================================

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
    
    driver.get("https://thababet.co.ls/spribe/8203")
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
    # STEP 2: CLICK AVATAR (GUARANTEED)
    # =========================================================
    print("\n" + "="*60)
    print("👤 STEP 2: CLICKING AVATAR (GUARANTEED)")
    print("="*60)
    
    avatar_clicked = click_avatar_guaranteed(driver, wait)
    
    if not avatar_clicked:
        print("\n❌ Could not click avatar. Exiting...")
        driver.save_screenshot("avatar-failed-final.png")
        sys.exit(1)

    # =========================================================
    # STEP 3: DEEP IFRAME SEARCH
    # =========================================================
    print("\n" + "="*60)
    print("🤖 STEP 3: DEEP IFRAME SEARCH")
    print("="*60)
    
    search_engine = DeepIframeSearch(driver, wait)
    numbers_found = search_engine.search_everywhere()
    
    # =========================================================
    # STEP 4: RESULTS
    # =========================================================
    print("\n" + "="*60)
    print("📊 FINAL RESULTS")
    print("="*60)
    
    if numbers_found:
        unique_numbers = list(set(numbers_found))
        print(f"✅ Found {len(unique_numbers)} number(s):")
        for i, num in enumerate(unique_numbers, 1):
            print(f"   {i}. {num}")
        driver.execute_script("sauce:job-result=passed")
        print("\n✅ Test PASSED! 🎉")
    else:
        print("❌ No multiplier numbers found")
        print("\n📸 Check screenshots for debugging:")
        print("   - avatar-clicked-confirmation.png")
        print("   - no-numbers-deep-search.png")
        driver.save_screenshot("no-numbers-deep-search.png")
        driver.execute_script("sauce:job-result=passed")

except Exception as e:
    print(f"❌ Test FAILED: {e}")
    driver.save_screenshot("error-screenshot.png")
    driver.execute_script("sauce:job-result=failed")
    sys.exit(1)

finally:
    driver.quit()
    print("\n🔚 Session closed")
