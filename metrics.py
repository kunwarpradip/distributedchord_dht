
import threading
import time
from collections import defaultdict


class MetricsRegistry:
	def __init__(self):
		self._lock = threading.Lock()  # Protects against concurrent access
		self.reset()

	def reset(self):
		with self._lock:  # thread safety
			self._metrics = defaultdict(lambda: {
				'count': 0,         # How many times recorded
				'total_time': 0.0,  # Sum of all durations
				'max_time': 0.0,    # Slowest operation
				'min_time': None,   # Fastest operation
			})
			self._counters = defaultdict(int)
			self._start_time = time.monotonic()

	def record_latency(self, name, duration_seconds):
		with self._lock:
			entry = self._metrics[name]
			entry['count'] += 1
			entry['total_time'] += duration_seconds
			entry['max_time'] = max(entry['max_time'], duration_seconds)
			
			# Set min_time on first recording
			if entry['min_time'] is None:
				entry['min_time'] = duration_seconds
			else:
				entry['min_time'] = min(entry['min_time'], duration_seconds)

	def increment(self, name, value=1):
		with self._lock:
			self._counters[name] += value

	def snapshot(self):
		with self._lock:
			elapsed = max(time.monotonic() - self._start_time, 1e-9)  #avoid division by zero
			
			latencies = {}
			for name, data in self._metrics.items():
				entry = dict(data)
				
				if entry['count']:
					entry['avg_time'] = entry['total_time'] / entry['count']
					entry['throughput_per_sec'] = entry['count'] / elapsed
				else:
					entry['avg_time'] = 0.0
					entry['throughput_per_sec'] = 0.0
				
				latencies[name] = entry
			
			return {
				'latencies': latencies,      
				'counters': dict(self._counters), 
				'elapsed_seconds': elapsed, 
			}

metrics_registry = MetricsRegistry()

__all__ = [
	"MetricsRegistry",
	"metrics_registry",
]
