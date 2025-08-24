#!/usr/bin/env python3
"""
Real-time shadow mode monitoring - shows live metrics as they come in
"""

import time
import requests
import json
import sys
from datetime import datetime
from typing import Dict, Any, Optional

# Check if rich is available, otherwise use simple console output
try:
    from rich.console import Console
    from rich.table import Table
    from rich.live import Live
    from rich.panel import Panel
    from rich.layout import Layout
    from rich.text import Text
    from rich.columns import Columns
    from rich.bar import Bar
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("📦 Rich library not found. Install with: pip install rich")
    print("🔧 Using simple console output instead...")

class ShadowModeMonitor:
    """Monitor shadow mode progress with real-time updates"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.console = Console() if RICH_AVAILABLE else None
        self.start_time = time.time()
        self.last_comparison_count = 0
        
    def get_metrics(self) -> Optional[Dict[str, Any]]:
        """Fetch current metrics from the API"""
        try:
            response = requests.get(f"{self.base_url}/api/v1/embeddings/production-readiness", timeout=5)
            if response.status_code == 200:
                return response.json()
        except requests.exceptions.RequestException:
            pass
        return None
    
    def get_health(self) -> Optional[Dict[str, Any]]:
        """Fetch health status"""
        try:
            response = requests.get(f"{self.base_url}/api/v1/embeddings/health", timeout=5)
            if response.status_code == 200:
                return response.json()
        except requests.exceptions.RequestException:
            pass
        return None
    
    def get_alerts(self) -> Optional[Dict[str, Any]]:
        """Fetch current alerts"""
        try:
            response = requests.get(f"{self.base_url}/api/v1/embeddings/alerts", timeout=5)
            if response.status_code == 200:
                return response.json()
        except requests.exceptions.RequestException:
            pass
        return None
    
    def create_rich_dashboard(self) -> Panel:
        """Create a rich dashboard display"""
        if not RICH_AVAILABLE:
            return None
            
        metrics = self.get_metrics()
        health = self.get_health()
        alerts = self.get_alerts()
        
        if not metrics:
            return Panel(
                "⚠️  Cannot connect to server. Make sure it's running!\n\n"
                f"Expected URL: {self.base_url}\n"
                "Run: bash start_shadow_mode.sh",
                title="🚨 Connection Error",
                style="red"
            )
        
        # Main stats table
        table = Table(title=f"Shadow Mode Monitoring - {datetime.now().strftime('%H:%M:%S')}")
        table.add_column("Metric", style="cyan", width=25)
        table.add_column("Value", style="white", width=20)
        table.add_column("Status", width=8)
        table.add_column("Target", style="dim", width=15)
        
        # Overall readiness
        readiness = metrics.get('readiness_score', 0)
        status_emoji = "🟢" if readiness > 0.9 else "🟡" if readiness > 0.7 else "🔴"
        table.add_row("Overall Readiness", f"{readiness:.1%}", status_emoji, ">90%")
        
        # Shadow mode status
        shadow_stats = metrics.get('shadow_mode_stats', {})
        shadow_enabled = metrics.get('checklist', {}).get('shadow_mode', {}).get('enabled', False)
        
        table.add_row(
            "Shadow Mode",
            "ENABLED" if shadow_enabled else "DISABLED",
            "🟢" if shadow_enabled else "🔴",
            "Enabled"
        )
        
        # Comparison statistics
        comparisons = shadow_stats.get('total_comparisons', 0)
        comparison_emoji = "✅" if comparisons >= 100 else "🔄"
        table.add_row("Comparisons Made", str(comparisons), comparison_emoji, "100+")
        
        # Runtime
        runtime_hours = shadow_stats.get('runtime_hours', 0)
        runtime_emoji = "✅" if runtime_hours >= 48 else "⏳"
        table.add_row("Runtime", f"{runtime_hours:.1f}h", runtime_emoji, "48h+")
        
        # Quality metrics
        if comparisons > 0:
            quality_metrics = shadow_stats.get('quality_metrics', {})
            similarity = quality_metrics.get('average_similarity', 0)
            sim_emoji = "✅" if similarity > 0.95 else "⚠️" if similarity > 0.90 else "❌"
            table.add_row("Avg Similarity", f"{similarity:.2%}", sim_emoji, ">95%")
            
            # Performance metrics
            perf_metrics = shadow_stats.get('performance_metrics', {})
            cache_hit_rate = perf_metrics.get('cache_hit_rate', 0)
            cache_emoji = "✅" if cache_hit_rate > 0.8 else "⚠️" if cache_hit_rate > 0.7 else "❌"
            table.add_row("Cache Hit Rate", f"{cache_hit_rate:.1%}", cache_emoji, ">80%")
            
            # Cost metrics
            cost_metrics = shadow_stats.get('cost_metrics', {})
            total_cost = cost_metrics.get('total_cost_savings', 0)
            table.add_row("Cost Savings", f"${total_cost:.4f}", "💰", "Tracking")
        
        # Progress calculation
        progress_items = []
        if comparisons >= 100:
            progress_items.append("✅ Comparisons")
        else:
            progress_items.append(f"🔄 Comparisons ({comparisons}/100)")
            
        if runtime_hours >= 48:
            progress_items.append("✅ Runtime")
        else:
            progress_items.append(f"⏳ Runtime ({runtime_hours:.1f}/48h)")
            
        if comparisons > 0:
            similarity = shadow_stats.get('quality_metrics', {}).get('average_similarity', 0)
            if similarity > 0.95:
                progress_items.append("✅ Quality")
            else:
                progress_items.append(f"⚠️ Quality ({similarity:.1%})")
        else:
            progress_items.append("⏳ Quality (pending)")
        
        # System health
        if health:
            health_status = health.get('status', 'unknown')
            health_emoji = "✅" if health_status == 'healthy' else "⚠️" if health_status == 'degraded' else "❌"
            table.add_row("System Health", health_status.title(), health_emoji, "Healthy")
        
        # Alerts
        if alerts and alerts.get('status') != 'no_alerts':
            current_alerts = alerts.get('current_alerts', [])
            alert_count = len(current_alerts)
            alert_emoji = "🚨" if alert_count > 0 else "✅"
            table.add_row("Active Alerts", str(alert_count), alert_emoji, "0")
        
        # Provider usage (if available)
        if shadow_stats.get('provider_usage'):
            provider_usage = shadow_stats['provider_usage']
            providers_text = ", ".join([f"{k}: {v}" for k, v in provider_usage.items()])
            table.add_row("Provider Usage", providers_text, "📊", "Balanced")
        
        # Rate of progress
        current_time = time.time()
        elapsed_hours = (current_time - self.start_time) / 3600
        if elapsed_hours > 0 and comparisons > self.last_comparison_count:
            rate = (comparisons - self.last_comparison_count) / elapsed_hours if elapsed_hours > 0 else 0
            table.add_row("Progress Rate", f"{rate:.1f}/hour", "📈", "Steady")
        
        self.last_comparison_count = comparisons
        
        # Create panels for different sections
        main_panel = Panel(table, title="🚀 WealthPath AI - Shadow Mode Status", border_style="green")
        
        # Recommendations panel
        recommendations = metrics.get('recommendations', [])
        if recommendations:
            rec_text = "\n".join([f"• {rec}" for rec in recommendations[:3]])
            rec_panel = Panel(rec_text, title="💡 Next Steps", border_style="blue")
        else:
            rec_panel = Panel("✅ System ready for production deployment!", title="💡 Status", border_style="green")
        
        # Alerts panel (if any)
        alert_panels = []
        if alerts and alerts.get('current_alerts'):
            alert_text = []
            for alert in alerts['current_alerts'][:3]:  # Show max 3 alerts
                level = alert.get('level', 'info').upper()
                message = alert.get('message', 'Unknown alert')
                alert_text.append(f"🚨 [{level}] {message}")
            
            if alert_text:
                alert_panel = Panel("\n".join(alert_text), title="🚨 Active Alerts", border_style="red")
                alert_panels.append(alert_panel)
        
        # Combine panels
        if alert_panels:
            return Columns([main_panel, Columns([rec_panel] + alert_panels)])
        else:
            return Columns([main_panel, rec_panel])
    
    def create_simple_dashboard(self) -> str:
        """Create simple text dashboard for when Rich is not available"""
        metrics = self.get_metrics()
        health = self.get_health()
        alerts = self.get_alerts()
        
        output = []
        output.append("=" * 80)
        output.append(f"🚀 WealthPath AI - Shadow Mode Status - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        output.append("=" * 80)
        
        if not metrics:
            output.append("⚠️  Cannot connect to server. Make sure it's running!")
            output.append(f"Expected URL: {self.base_url}")
            output.append("Run: bash start_shadow_mode.sh")
            return "\n".join(output)
        
        # Overall status
        readiness = metrics.get('readiness_score', 0)
        status = "🟢 READY" if readiness > 0.9 else "🟡 IN PROGRESS" if readiness > 0.7 else "🔴 NOT READY"
        output.append(f"Overall Status: {status} ({readiness:.1%})")
        
        # Shadow mode stats
        shadow_stats = metrics.get('shadow_mode_stats', {})
        shadow_enabled = metrics.get('checklist', {}).get('shadow_mode', {}).get('enabled', False)
        
        output.append(f"Shadow Mode: {'✅ ENABLED' if shadow_enabled else '❌ DISABLED'}")
        
        comparisons = shadow_stats.get('total_comparisons', 0)
        runtime_hours = shadow_stats.get('runtime_hours', 0)
        
        output.append(f"Comparisons: {comparisons} / 100 target")
        output.append(f"Runtime: {runtime_hours:.1f}h / 48h target")
        
        if comparisons > 0:
            quality_metrics = shadow_stats.get('quality_metrics', {})
            similarity = quality_metrics.get('average_similarity', 0)
            
            status_icon = "✅" if similarity > 0.95 else "⚠️" if similarity > 0.90 else "❌"
            output.append(f"Quality: {status_icon} {similarity:.2%} similarity")
            
            # Performance
            perf_metrics = shadow_stats.get('performance_metrics', {})
            cache_hit_rate = perf_metrics.get('cache_hit_rate', 0)
            output.append(f"Cache Hit Rate: {cache_hit_rate:.1%}")
            
            # Cost savings
            cost_metrics = shadow_stats.get('cost_metrics', {})
            total_cost = cost_metrics.get('total_cost_savings', 0)
            output.append(f"Cost Savings: ${total_cost:.4f}")
        
        # Health
        if health:
            health_status = health.get('status', 'unknown')
            health_icon = "✅" if health_status == 'healthy' else "⚠️" if health_status == 'degraded' else "❌"
            output.append(f"System Health: {health_icon} {health_status.title()}")
        
        # Alerts
        if alerts and alerts.get('current_alerts'):
            alert_count = len(alerts['current_alerts'])
            output.append(f"Active Alerts: 🚨 {alert_count}")
            
            for alert in alerts['current_alerts'][:2]:  # Show max 2
                level = alert.get('level', 'info').upper()
                message = alert.get('message', 'Unknown alert')
                output.append(f"  [{level}] {message}")
        
        # Recommendations
        recommendations = metrics.get('recommendations', [])
        if recommendations:
            output.append("\n💡 Next Steps:")
            for rec in recommendations[:3]:
                output.append(f"  • {rec}")
        
        return "\n".join(output)
    
    def run_monitoring_loop(self):
        """Run the main monitoring loop"""
        if RICH_AVAILABLE:
            print("🚀 Starting Rich monitoring dashboard...")
            print("Press Ctrl+C to exit")
            
            with Live(self.create_rich_dashboard(), refresh_per_second=0.5, console=self.console) as live:
                while True:
                    live.update(self.create_rich_dashboard())
                    time.sleep(2)
        else:
            print("🚀 Starting simple monitoring dashboard...")
            print("Press Ctrl+C to exit\n")
            
            try:
                while True:
                    # Clear screen for simple dashboard
                    print("\033[2J\033[H", end="")
                    print(self.create_simple_dashboard())
                    time.sleep(5)
            except KeyboardInterrupt:
                pass

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Monitor shadow mode progress")
    parser.add_argument("--url", default="http://localhost:8000", help="Base URL for the API")
    parser.add_argument("--once", action="store_true", help="Run once and exit (no live updates)")
    
    args = parser.parse_args()
    
    monitor = ShadowModeMonitor(base_url=args.url)
    
    if args.once:
        # Single run mode
        if RICH_AVAILABLE:
            console = Console()
            console.print(monitor.create_rich_dashboard())
        else:
            print(monitor.create_simple_dashboard())
        return
    
    # Live monitoring mode
    try:
        monitor.run_monitoring_loop()
    except KeyboardInterrupt:
        if RICH_AVAILABLE:
            Console().print("\n[yellow]Monitoring stopped[/yellow]")
        else:
            print("\n⏹️ Monitoring stopped")
    except Exception as e:
        if RICH_AVAILABLE:
            Console().print(f"\n[red]Error: {e}[/red]")
        else:
            print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()