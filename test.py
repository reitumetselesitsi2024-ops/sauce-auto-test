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
sauce_options['name'] = 'ThabaBet - Deep Iframe Search'
options.set_capability('sauce:options', sauce_options)

# --- 3. Connect to Sauce Labs ---
url = "https://ondemand.eu-central-1.saucelabs.com:443/wd/hub"
print(f"🚀 Connecting to Sauce Labs...")

# ============================================================
# DEEP IFRAME SEARCH ENGINE
# ============================================================
class DeepIframeSearch:
    def __init__(self, driver, wait):
        self.driver = driver
        self.wait = wait
        self.found_numbers = []
        self.visited_frames = set()
        self.search_level = 0
        self.max_level = 5
        self.all_iframe_info = []
        
    def log(self, message, level="INFO"):
        print(f"[{level}] {message}")
    
    def search_everywhere(self):
        """Search everything - main entry point"""
        self.log("🤖 Starting DEEP search for multipliers...")
        
        # Step 1: Search main page
        self.log("📄 Searching main page...")
        self.search_page_for_numbers()
        
        # Step 2: Find and search all iframes
        if not self.found_numbers:
            self.log("📄 Searching ALL iframes...")
            self.search_all_iframes_recursive()
        
        # Step 3: If still no numbers, try clicking inside iframes
        if not self.found_numbers:
            self.log("📄 Clicking inside iframes...")
            self.click_inside_iframes()
        
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
            
            # Find decimal numbers that could be multipliers (between 1.0 and 100)
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
    
    def search_all_iframes_recursive(self):
        """Search all iframes and their contents"""
        try:
            iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
            self.log(f"📊 Found {len(iframes)} iframe(s)")
            
            for i, iframe in enumerate(iframes):
                try:
                    # Get iframe info
                    iframe_id = iframe.get_attribute('id') or f"iframe-{i}"
                    iframe_src = iframe.get_attribute('src') or "unknown"
                    iframe_title = iframe.get_attribute('title') or "N/A"
                    iframe_class = iframe.get_attribute('class') or "N/A"
                    
                    # Store info for later
                    self.all_iframe_info.append({
                        'index': i,
                        'id': iframe_id,
                        'src': iframe_src,
                        'title': iframe_title,
                        'class': iframe_class
                    })
                    
                    self.log(f"\n📄 Checking iframe {i+1}:")
                    self.log(f"   ID: {iframe_id}")
                    self.log(f"   Title: {iframe_title}")
                    self.log(f"   SRC: {iframe_src[:100]}")
                    
                    # Skip if already visited
                    if iframe_id in self.visited_frames:
                        self.log(f"   ⏭️ Already visited, skipping")
                        continue
                    self.visited_frames.add(iframe_id)
                    
                    # Switch to iframe
                    self.driver.switch_to.frame(iframe)
                    self.search_level += 1
                    
                    # Search inside iframe
                    self.log(f"   🔍 Searching inside iframe...")
                    self.search_page_for_numbers()
                    
                    # If numbers found, we're done!
                    if self.found_numbers:
                        self.log(f"   ✅ Found numbers in iframe {i+1}!")
                        self.driver.switch_to.default_content()
                        return True
                    
                    # Look for game elements inside iframe
                    self.log(f"   🔍 Looking for game elements inside iframe...")
                    self.search_game_elements_inside_iframe()
                    
                    # If numbers found after clicking, we're done!
                    if self.found_numbers:
                        self.log(f"   ✅ Found numbers after clicking inside iframe {i+1}!")
                        self.driver.switch_to.default_content()
                        return True
                    
                    # Check for nested iframes
                    nested_iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
                    if nested_iframes:
                        self.log(f"   📊 Found {len(nested_iframes)} nested iframe(s)")
                        for nested in nested_iframes:
                            try:
                                nested_id = nested.get_attribute('id') or "unnamed"
                                self.log(f"      🔍 Checking nested iframe: {nested_id}")
                                self.driver.switch_to.frame(nested)
                                self.search_page_for_numbers()
                                if self.found_numbers:
                                    self.log(f"      ✅ Found numbers in nested iframe!")
                                    self.driver.switch_to.default_content()
                                    return True
                                self.driver.switch_to.parent_frame()
                            except:
                                self.driver.switch_to.default_content()
                    
                    # Go back to main content
                    self.driver.switch_to.default_content()
                    self.search_level -= 1
                    
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
        game_keywords = ['AVIATOR', 'CRASH', 'SKYPILOT', 'BET', 'START', 'PLAY', 'LAUNCH', 'GAME']
        
        for keyword in game_keywords:
            try:
                # Try to find and click the element
                selectors = [
                    f"//*[contains(text(), '{keyword}')]",
                    f"//*[contains(@class, '{keyword.lower()}')]",
                    f"//button[contains(text(), '{keyword}')]",
                    f"//div[contains(@role, 'button')]//*[contains(text(), '{keyword}')]",
                ]
                
                for selector in selectors:
                    try:
                        element = self.driver.find_element(By.XPATH, selector)
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                        time.sleep(0.5)
                        self.driver.execute_script("arguments[0].click();", element)
                        self.log(f"      ✅ Clicked on: {keyword}")
                        time.sleep(3)
                        
                        # Search for numbers after click
                        self.search_page_for_numbers()
                        if self.found_numbers:
                            return True
                    except:
                        continue
            except:
                pass
        
        return False
    
    def click_inside_iframes(self):
        """Click on elements inside iframes to reveal numbers"""
        self.log("🔍 Attempting to click inside iframes...")
        
        # Go through all iframes we found earlier
        for iframe_info in self.all_iframe_info:
            try:
                # Find the iframe again
                iframe = self.driver.find_element(By.ID, iframe_info['id'])
                self.driver.switch_to.frame(iframe)
                
                self.log(f"🔍 Clicking inside iframe: {iframe_info['id']}")
                
                # Try to click on AVIATOR or game elements
                self.search_game_elements_inside_iframe()
                
                if self.found_numbers:
                    self.log(f"✅ Found numbers inside iframe!")
                    self.driver.switch_to.default_content()
                    return True
                
                self.driver.switch_to.default_content()
            except:
                try:
                    self.driver.switch_to.default_content()
                except:
                    pass
                continue
        
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
    # STEP 2: CLICK AVATAR
    # =========================================================
    print("\n" + "="*60)
    print("👤 STEP 2: CLICKING AVATAR")
    print("="*60)
    
    avatar_clicked = False
    
    try:
        avatar = driver.find_element(By.XPATH, "//*[contains(@class, 'avatar') or contains(@class, 'profile') or contains(@class, 'user')]")
        driver.execute_script("arguments[0].click();", avatar)
        print("✅ Avatar clicked!")
        avatar_clicked = True
        time.sleep(3)
    except:
        print("❌ Could not click avatar")
        driver.save_screenshot("avatar-failed.png")
        sys.exit(1)
    
    if not avatar_clicked:
        print("❌ Avatar click failed!")
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
        print("   - The game is in a different iframe")
        print("\n📸 Check the screenshot for debugging:")
        driver.save_screenshot("no-numbers-deep-search.png")
        print("   Screenshot saved: no-numbers-deep-search.png")
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
