import requests
from bs4 import BeautifulSoup
from fastapi import HTTPException
from config.redisClient import redisClient
from redis.exceptions import RedisError
from typing import List
import time

import json
import re
import models.models as models


def fetch_mawaqit_with_retry(masjid_id: str, max_retries: int = 3):
    """Fetch mawaqit data with retry mechanism"""
    
    for attempt in range(max_retries):
        try:
            return fetch_mawaqit(masjid_id)
        except HTTPException as e:
            if e.status_code == 404:
                # Don't retry for 404 errors
                raise e
            elif attempt == max_retries - 1:
                # Last attempt failed, raise the exception
                raise e
            else:
                # Wait before retrying (exponential backoff)
                wait_time = 2 ** attempt
                print(f"Attempt {attempt + 1} failed for {masjid_id}, retrying in {wait_time}s...")
                time.sleep(wait_time)
        except Exception as e:
            if attempt == max_retries - 1:
                raise HTTPException(status_code=500, detail=f"All retry attempts failed for {masjid_id}: {str(e)}")
            else:
                wait_time = 2 ** attempt
                print(f"Attempt {attempt + 1} failed for {masjid_id}, retrying in {wait_time}s...")
                time.sleep(wait_time)


def fetch_mawaqit(masjid_id:str):
    WEEK_IN_SECONDS = 604800
    retrieved_data = None

    # Check if Redis client is initialized
    if redisClient is not None:
        try:
            retrieved_data = redisClient.get(masjid_id)
        except RedisError:
            print("Error when reading from cache")

        if retrieved_data:
            return json.loads(retrieved_data)

    url = f"https://mawaqit.net/fr/m/{masjid_id}"
    
    # Set headers to mimic a real browser request
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    try:
        # Add timeout to prevent hanging requests
        r = requests.get(url, headers=headers, timeout=30)
        
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'html.parser')
            
            # More flexible script finding - look for any script containing confData
            scripts = soup.find_all('script')
            confdata_script = None
            
            for script in scripts:
                if script.string and 'var confData' in script.string:
                    confdata_script = script
                    break
            
            if confdata_script:
                # Try multiple regex patterns for better matching
                patterns = [
                    r'var confData = ({.*?});',  # Original pattern
                    r'var confData\s*=\s*({.*?});',  # With whitespace
                    r'confData\s*=\s*({.*?});',  # Without var
                ]
                
                conf_data = None
                for pattern in patterns:
                    mawaqit = re.search(pattern, confdata_script.string, re.DOTALL)
                    if mawaqit:
                        try:
                            conf_data_json = mawaqit.group(1)
                            conf_data = json.loads(conf_data_json)
                            break
                        except json.JSONDecodeError:
                            continue
                
                if conf_data:
                    # Store data in Redis if client is initialized
                    if redisClient is not None:
                        try:
                            redisClient.set(masjid_id, json.dumps(conf_data), ex=WEEK_IN_SECONDS)
                        except RedisError:
                            print("Error when writing to cache")
                    return conf_data
                else:
                    raise HTTPException(status_code=500, detail=f"Failed to parse confData JSON for {masjid_id}")
            else:
                print("Script containing confData not found.")
                # Log more details for debugging
                print(f"Total scripts found: {len(scripts)}")
                scripts_with_content = sum(1 for s in scripts if s.string)
                print(f"Scripts with content: {scripts_with_content}")
                raise HTTPException(status_code=500, detail=f"Script containing confData not found for {masjid_id}")
        
        elif r.status_code == 404:
            raise HTTPException(status_code=404, detail=f"{masjid_id} not found")  
        else:
            raise HTTPException(status_code=502, detail=f"HTTP {r.status_code} error fetching {url}")
            
    except requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail=f"Request timeout when fetching data for {masjid_id}")
    except requests.exceptions.ConnectionError:
        raise HTTPException(status_code=502, detail=f"Connection error when fetching data for {masjid_id}")
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Request error when fetching data for {masjid_id}: {str(e)}") 

def get_prayer_times_of_the_day(masjid_id):
    conf_data = fetch_mawaqit_with_retry(masjid_id)
    times = conf_data["times"]
    sunrise = conf_data["shuruq"]
    prayer_time = models.PrayerTimes(fajr=times[0], sunrise=sunrise, dohr=times[1], asr=times[2], maghreb=times[3], icha=times[4])
    prayer_dict = prayer_time.model_dump()
    return prayer_dict

def get_calendar(masjid_id):
    conf_data = fetch_mawaqit_with_retry(masjid_id)
    return conf_data["calendar"]

def get_month(masjid_id, month_number):
    if month_number < 1 or month_number > 12:
        raise HTTPException(status_code=400, detail="Month number should be between 1 and 12")
    conf_data = fetch_mawaqit_with_retry(masjid_id)
    month = conf_data["calendar"][month_number - 1]
    prayer_times_list = [
        models.PrayerTimes( 
            fajr=prayer[0],
            sunrise=prayer[1],
            dohr=prayer[2],
            asr=prayer[3],
            maghreb=prayer[4],
            icha=prayer[5]
        )
        for prayer in month.values()
    ]
    return prayer_times_list

def get_announcements(masjid_id: int) -> List[models.Announcement]:
    conf_data = fetch_mawaqit_with_retry(masjid_id)
    announcements = conf_data.get("announcements", [])
    return [models.Announcement(**a) for a in announcements]

def get_services(masjid_id: int) -> models.MosqueServices:
    conf_data = fetch_mawaqit_with_retry(masjid_id)
    mosque_services = models.MosqueServices(**conf_data)
    return mosque_services