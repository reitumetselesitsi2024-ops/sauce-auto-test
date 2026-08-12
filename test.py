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
import traceback
from datetime import datetime
from pathlib import Path

# ============================================================
# ⚙️ CONFIGURATION - EDIT THESE VALUES
# ============================================================
PHONE_NUMBER = "58532178"  # <-- CHANGE THIS
PASSWORD = "598976Lesitsi"     # <-- CHANGE THIS
SCRAPE_INTERVAL = 2          # Minutes between scrapes
MULTIPLIER_THRESHOLD = 2.0   # Track multipliers >= this value

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

# Main data files
CSV_FILE = DATA_DIR / "multipliers.csv"
JSON_FILE = DATA_DIR / "multipliers.json"
BET_TRACKER_FILE = DATA_DIR / "bet_tracker.txt"  # NEW: TXT file for bet tracking
ERROR_LOG_FILE = DATA_DIR / "error_log.txt"      # NEW: Error logging

def log_error(error_message):
    """Log errors to file for debugging"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(ERROR_LOG_FILE, 'a') as f:
        f.write(f"[{timestamp}] ERROR: {error_message}\n")
        f.write("="*60 + "\n")

def load_existing_multipliers():
    """Load previously saved multipliers to avoid duplicates"""
    if CSV_FILE.exists():
        try:
            with open(CSV_FILE, 'r') as f:
                reader = csv.reader(f)
                next(reader, None)
                return {row[0] for row in reader}
        except:
            return set()
    return set()

def save_multipliers(multipliers_data):
    """Save multipliers to CSV and JSON"""
    try:
        # CSV
        file_exists = CSV_FILE.exists()
        with open(CSV_FILE, 'a', newline='') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(['multiplier', 'timestamp', 'value', 'win_prediction'])
            
            for data in multipliers_data:
                win_pred = "WIN" if data['value'] >= MULTIPLIER_THRESHOLD else "LOSS"
                writer.writerow([
                    data['multiplier'],
                    data['timestamp'],
                    data['value'],
                    win_pred
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
    except Exception as e:
        log_error(f"Save failed: {e}")

def save_bet_tracking(all_multipliers):
    """Save bet tracking analysis to TXT file"""
    try:
        # Filter multipliers >= threshold
        winning_bets = [m for m in all_multipliers if m >= MULTIPLIER_THRESHOLD]
        total_bets = len(all_multipliers)
        win_count = len(winning_bets)
        win_percentage = (win_count / total_bets * 100) if total_bets > 0 else 0
        
        # Get highest and most recent
        highest = max(all_multipliers) if all_multipliers else 0
        most_recent = all_multipliers[-1] if all_multipliers else 0
        
        # Create report
        report = []
        report.append("="*60)
        report.append(f"📊 BET TRACKER REPORT - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("="*60)
        report.append(f"🔢 Total multipliers tracked: {total_bets}")
        report.append(f"🎯 Threshold: >= {MULTIPLIER_THRESHOLD}x")
        report.append(f"✅ Winning bets (>= {MULTIPLIER_THRESHOLD}x): {win_count}")
        report.append(f"❌ Losing bets (< {MULTIPLIER_THRESHOLD}x): {total_bets - win_count}")
        report.append(f"📈 Win percentage: {win_percentage:.2f}%")
        report.append(f"🏆 Highest multiplier: {highest}x")
        report.append(f"🔄 Most recent multiplier: {most_recent}x")
        report.append("="*60)
        report.append("")
        report.append("📋 All tracked multipliers:")
        for i, mult in enumerate(all_multipliers, 1):
            status = "✅ WIN" if mult >= MULTIPLIER_THRESHOLD else "❌ LOSS"
            report.append(f"   {i}. {mult}x - {status}")
        report.append("="*60)
        report.append(f"💡 ANALYSIS: If you bet after seeing a multiplier >= {MULTIPLIER_THRESHOLD}x, you would win {win_percentage:.2f}% of the time!")
        report.append("="*60)
        
        # Save to TXT
        with open(BET_TRACKER_FILE, 'w') as f:
            f.write('\n'.join(report))
        
        print(f"✅ Bet tracking saved to: {BET_TRACKER_FILE}")
        return win_percentage, win_count, total_bets
    except Exception as e:
        log_error(f"Bet tracking failed: {e}")
        return 0, 0, 0

def commit_data_to_github():
    """Automatically commit and push data to GitHub"""
    try:
        result = subprocess.run(['git', 'status', '--porcelain', 'data/'], 
                               capture_output=True, text=True)
        
        if result.stdout.strip():
            subprocess.run(['git', 'add', 'data/'], capture_output=True)
            commit_msg = f"Update data - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            subprocess.run(['git', 'commit', '-m', commit_msg], capture_output=True)
            subprocess.run(['git', 'push'], capture_output=True)
            print(f"✅ Data committed to GitHub")
            return True
        else:
            print("ℹ️ No new data to commit")
            return False
    except Exception as e:
        log_error(f"Commit failed: {e}")
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
    
    try:
        # Load existing multipliers
        existing = load_existing_multipliers()
        print(f"📊 Existing multipliers: {len(existing)}")
        
        # Configure Sauce Labs
        options = ChromeOptions()
        options.browser_version = 'latest'
        options.platform_name = 'Windows 11'
        options.set_capability('sauce:options', {
            'username': username,
            'accessKey': access_key,
            'build': 'GitHub-Actions-Build',
            'name': '24-7-Scraper'
        })
        
        url = "https://ondemand.eu-central-1.saucelabs.com:443/wd/hub"
        
        driver = None
        
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
            email_field.send_keys(PHONE_NUMBER)
            
            password_field = driver.find_element(By.ID, "v-0-password")
            password_field.clear()
            password_field.send_keys(PASSWORD)
            
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
            frame_found = False
            for iframe in iframes:
                src = iframe.get_attribute('src') or ""
                if "aviator" in src.lower() or "spribe" in src.lower():
                    driver.switch_to.frame(iframe)
                    frame_found = True
                    print("✅ Switched to Aviator iframe")
                    break
            
            if not frame_found:
                print("⚠️ Aviator iframe not found!")
                driver.save_screenshot("iframe_not_found.png")
            
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
                all_values = []
                
                for mult in sorted_multipliers:
                    value = float(mult.replace('x', ''))
                    all_values.append(value)
                    if mult not in existing:
                        data = {
                            'multiplier': mult,
                            'timestamp': timestamp,
                            'value': value
                        }
                        new_data.append(data)
                        new_count += 1
                        print(f"   🆕 New: {mult}")
                
                if new_data:
                    save_multipliers(new_data)
                    print(f"✅ Saved {new_count} new multiplier(s)")
                    
                    # 🔥 Track betting performance
                    win_percentage, wins, total = save_bet_tracking(all_values)
                    print(f"📊 Win percentage: {win_percentage:.2f}% ({wins}/{total})")
                    
                    # Commit to GitHub
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
            if driver:
                driver.quit()
                print("✅ Browser closed")
            
            return True
            
        except Exception as e:
            error_msg = traceback.format_exc()
            log_error(f"Scrape error: {e}\n{error_msg}")
            print(f"❌ Scrape failed: {e}")
            
            if driver:
                try:
                    driver.quit()
                    print("✅ Browser closed (after error)")
                except:
                    pass
            
            # Save debug info
            try:
                if driver:
                    driver.save_screenshot("error_screenshot.png")
                    print("📸 Error screenshot saved")
            except:
                pass
            
            return False
            
    except Exception as e:
        log_error(f"Outer error: {e}")
        print(f"❌ Outer error: {e}")
        return False

# ============================================================
# MAIN LOOP - RUNS FOREVER
# ============================================================
def main():
    print(f"\n{'='*60}")
    print("🚀 24/7 AVIATOR SCRAPER WITH BET TRACKING")
    print(f"{'='*60}")
    print(f"📱 Phone: {PHONE_NUMBER}")
    print(f"⏰ Scraping every {SCRAPE_INTERVAL} minute(s)")
    print(f"🎯 Threshold: >= {MULTIPLIER_THRESHOLD}x")
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
                # If we have multiple failures, wait longer
                if fail_count >= 3:
                    print("⚠️ Multiple failures detected. Waiting extra 2 minutes...")
                    time.sleep(120)
            
            # Wait before next scrape
            print(f"\n⏳ Waiting {SCRAPE_INTERVAL} minutes until next scrape...")
            time.sleep(SCRAPE_INTERVAL * 60)
            
        except KeyboardInterrupt:
            print("\n🛑 Stopped by user")
            print(f"📊 Final stats - Runs: {run_count} | Success: {success_count} | Fail: {fail_count}")
            
            # Generate final report on stop
            try:
                if CSV_FILE.exists():
                    print("\n📊 Generating final bet tracking report...")
                    # Read all multipliers from CSV
                    all_vals = []
                    with open(CSV_FILE, 'r') as f:
                        reader = csv.reader(f)
                        next(reader, None)  # Skip header
                        for row in reader:
                            try:
                                all_vals.append(float(row[2]))  # value column
                            except:
                                pass
                    save_bet_tracking(all_vals)
                    print("✅ Final report saved!")
            except:
                pass
            break
            
        except Exception as e:
            log_error(f"Critical error: {e}")
            print(f"❌ Critical error: {e}")
            fail_count += 1
            print(f"⏳ Waiting {SCRAPE_INTERVAL} minutes before retry...")
            time.sleep(SCRAPE_INTERVAL * 60)

if __name__ == "__main__":
    main()
