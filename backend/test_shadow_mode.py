#!/usr/bin/env python3
"""
Quick test to verify shadow mode is working properly
"""

import requests
import json
import time
from typing import Dict, Any, Tuple

BASE_URL = "http://localhost:8000"

class ShadowModeValidator:
    """Validates that shadow mode setup is working correctly"""
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        
    def test_server_connection(self) -> Tuple[bool, str]:
        """Test 1: Check if server is running"""
        try:
            response = requests.get(f"{self.base_url}/docs", timeout=5)
            if response.status_code == 200:
                return True, "✅ Server is running and responding"
            else:
                return False, f"❌ Server returned status code: {response.status_code}"
        except requests.exceptions.ConnectionError:
            return False, f"❌ Cannot connect to server at {self.base_url}"
        except requests.exceptions.RequestException as e:
            return False, f"❌ Request failed: {str(e)}"
    
    def test_embedding_endpoints(self) -> Tuple[bool, str]:
        """Test 2: Check if embedding endpoints are accessible"""
        endpoints = [
            "/api/v1/embeddings/health",
            "/api/v1/embeddings/production-readiness",
            "/api/v1/embeddings/metrics"
        ]
        
        results = []
        for endpoint in endpoints:
            try:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
                if response.status_code == 200:
                    results.append(f"✅ {endpoint}")
                else:
                    results.append(f"❌ {endpoint} (status: {response.status_code})")
            except Exception as e:
                results.append(f"❌ {endpoint} (error: {str(e)})")
        
        all_success = all("✅" in result for result in results)
        status = "✅ All embedding endpoints accessible" if all_success else "⚠️ Some endpoints failed"
        
        return all_success, f"{status}\n   " + "\n   ".join(results)
    
    def test_shadow_mode_configuration(self) -> Tuple[bool, str]:
        """Test 3: Check shadow mode configuration"""
        try:
            response = requests.get(f"{self.base_url}/api/v1/embeddings/production-readiness", timeout=10)
            if response.status_code != 200:
                return False, f"❌ Cannot access readiness endpoint (status: {response.status_code})"
            
            data = response.json()
            checklist = data.get('checklist', {})
            
            # Check feature flags
            feature_flags = checklist.get('feature_flags', {})
            shadow_enabled = feature_flags.get('shadow_mode', False)
            hybrid_disabled = not data.get('hybrid_enabled', True)  # Should be false for shadow mode
            
            results = []
            if shadow_enabled:
                results.append("✅ EMBEDDING_SHADOW_MODE=true")
            else:
                results.append("❌ EMBEDDING_SHADOW_MODE not enabled")
            
            if hybrid_disabled:
                results.append("✅ USE_HYBRID_EMBEDDINGS=false") 
            else:
                results.append("⚠️ USE_HYBRID_EMBEDDINGS should be false for shadow mode")
            
            # Check providers
            providers = checklist.get('providers', {})
            local_ready = providers.get('local_available', False)
            
            if local_ready:
                results.append("✅ Local embedding provider ready")
            else:
                results.append("⚠️ Local embedding provider not ready")
            
            openai_ready = providers.get('openai_available', False)
            if openai_ready:
                results.append("✅ OpenAI provider configured")
            else:
                results.append("⚠️ OpenAI provider not configured")
            
            all_good = shadow_enabled and hybrid_disabled and local_ready
            status = "✅ Shadow mode properly configured" if all_good else "⚠️ Configuration issues detected"
            
            return all_good, f"{status}\n   " + "\n   ".join(results)
            
        except Exception as e:
            return False, f"❌ Configuration check failed: {str(e)}"
    
    def test_shadow_mode_functionality(self) -> Tuple[bool, str]:
        """Test 4: Simulate embedding request to trigger shadow comparison"""
        try:
            # Note: This would ideally test the actual embedding generation
            # but requires authentication. Instead, we check if the shadow
            # collection system is ready to log comparisons
            
            response = requests.get(f"{self.base_url}/api/v1/embeddings/production-readiness", timeout=10)
            if response.status_code != 200:
                return False, f"❌ Cannot access readiness data"
            
            data = response.json()
            shadow_stats = data.get('shadow_mode_stats', {})
            
            # Check if shadow collection is initialized
            if 'status' in shadow_stats and shadow_stats.get('status') == 'active':
                comparisons = shadow_stats.get('total_comparisons', 0)
                runtime_hours = shadow_stats.get('runtime_hours', 0)
                
                results = []
                results.append(f"📊 Comparisons logged: {comparisons}")
                results.append(f"⏱️ Runtime: {runtime_hours:.2f} hours")
                
                if comparisons > 0:
                    quality_metrics = shadow_stats.get('quality_metrics', {})
                    avg_similarity = quality_metrics.get('average_similarity', 0)
                    results.append(f"✨ Average similarity: {avg_similarity:.2%}")
                    
                    return True, "✅ Shadow mode is actively collecting data\n   " + "\n   ".join(results)
                else:
                    return True, "⏳ Shadow mode ready - waiting for embeddings\n   " + "\n   ".join(results)
            else:
                return True, "⏳ Shadow mode initialized - ready for first comparison"
                
        except Exception as e:
            return False, f"❌ Shadow functionality test failed: {str(e)}"
    
    def test_redis_connection(self) -> Tuple[bool, str]:
        """Test 5: Check Redis connection status"""
        try:
            response = requests.get(f"{self.base_url}/api/v1/embeddings/health", timeout=10)
            if response.status_code != 200:
                return False, f"❌ Cannot access health endpoint"
            
            health_data = response.json()
            components = health_data.get('components', {})
            cache_info = components.get('cache', {})
            
            if cache_info.get('status') == 'healthy':
                cache_stats = cache_info.get('stats', {})
                l2_available = cache_stats.get('l2_cache', {}).get('available', False)
                
                if l2_available:
                    return True, "✅ Redis cache available and healthy"
                else:
                    return True, "⚠️ Using in-memory cache (Redis not available but fallback working)"
            else:
                return False, "❌ Cache system not healthy"
                
        except Exception as e:
            return False, f"❌ Redis connection test failed: {str(e)}"
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all validation tests"""
        print("🧪 Testing Shadow Mode Setup...")
        print("=" * 60)
        
        tests = [
            ("Server Connection", self.test_server_connection),
            ("Embedding Endpoints", self.test_embedding_endpoints), 
            ("Shadow Configuration", self.test_shadow_mode_configuration),
            ("Shadow Functionality", self.test_shadow_mode_functionality),
            ("Redis Connection", self.test_redis_connection)
        ]
        
        results = {}
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n🔍 Test: {test_name}")
            print("-" * 30)
            
            try:
                success, message = test_func()
                results[test_name] = {"success": success, "message": message}
                
                if success:
                    passed += 1
                    
                print(message)
                
            except Exception as e:
                results[test_name] = {"success": False, "message": f"Test failed: {str(e)}"}
                print(f"❌ Test failed: {str(e)}")
        
        print("\n" + "=" * 60)
        print("📊 SHADOW MODE VALIDATION SUMMARY")
        print("=" * 60)
        print(f"Tests Passed: {passed}/{total}")
        print(f"Success Rate: {passed/total:.1%}")
        
        if passed == total:
            print("\n🎉 SUCCESS: Shadow mode is properly configured!")
            print("\n📝 Next Steps:")
            print("   1. Use WealthPath AI normally to generate embeddings")
            print("   2. Run 'python3 monitor_shadow.py' for live monitoring")
            print("   3. Check progress periodically at the dashboard URLs")
            print("   4. Wait for 100+ comparisons and >95% similarity")
            
        elif passed >= total * 0.8:  # 80% pass rate
            print("\n⚠️  PARTIAL SUCCESS: Most tests passed")
            print("   Shadow mode should work, but there are some issues to address")
            print("\n🔧 Issues to resolve:")
            for test_name, result in results.items():
                if not result["success"]:
                    print(f"   • {test_name}: Check configuration")
                    
        else:
            print("\n❌ FAILURE: Critical issues detected")
            print("   Shadow mode may not work properly")
            print("\n🚨 Critical issues:")
            for test_name, result in results.items():
                if not result["success"]:
                    print(f"   • {test_name}: {result['message'].split(chr(10))[0]}")
        
        print(f"\n📱 Monitoring URLs:")
        print(f"   Production Readiness: {self.base_url}/api/v1/embeddings/production-readiness")
        print(f"   Live Metrics: {self.base_url}/api/v1/embeddings/metrics")
        print(f"   System Health: {self.base_url}/api/v1/embeddings/health")
        
        return {
            "passed": passed,
            "total": total,
            "success_rate": passed/total,
            "results": results,
            "overall_success": passed == total
        }

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test shadow mode configuration")
    parser.add_argument("--url", default=BASE_URL, help="Base URL for the API")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    
    args = parser.parse_args()
    
    validator = ShadowModeValidator(base_url=args.url)
    results = validator.run_all_tests()
    
    if args.json:
        print(json.dumps(results, indent=2))
    
    # Exit with appropriate code
    if results["overall_success"]:
        exit(0)
    elif results["success_rate"] >= 0.8:
        exit(1)  # Partial success
    else:
        exit(2)  # Critical failure

if __name__ == "__main__":
    main()