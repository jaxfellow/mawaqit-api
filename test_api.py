#!/usr/bin/env python3

import requests
import json

def test_api_endpoints():
    """Test the main API endpoints"""
    base_url = "https://mawaqit-api-eight.vercel.app/api/v1"
    masjid_id = "assalam-lubeck"
    
    # Test endpoints
    endpoints = [
        ("Health Check", f"{base_url}/health"),
        ("Root", f"{base_url}/"),
        ("Prayer Times", f"{base_url}/{masjid_id}/prayer-times"),
        ("Raw Data", f"{base_url}/{masjid_id}/"),
        ("Announcements", f"{base_url}/{masjid_id}/announcements"),
    ]
    
    for name, url in endpoints:
        print(f"\n=== Testing {name} ===")
        print(f"URL: {url}")
        
        try:
            response = requests.get(url, timeout=30)
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"Response: {json.dumps(data, indent=2)[:500]}...")
                except:
                    print(f"Response (text): {response.text[:500]}...")
            else:
                print(f"Error Response: {response.text}")
                
        except requests.exceptions.Timeout:
            print("❌ Request timed out")
        except requests.exceptions.ConnectionError:
            print("❌ Connection error")
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_api_endpoints()