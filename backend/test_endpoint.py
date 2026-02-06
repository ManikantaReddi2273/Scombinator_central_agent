"""
Quick test script to check backend endpoints
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"[OK] Health check: {response.status_code} - {response.json()}")
        return True
    except Exception as e:
        print(f"[FAIL] Health check failed: {e}")
        return False

def test_cors():
    """Test CORS endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/health/cors", timeout=5)
        print(f"[OK] CORS check: {response.status_code} - {response.json()}")
        cors_headers = {k: v for k, v in response.headers.items() if 'access-control' in k.lower()}
        if cors_headers:
            print(f"   CORS Headers found: {list(cors_headers.keys())}")
        return True
    except Exception as e:
        print(f"[FAIL] CORS check failed: {e}")
        return False

def test_companies_no_auth():
    """Test companies endpoint without auth (should get 401)"""
    try:
        response = requests.get(f"{BASE_URL}/api/companies/", timeout=5)
        print(f"Companies (no auth): {response.status_code}")
        if response.status_code == 401:
            print("[OK] Correctly requires authentication")
        else:
            print(f"[WARN] Unexpected status: {response.text[:200]}")
        return response.status_code == 401
    except Exception as e:
        print(f"[FAIL] Companies endpoint failed: {e}")
        return False

def test_login():
    """Test login endpoint"""
    try:
        data = {
            "email": "reddimanikanta2005@gmail.com",
            "password": "R@ddi2273"
        }
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json=data,
            timeout=10
        )
        print(f"Login: {response.status_code}")
        if response.status_code == 200:
            token = response.json().get("access_token")
            print(f"[OK] Login successful, token: {token[:20]}...")
            return token
        else:
            print(f"[FAIL] Login failed: {response.text[:200]}")
            return None
    except Exception as e:
        print(f"[FAIL] Login failed: {e}")
        return None

def test_companies_with_auth(token):
    """Test companies endpoint with auth"""
    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        response = requests.get(
            f"{BASE_URL}/api/companies/",
            headers=headers,
            timeout=10
        )
        print(f"Companies (with auth): {response.status_code}")
        if response.status_code == 200:
            companies = response.json()
            print(f"[OK] Success! Found {len(companies)} companies")
            return True
        else:
            print(f"[FAIL] Failed: {response.text[:500]}")
            return False
    except Exception as e:
        print(f"[FAIL] Companies endpoint failed: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Backend Endpoint Testing")
    print("=" * 60)
    print()
    
    print("1. Testing health endpoint...")
    health_ok = test_health()
    print()
    
    print("2. Testing CORS endpoint...")
    cors_ok = test_cors()
    print()
    
    print("3. Testing companies endpoint (no auth - should fail)...")
    test_companies_no_auth()
    print()
    
    print("4. Testing login...")
    token = test_login()
    print()
    
    if token:
        print("5. Testing companies endpoint (with auth)...")
        test_companies_with_auth(token)
        print()
    
    print("=" * 60)
    print("Testing complete!")
    print("=" * 60)

