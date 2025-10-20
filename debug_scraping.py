#!/usr/bin/env python3

import requests
from bs4 import BeautifulSoup
import re
import json

def test_mawaqit_scraping(masjid_id):
    url = f"https://mawaqit.net/fr/m/{masjid_id}"
    print(f"Testing URL: {url}")
    
    r = requests.get(url)
    print(f"Status Code: {r.status_code}")
    
    if r.status_code != 200:
        print(f"Failed to fetch page. Status: {r.status_code}")
        return
    
    soup = BeautifulSoup(r.text, 'html.parser')
    
    # Check all scripts for confData
    scripts = soup.find_all('script')
    print(f"Total scripts found: {len(scripts)}")
    
    confdata_script = None
    for i, script in enumerate(scripts):
        if script.string and 'confData' in script.string:
            print(f"Script {i} contains confData")
            confdata_script = script
            break
    
    if not confdata_script:
        print("No script containing confData found!")
        return
    
    # Try to extract confData using regex
    print("Attempting to extract confData...")
    
    # Original regex pattern
    mawaqit = re.search(r'var confData = (.*?);', confdata_script.string, re.DOTALL)
    
    if mawaqit:
        print("Regex match successful!")
        conf_data_json = mawaqit.group(1)
        
        try:
            conf_data = json.loads(conf_data_json)
            print("JSON parsing successful!")
            print(f"Prayer times: {conf_data.get('times', 'Not found')}")
            print(f"Sunrise: {conf_data.get('shuruq', 'Not found')}")
            return conf_data
        except json.JSONDecodeError as e:
            print(f"JSON parsing failed: {e}")
            print(f"JSON string preview (first 200 chars): {conf_data_json[:200]}...")
            print(f"JSON string preview (last 200 chars): ...{conf_data_json[-200:]}")
    else:
        print("Regex match failed!")
        # Show part of the script content for debugging
        script_content = confdata_script.string[:1000] if confdata_script.string else "No content"
        print(f"Script content preview: {script_content}...")

if __name__ == "__main__":
    test_mawaqit_scraping("assalam-lubeck")