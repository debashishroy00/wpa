#!/usr/bin/env python3
"""
Load testing framework for hybrid embedding system.
Finds break-even points and validates performance under load.
"""

import asyncio
import time
import json
import statistics
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass, asdict
import argparse
import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.embeddings.compatibility import get_embedding_service
from app.services.embeddings.base import EmbeddingContext
from app.core.config import settings

@dataclass
class LoadTestConfig:
    """Load test configuration"""
    concurrent_users: int = 10
    requests_per_user: int = 100
    ramp_up_seconds: int = 30
    test_duration_seconds: int = 300
    batch_sizes: List[int] = None
    contexts: List[str] = None
    
    def __post_init__(self):
        if self.batch_sizes is None:
            self.batch_sizes = [1, 5, 10, 25, 50, 100]
        if self.contexts is None:
            self.contexts = ["realtime", "batch", "analysis"]

@dataclass 
class LoadTestResult:
    """Results from a load test run"""
    config: LoadTestConfig
    start_time: float
    end_time: float
    total_requests: int
    successful_requests: int
    failed_requests: int
    total_embeddings: int
    
    # Performance metrics
    latency_samples: List[float]
    throughput_rps: float
    
    # Cost metrics
    total_cost_usd: float
    avg_cost_per_embedding: float
    
    # Provider usage
    provider_usage: Dict[str, int]
    cache_hit_rate: float
    
    # Quality metrics (if available)
    quality_samples: List[float]
    
    @property
    def duration_seconds(self) -> float:
        return self.end_time - self.start_time
    
    @property
    def p50_latency_ms(self) -> float:
        return statistics.median(self.latency_samples) if self.latency_samples else 0
    
    @property
    def p95_latency_ms(self) -> float:
        if len(self.latency_samples) < 20:
            return self.p50_latency_ms
        return statistics.quantiles(self.latency_samples, n=20)[18]
    
    @property
    def p99_latency_ms(self) -> float:
        if len(self.latency_samples) < 100:
            return self.p95_latency_ms
        return statistics.quantiles(self.latency_samples, n=100)[98]
    
    @property
    def success_rate(self) -> float:
        return self.successful_requests / max(1, self.total_requests)

class EmbeddingLoadTester:
    """Load testing framework for embedding system"""
    
    def __init__(self):
        # Sample texts for testing (financial domain)
        self.test_texts = [
            "Retirement planning requires careful consideration of your risk tolerance and time horizon.",
            "Diversifying your investment portfolio across asset classes can help manage risk.",
            "Roth IRA conversions may provide tax advantages in retirement.",
            "Dollar-cost averaging helps reduce the impact of market volatility.",
            "Emergency funds should cover 3-6 months of living expenses.",
            "Tax-loss harvesting can optimize your after-tax returns.",
            "Estate planning ensures your wealth transfers according to your wishes.",
            "Asset allocation should align with your financial goals and timeline.",
            "Social Security benefits are an important component of retirement income.",
            "529 plans offer tax-advantaged savings for education expenses.",
            "Rebalancing maintains your target asset allocation over time.",
            "Long-term care insurance protects against healthcare costs in retirement.",
            "HSAs provide triple tax advantages for qualified medical expenses.",
            "Backdoor Roth conversions allow high earners to access Roth IRA benefits.",
            "Monte Carlo simulations model various market scenarios for planning.",
            "Factor investing targets specific risk and return characteristics.",
            "TIPS bonds provide protection against inflation risk.",
            "Required minimum distributions begin at age 73 for traditional IRAs.",
            "Charitable giving strategies can provide tax benefits while supporting causes.",
            "Life insurance needs change as your financial situation evolves."
        ]
        
        self.service = None
    
    async def initialize(self):
        """Initialize the embedding service"""
        self.service = get_embedding_service()
        print("🚀 Embedding service initialized")
    
    async def run_single_request_test(
        self,
        text: str,
        context: EmbeddingContext = EmbeddingContext.REALTIME
    ) -> Tuple[bool, Dict[str, Any]]:
        """Run a single embedding request and return results"""
        try:
            start_time = time.time()
            
            # Use enhanced API for detailed metrics
            result = await self.service.generate_embedding_with_metadata(
                text=text,
                context=context.value if hasattr(context, 'value') else str(context)
            )
            
            latency_ms = (time.time() - start_time) * 1000
            
            return True, {
                "latency_ms": latency_ms,
                "provider": result.get("provider", "unknown"),
                "cached": result.get("cached", False),
                "cost_usd": result.get("cost_usd", 0.0),
                "dimension": result.get("dimension", 0),
                "tokens_used": result.get("tokens_used", 0)
            }
            
        except Exception as e:
            return False, {"error": str(e)}
    
    async def run_batch_test(
        self,
        texts: List[str],
        context: EmbeddingContext = EmbeddingContext.BATCH
    ) -> Tuple[bool, Dict[str, Any]]:
        """Run batch embedding request"""
        try:
            start_time = time.time()
            
            results = await self.service.batch_generate_embeddings_with_metadata(
                texts=texts,
                context=context.value if hasattr(context, 'value') else str(context)
            )
            
            latency_ms = (time.time() - start_time) * 1000
            
            # Aggregate results
            total_cost = sum(r.get("cost_usd", 0.0) for r in results)
            providers = [r.get("provider", "unknown") for r in results]
            cached_count = sum(1 for r in results if r.get("cached", False))
            
            return True, {
                "latency_ms": latency_ms,
                "batch_size": len(texts),
                "total_cost_usd": total_cost,
                "avg_latency_per_text": latency_ms / len(texts),
                "providers": providers,
                "cache_hit_rate": cached_count / len(results),
                "embeddings_per_second": len(texts) / (latency_ms / 1000)
            }
            
        except Exception as e:
            return False, {"error": str(e)}
    
    async def run_concurrent_load_test(self, config: LoadTestConfig) -> LoadTestResult:
        """Run concurrent load test with multiple users"""
        print(f"🧪 Starting load test: {config.concurrent_users} users, {config.requests_per_user} requests each")
        
        start_time = time.time()
        
        # Results tracking
        results = LoadTestResult(
            config=config,
            start_time=start_time,
            end_time=0,
            total_requests=0,
            successful_requests=0,
            failed_requests=0,
            total_embeddings=0,
            latency_samples=[],
            throughput_rps=0,
            total_cost_usd=0,
            avg_cost_per_embedding=0,
            provider_usage={},
            cache_hit_rate=0,
            quality_samples=[]
        )
        
        async def user_simulation(user_id: int):
            """Simulate a single user's requests"""
            user_results = []
            
            # Ramp up delay
            ramp_delay = (user_id / config.concurrent_users) * config.ramp_up_seconds
            await asyncio.sleep(ramp_delay)
            
            for request_id in range(config.requests_per_user):
                # Select random text and context
                import random
                text = random.choice(self.test_texts)
                context = random.choice(config.contexts)
                
                # Convert string to enum
                context_enum = {
                    "realtime": EmbeddingContext.REALTIME,
                    "batch": EmbeddingContext.BATCH,
                    "analysis": EmbeddingContext.ANALYSIS,
                    "search": EmbeddingContext.SEARCH
                }.get(context, EmbeddingContext.REALTIME)
                
                success, result = await self.run_single_request_test(text, context_enum)
                user_results.append((success, result))
                
                # Small delay to avoid overwhelming
                await asyncio.sleep(0.1)
            
            return user_results
        
        # Run concurrent users
        tasks = [user_simulation(i) for i in range(config.concurrent_users)]
        all_user_results = await asyncio.gather(*tasks)
        
        # Aggregate results
        for user_results in all_user_results:
            for success, result in user_results:
                results.total_requests += 1
                
                if success:
                    results.successful_requests += 1
                    results.total_embeddings += 1
                    
                    # Collect metrics
                    if "latency_ms" in result:
                        results.latency_samples.append(result["latency_ms"])
                    
                    if "cost_usd" in result:
                        results.total_cost_usd += result["cost_usd"]
                    
                    if "provider" in result:
                        provider = result["provider"]
                        results.provider_usage[provider] = results.provider_usage.get(provider, 0) + 1
                else:
                    results.failed_requests += 1
        
        # Calculate final metrics
        results.end_time = time.time()
        results.throughput_rps = results.successful_requests / results.duration_seconds
        results.avg_cost_per_embedding = (
            results.total_cost_usd / max(1, results.total_embeddings)
        )
        
        # Calculate cache hit rate from provider usage (local provider = cache hit)
        local_requests = results.provider_usage.get("local", 0)
        results.cache_hit_rate = local_requests / max(1, results.successful_requests)
        
        return results
    
    async def run_batch_size_analysis(self) -> Dict[int, Dict[str, float]]:
        """Analyze performance across different batch sizes"""
        print("📊 Running batch size analysis...")
        
        batch_sizes = [1, 5, 10, 25, 50, 100, 200]
        batch_results = {}
        
        for batch_size in batch_sizes:
            print(f"  Testing batch size: {batch_size}")
            
            # Create batch
            batch_texts = (self.test_texts * ((batch_size // len(self.test_texts)) + 1))[:batch_size]
            
            # Run multiple trials
            trials = 3
            trial_results = []
            
            for trial in range(trials):
                success, result = await self.run_batch_test(batch_texts, EmbeddingContext.BATCH)
                
                if success:
                    trial_results.append(result)
                
                await asyncio.sleep(1)  # Cool down between trials
            
            if trial_results:
                # Average across trials
                avg_latency = statistics.mean(r["latency_ms"] for r in trial_results)
                avg_cost = statistics.mean(r["total_cost_usd"] for r in trial_results)
                avg_throughput = statistics.mean(r["embeddings_per_second"] for r in trial_results)
                avg_cache_rate = statistics.mean(r["cache_hit_rate"] for r in trial_results)
                
                batch_results[batch_size] = {
                    "latency_ms": avg_latency,
                    "cost_usd": avg_cost,
                    "embeddings_per_second": avg_throughput,
                    "cache_hit_rate": avg_cache_rate,
                    "cost_per_embedding": avg_cost / batch_size
                }
            
        return batch_results
    
    def print_results(self, results: LoadTestResult):
        """Print formatted test results"""
        print("\n" + "="*80)
        print("🏁 LOAD TEST RESULTS")
        print("="*80)
        
        print(f"Duration: {results.duration_seconds:.1f}s")
        print(f"Total Requests: {results.total_requests}")
        print(f"Success Rate: {results.success_rate:.1%}")
        print(f"Failed Requests: {results.failed_requests}")
        
        print(f"\n📊 PERFORMANCE METRICS")
        print(f"Throughput: {results.throughput_rps:.1f} RPS")
        print(f"P50 Latency: {results.p50_latency_ms:.0f}ms")
        print(f"P95 Latency: {results.p95_latency_ms:.0f}ms")
        print(f"P99 Latency: {results.p99_latency_ms:.0f}ms")
        
        print(f"\n💰 COST METRICS")
        print(f"Total Cost: ${results.total_cost_usd:.4f}")
        print(f"Avg Cost/Embedding: ${results.avg_cost_per_embedding:.6f}")
        
        print(f"\n🔄 PROVIDER USAGE")
        for provider, count in results.provider_usage.items():
            percentage = (count / results.successful_requests) * 100
            print(f"{provider}: {count} ({percentage:.1f}%)")
        
        print(f"\n📈 CACHE EFFICIENCY")
        print(f"Cache Hit Rate: {results.cache_hit_rate:.1%}")
        
        # Performance assessment
        print(f"\n🎯 ASSESSMENT")
        if results.p95_latency_ms <= 500:
            print("✅ Latency: Excellent (P95 ≤ 500ms)")
        elif results.p95_latency_ms <= 1000:
            print("⚠️  Latency: Good (P95 ≤ 1000ms)")
        else:
            print("❌ Latency: Poor (P95 > 1000ms)")
        
        if results.success_rate >= 0.99:
            print("✅ Reliability: Excellent (≥99% success)")
        elif results.success_rate >= 0.95:
            print("⚠️  Reliability: Good (≥95% success)")
        else:
            print("❌ Reliability: Poor (<95% success)")
        
        if results.throughput_rps >= 50:
            print("✅ Throughput: Excellent (≥50 RPS)")
        elif results.throughput_rps >= 20:
            print("⚠️  Throughput: Good (≥20 RPS)")
        else:
            print("❌ Throughput: Poor (<20 RPS)")
    
    def print_batch_analysis(self, batch_results: Dict[int, Dict[str, float]]):
        """Print batch size analysis results"""
        print("\n" + "="*80)
        print("📊 BATCH SIZE ANALYSIS")
        print("="*80)
        
        print(f"{'Batch Size':<12} {'Latency (ms)':<15} {'Cost ($)':<12} {'EPS':<10} {'$/Embedding':<15}")
        print("-" * 80)
        
        for batch_size in sorted(batch_results.keys()):
            result = batch_results[batch_size]
            print(f"{batch_size:<12} "
                  f"{result['latency_ms']:<15.0f} "
                  f"{result['cost_usd']:<12.4f} "
                  f"{result['embeddings_per_second']:<10.1f} "
                  f"{result['cost_per_embedding']:<15.6f}")
        
        # Find optimal batch size
        min_cost_batch = min(batch_results.items(), key=lambda x: x[1]['cost_per_embedding'])
        max_throughput_batch = max(batch_results.items(), key=lambda x: x[1]['embeddings_per_second'])
        
        print(f"\n🎯 RECOMMENDATIONS")
        print(f"Lowest cost per embedding: Batch size {min_cost_batch[0]} "
              f"(${min_cost_batch[1]['cost_per_embedding']:.6f})")
        print(f"Highest throughput: Batch size {max_throughput_batch[0]} "
              f"({max_throughput_batch[1]['embeddings_per_second']:.1f} EPS)")

async def main():
    """Main load testing function"""
    parser = argparse.ArgumentParser(description="Load test the hybrid embedding system")
    parser.add_argument("--users", type=int, default=10, help="Concurrent users")
    parser.add_argument("--requests", type=int, default=50, help="Requests per user")
    parser.add_argument("--duration", type=int, default=300, help="Test duration in seconds")
    parser.add_argument("--batch-analysis", action="store_true", help="Run batch size analysis")
    parser.add_argument("--output", type=str, help="Output results to JSON file")
    
    args = parser.parse_args()
    
    # Initialize tester
    tester = EmbeddingLoadTester()
    await tester.initialize()
    
    # Configure test
    config = LoadTestConfig(
        concurrent_users=args.users,
        requests_per_user=args.requests,
        test_duration_seconds=args.duration
    )
    
    try:
        # Run load test
        print("🏁 Starting load test...")
        results = await tester.run_concurrent_load_test(config)
        tester.print_results(results)
        
        # Run batch analysis if requested
        batch_results = None
        if args.batch_analysis:
            batch_results = await tester.run_batch_size_analysis()
            tester.print_batch_analysis(batch_results)
        
        # Save results if output file specified
        if args.output:
            output_data = {
                "load_test_results": asdict(results),
                "batch_analysis": batch_results
            }
            
            with open(args.output, 'w') as f:
                json.dump(output_data, f, indent=2, default=str)
            
            print(f"\n💾 Results saved to: {args.output}")
        
        print("\n🎉 Load testing completed!")
        
    except KeyboardInterrupt:
        print("\n⏹️  Load test interrupted by user")
    except Exception as e:
        print(f"\n❌ Load test failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())