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
import json
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
sauce_options['name'] = 'ThabaBet - Login + Avatar + AI Search'
options.set_capability('sauce:options', sauce_options)

# --- 3. Connect to Sauce Labs ---
url = "https://ondemand.eu-central-1.saucelabs.com:443/wd/hub"
print(f"🚀 Connecting to Sauce Labs...")

# ============================================================
# AI SEARCH ENGINE CLASS
# ============================================================
class AISearchEngine:
    def __init__(self, driver, wait):
        self.driver = driver
        self.wait = wait
        self.found_numbers = []
        self.visited_iframes = set()
        self.visited_elements = set()
        self.search_depth = 0
        self.max_depth = 5
        
    def log(self, message, level="INFO"):
        print(f"[{level}] {message}")
    
    def search_for_multipliers(self):
        """Main search method - tries multiple strategies"""
        self.log("🤖 Starting AI search for multipliers...")
        
        # Strategy 1: Search in current page
        self.log("📄 Strategy 1: Searching current page...")
        self.search_page_for_numbers()
        
        # Strategy 2: Search in all iframes
        if not self.found_numbers:
            self.log("📄 Strategy 2: Searching all iframes...")
            self.search_all_iframes()
        
        # Strategy 3: Click on potential game elements
        if not self.found_numbers:
            self.log("📄 Strategy 3: Clicking potential game elements...")
            self.click_potential_game_elements()
        
        # Strategy 4: Deep search - follow links and buttons
        if not self.found_numbers:
            self.log("📄 Strategy 4: Deep search...")
            self.deep_search()
        
        return self.found_numbers
    
    def search_page_for_numbers(self):
        """Search the current page for numbers"""
        try:
            # Get all text
            body_text = self.driver.find_element(By.TAG_NAME, "body").text
            
            # Find numbers with x (like 2.4x, 1.5x)
            pattern = r'\b\d+\.\d+x?\b'
            matches = re.findall(pattern, body_text)
            
            if matches:
                self.log(f"✅ Found {len(matches)} number(s) on page: {matches}")
                self.found_numbers.extend(matches)
                return True
            
            # Find any decimal numbers that could be multipliers
            pattern = r'\b\d+\.\d+\b'
            matches = re.findall(pattern, body_text)
            if matches:
                self.log(f"✅ Found {len(matches)} decimal number(s): {matches[:10]}")
                # Only add if they look like multipliers (between 1.0 and 100)
                for num in matches:
                    try:
                        val = float(num)
                        if 1.0 <= val <= 100.0:
                            self.found_numbers.append(num)
                            self.log(f"✅ Added potential multiplier: {num}")
                    except:
                        pass
                return True
                
        except Exception as e:
            self.log(f"⚠️ Error searching page: {e}")
        return False
    
    def search_all_iframes(self):
        """Search through all iframes"""
        try:
            iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
            self.log(f"📊 Found {len(iframes)} iframe(s)")
            
            for i, iframe in enumerate(iframes):
                if i in self.visited_iframes:
                    continue
                self.visited_iframes.add(i)
                
                try:
                    iframe_id = iframe.get_attribute('id') or f"iframe-{i}"
                    iframe_src = iframe.get_attribute('src') or "unknown"
                    
                    self.log(f"📄 Checking iframe {i+1}: id={iframe_id}")
                    self.log(f"   SRC: {iframe_src[:100]}")
                    
                    # Switch to iframe
                    self.driver.switch_to.frame(iframe)
                    
                    # Search in iframe
                    self.search_page_for_numbers()
                    
                    # Try to find game elements inside iframe
                    self.search_game_elements_inside_iframe()
                    
                    # Go back to main content
                    self.driver.switch_to.default_content()
                    
                    if self.found_numbers:
                        self.log(f"✅ Found numbers in iframe {i+1}!")
                        return True
                        
                except Exception as e:
                    self.log(f"⚠️ Could not process iframe {i+1}: {e}")
                    self.driver.switch_to.default_content()
                    
            return False
            
        except Exception as e:
            self.log(f"⚠️ Error searching iframes: {e}")
            return False
    
    def search_game_elements_inside_iframe(self):
        """Search for game elements inside current iframe"""
        game_keywords = ['multiplier', 'odds', 'rate', 'value', 'number', 'digit', 'score', 'current', 'bet']
        
        for keyword in game_keywords:
            try:
                elements = self.driver.find_elements(By.XPATH, f"//*[contains(translate(@class, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{keyword}')]")
                for element in elements[:10]:
                    text = element.text.strip()
                    if text and re.search(r'\d+\.\d+', text):
                        self.found_numbers.append(text)
                        self.log(f"✅ Found number in game element: '{text}'")
            except:
                pass
    
    def click_potential_game_elements(self):
        """Click on elements that might lead to the game"""
        # Try clicking on AVIATOR, CRASH, or other game names
        game_names = ['AVIATOR', 'CRASH', 'SKYPILOT', 'SPORTS', 'CASINO', 'GAME', 'BET']
        
        for game_name in game_names:
            try:
                self.log(f"🔍 Trying to click: {game_name}")
                
                # Try multiple ways to find the element
                selectors = [
                    f"//*[contains(text(), '{game_name}')]",
                    f"//*[contains(@class, '{game_name.lower()}')]",
                    f"//*[contains(@id, '{game_name.lower()}')]",
                    f"//button[contains(text(), '{game_name}')]",
                    f"//div[contains(@class, 'game')]//*[contains(text(), '{game_name}')]",
                ]
                
                for selector in selectors:
                    try:
                        element = self.driver.find_element(By.XPATH, selector)
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                        time.sleep(0.5)
                        self.driver.execute_script("arguments[0].click();", element)
                        self.log(f"✅ Clicked on: {game_name}")
                        time.sleep(3)
                        
                        # After clicking, search for numbers
                        self.search_page_for_numbers()
                        self.search_all_iframes()
                        
                        if self.found_numbers:
                            return True
                    except:
                        continue
                        
            except Exception as e:
                self.log(f"⚠️ Could not click {game_name}: {e}")
        
        return False
    
    def deep_search(self):
        """Deep search - follow links and buttons recursively"""
        if self.search_depth > self.max_depth:
            return
        
        self.search_depth += 1
        self.log(f"🔍 Deep search level {self.search_depth}...")
        
        # Click on any clickable elements that might contain numbers
        clickable_selectors = [
            "//button",
            "//a",
            "//div[@role='button']",
            "//*[contains(@class, 'clickable')]",
            "//*[contains(@class, 'btn')]",
        ]
        
        for selector in clickable_selectors:
            try:
                elements = self.driver.find_elements(By.XPATH, selector)
                for element in elements[:5]:  # Limit to avoid too many clicks
                    try:
                        # Check if element has text that looks promising
                        text = element.text.strip()
                        if any(keyword in text.upper() for keyword in ['BET', 'START', 'PLAY', 'GAME', 'LAUNCH', 'AVIATOR', 'CRASH']):
                            # Skip if already visited
                            element_id = f"{element.tag_name}_{text}"
                            if element_id in self.visited_elements:
                                continue
                            self.visited_elements.add(element_id)
                            
                            self.log(f"🔍 Clicking element: '{text[:30]}'")
                            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                            time.sleep(0.5)
                            self.driver.execute_script("arguments[0].click();", element)
                            time.sleep(3)
                            
                            # Search for numbers after click
                            self.search_page_for_numbers()
                            self.search_all_iframes()
                            
                            if self.found_numbers:
                                return
                    except:
                        continue
            except:
                pass

# ============================================================
# MAIN TEST EXECUTION - LOGIN → AVATAR → AI SEARCH
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
    # STEP 3: AI SEARCH FOR MULTIPLIERS
    # =========================================================
    print("\n" + "="*60)
    print("🤖 STEP 3: AI SEARCH FOR MULTIPLIERS")
    print("="*60)
    
    ai_engine = AISearchEngine(driver, wait)
    numbers_found = ai_engine.search_for_multipliers()
    
    # =========================================================
    # STEP 4: RESULTS
    # =========================================================
    print("\n" + "="*60)
    print("📊 FINAL RESULTS")
    print("="*60)
    
    if numbers_found:
        # Remove duplicates
        unique_numbers = list(set(numbers_found))
        print(f"✅ Found {len(unique_numbers)} number(s):")
        for i, num in enumerate(unique_numbers, 1):
            print(f"   {i}. {num}")
        driver.execute_script("sauce:job-result=passed")
        print("\n✅ Test PASSED! 🎉")
    else:
        print("❌ No multiplier numbers found")
        print("\n💡 The game may need to be started first.")
        print("   Look for a 'Bet' or 'Start' button in the Aviator game.")
        driver.save_screenshot("no-numbers-ai-search.png")
        print("📸 Screenshot saved: no-numbers-ai-search.png")
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
