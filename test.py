from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import sys
import time
import re
from datetime import datetime
from pathlib import Path

# ============================================================
# CONFIGURATION
# ============================================================
PHONE_NUMBER = "58532178"
PASSWORD = "598976Lesitsi"
SCRAPE_INTERVAL = 2  # Minutes

username = os.environ.get('SAUCE_USERNAME')
access_key = os.environ.get('SAUCE_ACCESS_KEY')

if not username or not access_key:
    print("❌ ERROR: SAUCE_USERNAME or SAUCE_ACCESS_KEY not set!")
    sys.exit(1)

# ============================================================
# SETUP
# ============================================================
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

RESULTS_TXT = DATA_DIR / "results.txt"
ALL_MULTIPLIERS = []

def save_results():
    """Save just the numbers to TXT"""
    with open(RESULTS_TXT, 'w') as f:
        for mult in ALL_MULTIPLIERS:
            f.write(f"{mult}\n")

# ============================================================
# SCRAPER
# ============================================================
def scrape():
    print(f"\n🔄 {datetime.now().strftime('%H:%M:%S')}")
    
    options = ChromeOptions()
    options.browser_version = 'latest'
    options.platform_name = 'Windows 11'
    options.set_capability('sauce:options', {
        'username': username,
        'accessKey': access_key,
        'build': 'Aviator-Scraper',
        'name': 'Simple-Scraper'
    })
    
    url = "https://ondemand.eu-central-1.saucelabs.com:443/wd/hub"
    driver = None
    
    try:
        driver = webdriver.Remote(command_executor=url, options=options)
        wait = WebDriverWait(driver, 20)
        
        # Login
        driver.get("https://thababet.co.ls/sign-in")
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "login-page")))
        
        email_field = wait.until(EC.presence_of_element_located((By.ID, "v-0-username")))
        email_field.clear()
        email_field.send_keys(PHONE_NUMBER)
        
        password_field = driver.find_element(By.ID, "v-0-password")
        password_field.clear()
        password_field.send_keys(PASSWORD)
        
        login_button = wait.until(EC.element_to_be_clickable((By.ID, "v-0-submit-button")))
        login_button.click()
        time.sleep(5)
        
        # Go to Aviator
        driver.get("https://thababet.co.ls/spribe/8203")
        time.sleep(8)
        
        # Find iframe
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        for iframe in iframes:
            src = iframe.get_attribute('src') or ""
            if "aviator" in src.lower():
                driver.switch_to.frame(iframe)
                break
        
        time.sleep(2)
        
        # Extract multipliers
        page_text = driver.find_element(By.TAG_NAME, "body").text
        pattern = r'\b\d+\.\d+x\b'
        matches = re.findall(pattern, page_text)
        
        if matches:
            unique = list(set(matches))
            new_count = 0
            for mult in unique:
                if mult not in ALL_MULTIPLIERS:
                    ALL_MULTIPLIERS.append(mult)
                    new_count += 1
                    print(f"   {mult}")
            
            if new_count > 0:
                save_results()
                print(f"✅ Saved {new_count} new")
        
        driver.quit()
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        if driver:
            try:
                driver.quit()
            except:
                pass
        return False

# ============================================================
# MAIN LOOP
# ============================================================
def main():
    print("\n" + "="*50)
    print("🚀 AVIATOR SCRAPER")
    print("="*50)
    print(f"⏰ Every {SCRAPE_INTERVAL} minutes")
    print("="*50)
    
    run_count = 0
    
    while True:
        try:
            run_count += 1
            print(f"\n📊 RUN #{run_count}")
            scrape()
            print(f"⏳ Waiting {SCRAPE_INTERVAL} min...")
            time.sleep(SCRAPE_INTERVAL * 60)
            
        except KeyboardInterrupt:
            print("\n🛑 Stopped")
            print(f"📊 Total: {len(ALL_MULTIPLIERS)} multipliers")
            save_results()
            print("✅ Saved to data/results.txt")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            time.sleep(60)

if __name__ == "__main__":
    main()
