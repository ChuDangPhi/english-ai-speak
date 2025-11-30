"""
Simple API Test Script for OhMyGPT and Deepgram
"""
import os
from dotenv import load_dotenv
import httpx

# Load environment variables
load_dotenv()

def test_ohmygpt():
    """Test OhMyGPT API connection"""
    print("\n🔍 Testing OhMyGPT API...")
    
    api_key = os.getenv("OHMYGPT_API_KEY")
    base_url = os.getenv("OHMYGPT_BASE_URL", "https://api.ohmygpt.com/v1")
    model = os.getenv("OHMYGPT_MODEL", "gpt-4o-mini")
    
    if not api_key:
        print("❌ OHMYGPT_API_KEY not found in .env")
        return False
    
    print(f"   API Key: {api_key[:10]}...{api_key[-5:]}")
    print(f"   Base URL: {base_url}")
    print(f"   Model: {model}")
    
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                f"{base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "messages": [
                        {"role": "user", "content": "Hello! Say 'API working' in exactly 2 words."}
                    ],
                    "max_tokens": 50,
                    "temperature": 0.5
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                reply = data['choices'][0]['message']['content']
                print(f"   ✅ OhMyGPT Response: {reply}")
                return True
            else:
                print(f"   ❌ Error {response.status_code}: {response.text}")
                return False
                
    except Exception as e:
        print(f"   ❌ Connection Error: {str(e)}")
        return False


def test_deepgram():
    """Test Deepgram API connection"""
    print("\n🔍 Testing Deepgram API...")
    
    api_key = os.getenv("DEEPGRAM_API_KEY")
    
    if not api_key:
        print("❌ DEEPGRAM_API_KEY not found in .env")
        return False
    
    print(f"   API Key: {api_key[:10]}...{api_key[-5:]}")
    
    try:
        # Test API key by checking projects endpoint
        with httpx.Client(timeout=30.0) as client:
            response = client.get(
                "https://api.deepgram.com/v1/projects",
                headers={
                    "Authorization": f"Token {api_key}",
                    "Content-Type": "application/json"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                projects = data.get('projects', [])
                print(f"   ✅ Deepgram Connected! Found {len(projects)} project(s)")
                if projects:
                    print(f"   📁 Project: {projects[0].get('name', 'N/A')}")
                return True
            elif response.status_code == 401:
                print(f"   ❌ Invalid API Key (401 Unauthorized)")
                return False
            else:
                print(f"   ❌ Error {response.status_code}: {response.text}")
                return False
                
    except Exception as e:
        print(f"   ❌ Connection Error: {str(e)}")
        return False


def main():
    print("=" * 60)
    print("🧪 API Connection Test")
    print("=" * 60)
    
    results = {}
    
    # Test OhMyGPT
    results['OhMyGPT'] = test_ohmygpt()
    
    # Test Deepgram
    results['Deepgram'] = test_deepgram()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 RESULTS SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for service, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"   {service:15} {status}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("🎉 All APIs are working correctly!")
    else:
        print("⚠️  Some APIs failed. Please check your API keys in .env")
    
    return all_passed


if __name__ == "__main__":
    main()
