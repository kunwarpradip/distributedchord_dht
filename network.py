"""
Network Layer with Simulation Capabilities
===========================================

This module handles all socket communication in python-chord.
We've added simulation capabilities to test the system under realistic conditions:

1. **Latency Simulation**: Add artificial delays to simulate WAN/datacenter networks
2. **Jitter**: Random variation in latency (realistic networks aren't consistent)
3. **Packet Loss**: Randomly drop packets to test retry mechanisms
4. **Network Partitions**: Isolate groups of nodes to test split-brain scenarios

Why simulate these conditions?
- Real distributed systems face these issues in production
- Testing locally with simulation is faster than deploying to multiple datacenters
- We can reproduce bugs by controlling the network conditions
"""

import random
import socket
import threading
import time


# Global network profile - controls all simulation parameters
NETWORK_PROFILE = {
	'delay_ms': 0.0,           # Base latency to add (milliseconds)
	'jitter_ms': 0.0,          # Random variation (+/- this amount)
	'drop_rate': 0.0,          # Probability of packet loss (0.0 to 1.0)
	'isolated_ports': set(),   # Ports that can't communicate (partition simulation)
}

# Lock to safely update the profile from multiple threads
_profile_lock = threading.Lock()


def configure_network_profile(delay_ms=0.0, jitter_ms=0.0, drop_rate=0.0, isolated_ports=None):
	#configure network simulation parameters for experiments.

	with _profile_lock:
		NETWORK_PROFILE['delay_ms'] = max(delay_ms, 0.0)
		NETWORK_PROFILE['jitter_ms'] = max(jitter_ms, 0.0)
		NETWORK_PROFILE['drop_rate'] = min(max(drop_rate, 0.0), 1.0)
		NETWORK_PROFILE['isolated_ports'] = set() if isolated_ports is None else set(isolated_ports)


def _should_isolate(socket_obj):
	#Check if this socket connection should be blocked (partition simulation).
	try:
		local_port = socket_obj.getsockname()[1]
		peer_port = socket_obj.getpeername()[1]
	except socket.error:
		return False
	
	with _profile_lock:
		isolated = NETWORK_PROFILE['isolated_ports']
		return local_port in isolated or peer_port in isolated


# reads from socket until "\r\n"
def read_from_socket(s):
	result = bytearray()
	while 1:
		data = s.recv(256)
		if not data:
			break
		result.extend(data)
		if result.endswith(b"\r\n"):
			result = result[:-2]
			break
	return result.decode("utf-8")

# sends all on socket, adding "\r\n"
def send_to_socket(s, msg):
	#Send a message over a socket with simulation applied.
	
	if isinstance(msg, str):
		payload = msg.encode("utf-8")
	else:
		payload = msg

	with _profile_lock:
		delay_ms = NETWORK_PROFILE['delay_ms']
		jitter_ms = NETWORK_PROFILE['jitter_ms']
		drop_rate = NETWORK_PROFILE['drop_rate']
	
	# Apply latency + jitter
	if delay_ms or jitter_ms:
		jitter_component = random.uniform(-jitter_ms, jitter_ms) if jitter_ms else 0.0
		total_delay = max(delay_ms + jitter_component, 0.0) / 1000.0  # Convert to seconds
		
		if total_delay:
			time.sleep(total_delay)  
	
	# Check for network partition
	if _should_isolate(s):
		raise socket.error("Simulated network partition")
	
	# Simulate packet loss
	if drop_rate and random.random() < drop_rate:
		raise socket.error("Simulated packet drop")
	
	s.sendall(payload + b"\r\n")
