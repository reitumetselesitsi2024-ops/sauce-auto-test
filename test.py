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
import csv
import subprocess
from datetime import datetime
from pathlib import Path

# ============================================================
# ⚙️ CONFIGURATION - EDIT THESE VALUES
# ============================================================
PHONE_NUMBER = "58532178"  # <-- CHANGE THIS
PASSWORD = "598976Lesitsi"     # <-- CHANGE THIS
SCRAPE_INTERVAL = 5          # Minutes between scrapes (default: 5)

# Sauce Labs credentials (from GitHub Secrets)
username = os.environ.get('SAUCE_USERNAME')
access_key = os.environ.get('SAUCE_ACCESS_KEY')

if not username or not access_key:
    print("❌ ERROR: SAUCE_USERNAME or SAUCE_ACCESS_KEY not set!")
    sys.exit(1)

# ============================================================
# DATA STORAGE
# ============================================================
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

CSV_FILE = DATA_DIR / "multipliers.csv"
JSON_FILE = DATA_DIR / "multipliers.json"

def load_existing_multipliers():
    """Load previously saved multipliers to avoid duplicates"""
    if CSV_FILE.exists():
        with open(CSV_FILE, 'r') as f:
            reader = csv.reader(f)
            next(reader, None)
            return {row[0] for row in reader}
    return set()

def save_multipliers(multipliers_data):
    """Save multipliers to CSV and JSON"""
    
    # CSV
    file_exists = CSV_FILE.exists()
    with open(CSV_FILE, 'a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['multiplier', 'timestamp', 'value'])
        
        for data in multipliers_data:
            writer.writerow([
                data['multiplier'],
                data['timestamp'],
                data['value']
            ])
    
    # JSON
    try:
        if JSON_FILE.exists():
            with open(JSON_FILE, 'r') as f:
                existing_data = json.load(f)
        else:
            existing_data = []
        
        existing_data.extend(multipliers_data)
        
        with open(JSON_FILE, 'w') as f:
            json.dump(existing_data, f, indent=2)
    except:
        pass

def commit_data_to_github():
    """Automatically commit and push data to GitHub"""
    try:
        # Check if there are changes to commit
        result = subprocess.run(['git', 'status', '--porcelain', 'data/'], 
                               capture_output=True, text=True)
        
        if result.stdout.strip():
            # Add data folder
            subprocess.run(['git', 'add', 'data/'], capture_output=True)
            
            # Commit
            commit_msg = f"Update multiplier data - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            subprocess.run(['git', 'commit', '-m', commit_msg], capture_output=True)
            
            # Push
            subprocess.run(['git', 'push'], capture_output=True)
            
            print(f"✅ Data committed to GitHub at {datetime.now().strftime('%H:%M:%S')}")
            return True
        else:
            print("ℹ️ No new data to commit")
            return False
    except Exception as e:
        print(f"⚠️ Could not commit data: {e}")
        return False

# ============================================================
# SCRAPER FUNCTION
# ============================================================
def scrape_aviator():
    """Open browser, scrape data, close browser"""
    
    print(f"\n{'='*60}")
    print(f"🔄 SCRAPE STARTED: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")
    
    # Load existing multipliers
    existing = load_existing_multipliers()
    print(f"📊 Existing multipliers: {len(existing)}")
    
    # Configure Sauce Labs
    options = ChromeOptions()
    options.browser_version = 'latest'
    options.platform_name = 'Windows 11'
    
    sauce_options = {}
    sauce_options['username'] = username
    sauce_options['accessKey'] = access_key
    sauce_options['build'] = 'GitHub-Actions-Build'
    sauce_options['name'] = '24-7-Scraper'
    options.set_capability('sauce:options', sauce_options)
    
    url = "https://ondemand.eu-central-1.saucelabs.com:443/wd/hub"
    
    driver = None
    multipliers_found = []
    
    try:
        # --- START BROWSER ---
        driver = webdriver.Remote(command_executor=url, options=options)
        print("✅ Browser opened")
        wait = WebDriverWait(driver, 20)
        
        # Login
        driver.get("https://thababet.co.ls/sign-in")
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "login-page")))
        
        email_field = wait.until(EC.presence_of_element_located((By.ID, "v-0-username")))
        email_field.clear()
        email_field.send_keys(PHONE_NUMBER)  # Using config variable
        
        password_field = driver.find_element(By.ID, "v-0-password")
        password_field.clear()
        password_field.send_keys(PASSWORD)  # Using config variable
        
        login_button = wait.until(EC.element_to_be_clickable((By.ID, "v-0-submit-button")))
        login_button.click()
        time.sleep(5)
        print("✅ Login successful")
        
        # Go to Aviator
        driver.get("https://thababet.co.ls/spribe/8203")
        time.sleep(8)
        print("✅ Aviator game loaded")
        
        # Find Aviator iframe
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        for iframe in iframes:
            src = iframe.get_attribute('src') or ""
            if "aviator" in src.lower() or "spribe" in src.lower():
                driver.switch_to.frame(iframe)
                print("✅ Switched to Aviator iframe")
                break
        
        time.sleep(2)
        
        # Extract multipliers
        page_text = driver.find_element(By.TAG_NAME, "body").text
        pattern = r'\b\d+\.\d+x\b'
        multipliers = re.findall(pattern, page_text)
        
        if multipliers:
            unique_multipliers = list(set(multipliers))
            sorted_multipliers = sorted(
                unique_multipliers,
                key=lambda x: float(x.replace('x', '')),
                reverse=True
            )
            
            print(f"✅ Found {len(sorted_multipliers)} multiplier(s)")
            
            # Check for new ones
            new_data = []
            timestamp = datetime.now().isoformat()
            new_count = 0
            
            for mult in sorted_multipliers:
                if mult not in existing:
                    data = {
                        'multiplier': mult,
                        'timestamp': timestamp,
                        'value': float(mult.replace('x', ''))
                    }
                    new_data.append(data)
                    new_count += 1
                    print(f"   🆕 New: {mult}")
            
            if new_data:
                save_multipliers(new_data)
                print(f"✅ Saved {new_count} new multiplier(s)")
                
                # 🔥 COMMIT TO GITHUB (so you can view while running)
                commit_data_to_github()
            else:
                print("ℹ️ No new multipliers found")
            
            # Show summary
            if sorted_multipliers:
                print(f"\n📊 Summary:")
                print(f"   🏆 Highest: {sorted_multipliers[0]}")
                print(f"   🔄 Latest: {sorted_multipliers[-1]}")
                print(f"   📊 Total stored: {len(existing) + new_count}")
        
        # --- CLOSE BROWSER ---
        driver.quit()
        print("✅ Browser closed")
        
        return True
        
    except Exception as e:
        print(f"❌ Scrape failed: {e}")
        if driver:
            try:
                driver.quit()
                print("✅ Browser closed (after error)")
            except:
                pass
        return False

# ============================================================
# MAIN LOOP - RUNS FOREVER
# ============================================================
def main():
    print(f"\n{'='*60}")
    print("🚀 24/7 AVIATOR SCRAPER STARTED")
    print(f"{'='*60}")
    print(f"📱 Phone: {PHONE_NUMBER}")
    print(f"⏰ Scraping every {SCRAPE_INTERVAL} minute(s)")
    print(f"📁 Data stored in: {DATA_DIR}")
    print(f"📤 Auto-commit to GitHub: ENABLED")
    print(f"{'='*60}")
    
    run_count = 0
    success_count = 0
    fail_count = 0
    
    while True:
        try:
            run_count += 1
            print(f"\n📊 RUN #{run_count} (Success: {success_count} | Fail: {fail_count})")
            
            success = scrape_aviator()
            
            if success:
                success_count += 1
            else:
                fail_count += 1
            
            # Wait before next scrape
            print(f"\n⏳ Waiting {SCRAPE_INTERVAL} minutes until next scrape...")
            time.sleep(SCRAPE_INTERVAL * 60)
            
        except KeyboardInterrupt:
            print("\n🛑 Stopped by user")
            print(f"📊 Final stats - Runs: {run_count} | Success: {success_count} | Fail: {fail_count}")
            break
        except Exception as e:
            print(f"❌ Critical error: {e}")
            fail_count += 1
            print(f"⏳ Waiting {SCRAPE_INTERVAL} minutes before retry...")
            time.sleep(SCRAPE_INTERVAL * 60)

if __name__ == "__main__":
    main()
