"""
Background Memory Optimizer
Continuously optimizes and maintains the active memory cache
Runs as a background thread/process
"""
import threading
import time
from typing import Optional
from datetime import datetime, timedelta
from .active_memory import get_active_memory


class MemoryOptimizer:
    """
    Background service that continuously optimizes active memory:
    1. Runs periodic optimization cycles
    2. Compresses old memories
    3. Removes duplicates
    4. Updates statistics
    """

    def __init__(self, optimization_interval: int = 300):
        """
        Initialize memory optimizer

        Args:
            optimization_interval: Seconds between optimization cycles (default: 5 minutes)
        """
        self.optimization_interval = optimization_interval
        self.memory = get_active_memory()

        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._last_optimization: Optional[datetime] = None

        print(f"✓ Memory Optimizer initialized (interval: {optimization_interval}s)")

    def start(self):
        """Start the background optimizer"""
        if self._running:
            print("Memory optimizer already running")
            return

        self._running = True
        self._thread = threading.Thread(target=self._optimization_loop, daemon=True)
        self._thread.start()

        print("🔄 Memory optimizer started in background")

    def stop(self):
        """Stop the background optimizer"""
        if not self._running:
            return

        self._running = False
        if self._thread:
            self._thread.join(timeout=5)

        print("🛑 Memory optimizer stopped")

    def _optimization_loop(self):
        """Main optimization loop (runs in background thread)"""
        print("🔧 Memory optimization loop started")

        while self._running:
            try:
                # Wait for the interval
                time.sleep(self.optimization_interval)

                if not self._running:
                    break

                # Run optimization
                print(f"\n🔧 Running memory optimization cycle at {datetime.now().strftime('%H:%M:%S')}")
                self._optimize()

            except Exception as e:
                print(f"⚠ Error in optimization loop: {e}")
                # Continue running despite errors
                time.sleep(60)  # Wait a minute before retrying

    def _optimize(self):
        """Perform optimization cycle"""
        start_time = time.time()

        # Get pre-optimization stats
        stats_before = self.memory.get_stats()
        total_before = stats_before.get('current_total', 0)

        print(f"  Memories before: {total_before}")

        # Run optimization
        self.memory.optimize_memory()

        # Get post-optimization stats
        stats_after = self.memory.get_stats()
        total_after = stats_after.get('current_total', 0)

        elapsed = time.time() - start_time
        self._last_optimization = datetime.now()

        print(f"  Memories after: {total_after}")
        print(f"  Optimization took {elapsed:.2f}s")
        print(f"✓ Memory optimization cycle complete\n")

    def force_optimize(self):
        """Force an immediate optimization cycle"""
        print("🔧 Forcing immediate memory optimization...")
        self._optimize()

    def get_status(self) -> dict:
        """Get optimizer status"""
        return {
            'running': self._running,
            'last_optimization': self._last_optimization.isoformat() if self._last_optimization else None,
            'optimization_interval': self.optimization_interval,
            'next_optimization_in': self._get_seconds_until_next_optimization()
        }

    def _get_seconds_until_next_optimization(self) -> Optional[int]:
        """Calculate seconds until next optimization"""
        if not self._last_optimization or not self._running:
            return None

        next_optimization = self._last_optimization + timedelta(seconds=self.optimization_interval)
        delta = next_optimization - datetime.now()

        return max(0, int(delta.total_seconds()))


# Singleton instance
_optimizer = None


def get_memory_optimizer(optimization_interval: int = 300) -> MemoryOptimizer:
    """
    Get or create singleton MemoryOptimizer instance

    Args:
        optimization_interval: Seconds between optimization cycles

    Returns:
        MemoryOptimizer instance
    """
    global _optimizer

    if _optimizer is None:
        _optimizer = MemoryOptimizer(optimization_interval)

    return _optimizer


def start_background_optimizer(optimization_interval: int = 300):
    """
    Start the background memory optimizer

    Args:
        optimization_interval: Seconds between optimization cycles
    """
    optimizer = get_memory_optimizer(optimization_interval)
    optimizer.start()
    return optimizer


if __name__ == "__main__":
    # Test the optimizer
    print("Testing Memory Optimizer...")

    # Create optimizer
    optimizer = MemoryOptimizer(optimization_interval=10)  # 10 seconds for testing

    # Start it
    optimizer.start()

    print("\nOptimizer running in background...")
    print("Status:", optimizer.get_status())

    # Wait for a couple of cycles
    print("\nWaiting for 25 seconds to see 2-3 optimization cycles...")
    time.sleep(25)

    # Force an optimization
    print("\nForcing immediate optimization...")
    optimizer.force_optimize()

    # Check status
    print("\nFinal status:", optimizer.get_status())

    # Stop optimizer
    optimizer.stop()

    print("\n✅ Memory Optimizer test complete!")
