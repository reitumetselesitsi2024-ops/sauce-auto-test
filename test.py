from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
import os

# Get credentials from GitHub Secrets
username = os.environ.get('SAUCE_USERNAME')
access_key = os.environ.get('SAUCE_ACCESS_KEY')

# Setup Sauce Labs options
options = ChromeOptions()
options.browser_version = 'latest'
options.platform_name = 'Windows 11'

sauce_options = {}
sauce_options['username'] = username
sauce_options['accessKey'] = access_key
sauce_options['build'] = 'GitHub-Actions-Build'
sauce_options['name'] = 'My Test on Windows 11'
options.set_capability('sauce:options', sauce_options)

# Connect to Sauce Labs
url = "https://ondemand.eu-central-1.saucelabs.com:443/wd/hub"
driver = webdriver.Remote(command_executor=url, options=options)

try:
    # Run your test
    driver.get("https://www.saucedemo.com")
    title = driver.title
    print(f"Page title: {title}")
    
    # Check if test passed
    if "Swag Labs" in title:
        print("✅ Test passed!")
        driver.execute_script("sauce:job-result=passed")
    else:
        print("❌ Test failed - wrong title")
        driver.execute_script("sauce:job-result=failed")
        
except Exception as e:
    print(f"❌ Error: {e}")
    driver.execute_script("sauce:job-result=failed")
    
finally:
    driver.quit()
