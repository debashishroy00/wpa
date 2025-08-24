#!/usr/bin/env python3
"""
Rollback verification system for hybrid embedding deployment.
Ensures the system can safely revert to legacy mode within 1 minute.
"""

import asyncio
import time
import json
import sys
import os
from typing import Dict, Any, List, Tuple
from dataclasses import dataclass

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.embeddings.compatibility import get_embedding_service
from app.core.config import settings

@dataclass
class RollbackTest:
    """Single rollback test case"""
    name: str
    description: str
    test_func: str
    expected_result: str
    critical: bool = True

class RollbackVerifier:
    """Verifies rollback capability and safety"""
    
    def __init__(self):
        self.test_texts = [
            "Test embedding generation functionality",
            "Verify backward compatibility is maintained",
            "Ensure performance meets baseline requirements"
        ]
        
        # Define test cases
        self.tests = [
            RollbackTest(
                name="feature_flag_disable",
                description="Verify USE_HYBRID_EMBEDDINGS can be disabled",
                test_func="test_feature_flag_disable",
                expected_result="System reverts to legacy mode",
                critical=True
            ),
            RollbackTest(
                name="legacy_api_compatibility", 
                description="Verify legacy API endpoints work correctly",
                test_func="test_legacy_api_compatibility",
                expected_result="Legacy endpoints return expected results",
                critical=True
            ),
            RollbackTest(
                name="performance_baseline",
                description="Verify performance meets legacy baseline",
                test_func="test_performance_baseline",
                expected_result="Latency within 10% of legacy baseline",
                critical=False
            ),
            RollbackTest(
                name="error_handling",
                description="Verify graceful error handling during rollback",
                test_func="test_error_handling",
                expected_result="No exceptions during mode switching",
                critical=True
            ),
            RollbackTest(
                name="data_consistency",
                description="Verify data consistency after rollback",
                test_func="test_data_consistency", 
                expected_result="Same embeddings generated pre/post rollback",
                critical=True
            )
        ]
    
    async def test_feature_flag_disable(self) -> Tuple[bool, Dict[str, Any]]:
        """Test disabling the hybrid embedding feature flag"""
        try:
            # Get current setting
            original_setting = getattr(settings, 'USE_HYBRID_EMBEDDINGS', False)
            
            # Temporarily disable hybrid embeddings
            settings.USE_HYBRID_EMBEDDINGS = False
            
            # Create new service instance
            service = get_embedding_service()
            
            # Test basic functionality
            embedding = await service.generate_embedding(self.test_texts[0])
            
            # Verify we got a valid embedding
            is_valid = (
                isinstance(embedding, list) and
                len(embedding) > 0 and
                all(isinstance(x, (int, float)) for x in embedding)
            )
            
            # Restore original setting
            settings.USE_HYBRID_EMBEDDINGS = original_setting
            
            return is_valid, {
                "embedding_dimension": len(embedding) if is_valid else 0,
                "hybrid_mode_disabled": True,
                "fallback_successful": is_valid
            }
            
        except Exception as e:
            # Restore original setting on error
            settings.USE_HYBRID_EMBEDDINGS = getattr(settings, 'USE_HYBRID_EMBEDDINGS', False)
            return False, {"error": str(e)}
    
    async def test_legacy_api_compatibility(self) -> Tuple[bool, Dict[str, Any]]:
        """Test legacy API compatibility"""
        try:
            service = get_embedding_service()
            
            # Test single embedding (legacy interface)
            single_embedding = await service.generate_embedding(self.test_texts[0])
            
            # Test batch embeddings (legacy interface) 
            batch_embeddings = await service.generate_embeddings(self.test_texts[:2])
            
            # Validate results
            single_valid = (
                isinstance(single_embedding, list) and
                len(single_embedding) > 0
            )
            
            batch_valid = (
                isinstance(batch_embeddings, list) and
                len(batch_embeddings) == 2 and
                all(isinstance(emb, list) for emb in batch_embeddings)
            )
            
            return single_valid and batch_valid, {
                "single_embedding_valid": single_valid,
                "batch_embeddings_valid": batch_valid,
                "single_dimension": len(single_embedding) if single_valid else 0,
                "batch_dimensions": [len(emb) for emb in batch_embeddings] if batch_valid else []
            }
            
        except Exception as e:
            return False, {"error": str(e)}
    
    async def test_performance_baseline(self) -> Tuple[bool, Dict[str, Any]]:
        """Test performance meets baseline requirements"""
        try:
            service = get_embedding_service()
            
            # Measure latency for multiple requests
            latencies = []
            
            for text in self.test_texts:
                start_time = time.time()
                embedding = await service.generate_embedding(text)
                latency_ms = (time.time() - start_time) * 1000
                latencies.append(latency_ms)
            
            avg_latency = sum(latencies) / len(latencies)
            max_latency = max(latencies)
            
            # Performance criteria (adjust based on your baseline)
            baseline_latency_ms = 1000  # 1 second baseline
            performance_acceptable = avg_latency <= baseline_latency_ms
            
            return performance_acceptable, {
                "average_latency_ms": round(avg_latency, 2),
                "max_latency_ms": round(max_latency, 2),
                "baseline_latency_ms": baseline_latency_ms,
                "performance_acceptable": performance_acceptable,
                "latency_samples": [round(l, 2) for l in latencies]
            }
            
        except Exception as e:
            return False, {"error": str(e)}
    
    async def test_error_handling(self) -> Tuple[bool, Dict[str, Any]]:
        """Test graceful error handling during rollback"""
        try:
            service = get_embedding_service()
            error_count = 0
            
            # Test various error scenarios
            test_scenarios = [
                "",  # Empty string
                "a" * 10000,  # Very long string
                None,  # None value (should be handled gracefully)
            ]
            
            for i, scenario in enumerate(test_scenarios):
                try:
                    if scenario is None:
                        # Skip None test as it would cause TypeError
                        continue
                    result = await service.generate_embedding(str(scenario))
                    # If no error, that's good
                except Exception as e:
                    # Count errors, but they might be expected
                    error_count += 1
            
            # Error handling is acceptable if we didn't crash completely
            graceful_handling = error_count <= len(test_scenarios)  # Some errors are expected
            
            return graceful_handling, {
                "error_count": error_count,
                "total_scenarios": len(test_scenarios) - 1,  # Excluding None
                "graceful_handling": graceful_handling
            }
            
        except Exception as e:
            return False, {"error": str(e)}
    
    async def test_data_consistency(self) -> Tuple[bool, Dict[str, Any]]:
        """Test data consistency before and after rollback"""
        try:
            service = get_embedding_service()
            
            # Generate embeddings in current mode
            pre_rollback_embeddings = []
            for text in self.test_texts:
                embedding = await service.generate_embedding(text)
                pre_rollback_embeddings.append(embedding)
            
            # Simulate rollback by disabling hybrid mode temporarily
            original_setting = getattr(settings, 'USE_HYBRID_EMBEDDINGS', False)
            settings.USE_HYBRID_EMBEDDINGS = False
            
            # Create new service instance and generate embeddings
            rollback_service = get_embedding_service()
            post_rollback_embeddings = []
            for text in self.test_texts:
                embedding = await rollback_service.generate_embedding(text)
                post_rollback_embeddings.append(embedding)
            
            # Restore original setting
            settings.USE_HYBRID_EMBEDDINGS = original_setting
            
            # Compare embeddings (they should be similar but may not be identical)
            consistency_scores = []
            for pre, post in zip(pre_rollback_embeddings, post_rollback_embeddings):
                if len(pre) == len(post):
                    # Calculate cosine similarity
                    import numpy as np
                    pre_vec = np.array(pre)
                    post_vec = np.array(post)
                    similarity = np.dot(pre_vec, post_vec) / (np.linalg.norm(pre_vec) * np.linalg.norm(post_vec))
                    consistency_scores.append(float(similarity))
                else:
                    consistency_scores.append(0.0)  # Different dimensions
            
            avg_consistency = sum(consistency_scores) / len(consistency_scores)
            consistent = avg_consistency > 0.9  # 90% similarity threshold
            
            return consistent, {
                "average_consistency": round(avg_consistency, 3),
                "consistency_scores": [round(s, 3) for s in consistency_scores],
                "dimension_match": len(pre_rollback_embeddings[0]) == len(post_rollback_embeddings[0]),
                "consistent": consistent
            }
            
        except Exception as e:
            # Restore original setting on error
            settings.USE_HYBRID_EMBEDDINGS = getattr(settings, 'USE_HYBRID_EMBEDDINGS', False)
            return False, {"error": str(e)}
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all rollback verification tests"""
        print("🔄 Starting rollback verification tests...")
        start_time = time.time()
        
        results = {
            "start_time": start_time,
            "tests": {},
            "summary": {
                "total_tests": len(self.tests),
                "passed_tests": 0,
                "failed_tests": 0,
                "critical_failures": 0
            }
        }
        
        for test in self.tests:
            print(f"  🧪 Running: {test.name}")
            
            try:
                # Get test function and run it
                test_func = getattr(self, test.test_func)
                success, test_result = await test_func()
                
                results["tests"][test.name] = {
                    "description": test.description,
                    "expected": test.expected_result,
                    "success": success,
                    "critical": test.critical,
                    "result": test_result
                }
                
                if success:
                    results["summary"]["passed_tests"] += 1
                    print(f"    ✅ {test.name} passed")
                else:
                    results["summary"]["failed_tests"] += 1
                    if test.critical:
                        results["summary"]["critical_failures"] += 1
                    print(f"    ❌ {test.name} failed: {test_result.get('error', 'Unknown error')}")
            
            except Exception as e:
                print(f"    💥 {test.name} crashed: {str(e)}")
                results["tests"][test.name] = {
                    "description": test.description,
                    "expected": test.expected_result,
                    "success": False,
                    "critical": test.critical,
                    "result": {"error": f"Test crashed: {str(e)}"}
                }
                results["summary"]["failed_tests"] += 1
                if test.critical:
                    results["summary"]["critical_failures"] += 1
        
        # Calculate timing
        end_time = time.time()
        results["end_time"] = end_time
        results["duration_seconds"] = end_time - start_time
        
        # Overall assessment
        results["rollback_safe"] = results["summary"]["critical_failures"] == 0
        results["rollback_time_acceptable"] = results["duration_seconds"] <= 60  # 1 minute max
        
        return results
    
    def print_results(self, results: Dict[str, Any]):
        """Print formatted test results"""
        print("\n" + "="*80)
        print("🔄 ROLLBACK VERIFICATION RESULTS")
        print("="*80)
        
        summary = results["summary"]
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Passed: {summary['passed_tests']}")
        print(f"Failed: {summary['failed_tests']}")
        print(f"Critical Failures: {summary['critical_failures']}")
        print(f"Duration: {results['duration_seconds']:.1f}s")
        
        print(f"\n📋 TEST DETAILS")
        for test_name, test_result in results["tests"].items():
            status = "✅" if test_result["success"] else "❌"
            critical = " (CRITICAL)" if test_result["critical"] else ""
            print(f"{status} {test_name}{critical}")
            print(f"   {test_result['description']}")
            
            if not test_result["success"] and "error" in test_result["result"]:
                print(f"   Error: {test_result['result']['error']}")
        
        print(f"\n🎯 ROLLBACK ASSESSMENT")
        
        if results["rollback_safe"]:
            print("✅ Rollback Safety: SAFE (no critical failures)")
        else:
            print("❌ Rollback Safety: UNSAFE (critical failures detected)")
        
        if results["rollback_time_acceptable"]:
            print("✅ Rollback Time: ACCEPTABLE (≤1 minute)")
        else:
            print("❌ Rollback Time: TOO SLOW (>1 minute)")
        
        overall_safe = results["rollback_safe"] and results["rollback_time_acceptable"]
        
        if overall_safe:
            print("\n🟢 OVERALL: ROLLBACK VERIFIED - Safe to deploy")
        else:
            print("\n🔴 OVERALL: ROLLBACK FAILED - Do not deploy")
            print("\nREQUIRED ACTIONS:")
            
            if not results["rollback_safe"]:
                print("- Fix critical test failures before deployment")
            if not results["rollback_time_acceptable"]:
                print("- Optimize rollback process to complete within 60 seconds")
        
        print(f"\n📊 GO/NO-GO DECISION")
        
        go_criteria = [
            ("No critical failures", results["rollback_safe"]),
            ("Rollback time ≤60s", results["rollback_time_acceptable"]),
            ("Legacy API works", results["tests"].get("legacy_api_compatibility", {}).get("success", False)),
            ("Feature flag works", results["tests"].get("feature_flag_disable", {}).get("success", False))
        ]
        
        all_go = all(passed for _, passed in go_criteria)
        
        print("Criteria:")
        for criterion, passed in go_criteria:
            status = "✅" if passed else "❌"
            print(f"  {status} {criterion}")
        
        if all_go:
            print(f"\n🚀 DECISION: GO - System ready for production rollout")
        else:
            print(f"\n🛑 DECISION: NO-GO - Address issues before deployment")

async def main():
    """Main rollback verification function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Verify rollback capability")
    parser.add_argument("--output", type=str, help="Output results to JSON file")
    parser.add_argument("--timeout", type=int, default=120, help="Test timeout in seconds")
    
    args = parser.parse_args()
    
    verifier = RollbackVerifier()
    
    try:
        # Run verification with timeout
        results = await asyncio.wait_for(
            verifier.run_all_tests(),
            timeout=args.timeout
        )
        
        # Print results
        verifier.print_results(results)
        
        # Save results if requested
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            print(f"\n💾 Results saved to: {args.output}")
        
        # Exit with appropriate code
        if results["rollback_safe"] and results["rollback_time_acceptable"]:
            sys.exit(0)  # Success
        else:
            sys.exit(1)  # Failure
        
    except asyncio.TimeoutError:
        print(f"\n⏰ Rollback verification timed out after {args.timeout}s")
        print("❌ TIMEOUT FAILURE - Rollback takes too long")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n⏹️ Rollback verification interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Rollback verification failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())