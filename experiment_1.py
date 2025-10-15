#!/usr/bin/env python3
import sys
import time
import json
from address import Address
from dht import DHT
from metrics import metrics_registry
from network import configure_network_profile

def create_ring(num_nodes=4, base_port=5000):
    print(f"Creating {num_nodes}-node Chord ring")
    
    nodes = []

    #first node
    bootstrap_addr = Address("127.0.0.1", base_port)
    print(f"  Node 0: {bootstrap_addr}")
    node0 = DHT(bootstrap_addr)  
    nodes.append(node0)
    time.sleep(1.5) 
    
    # remaining nodes join
    for i in range(1, num_nodes):
        port = base_port + i
        addr = Address("127.0.0.1", port)
        print(f"  Node {i}: {addr}")
        node = DHT(addr, bootstrap_addr) 
        nodes.append(node)
        time.sleep(1.0)  
    
    print(f"Ring done with {num_nodes} nodes\n")
    return nodes

def run_workload(nodes, num_operations=20, read_ratio=0.7):
    print(f"workload running with {num_operations} operations (read_ratio={read_ratio})")
    
    import random
    
    #write data workload
    print("Writing data")
    keys = [f"key_{i}" for i in range(10)]
    for key in keys:
        value = f"value_for_{key}"
        nodes[0].set(key, value)
        time.sleep(0.1)
    
    print(f"Done writing")
    
    # read/write workload
    print("read/write operations")
    num_gets = int(num_operations * read_ratio)
    num_sets = num_operations - num_gets
    
    operations = ['get'] * num_gets + ['set'] * num_sets
    random.shuffle(operations)
    
    for i, op in enumerate(operations):
        node = random.choice(nodes)
        key = random.choice(keys)
        
        if op == 'get':
            node.get(key)
        else:
            node.set(key, f"updated_value_{i}")
        
        time.sleep(0.05)  # Small delay
    
    print(f"read/write complete\n")

def print_metrics_summary(data): 
    if data['latencies']:
        for name, stats in sorted(data['latencies'].items()):
            print(f"\n{name}:")
            print(f"Count:{stats['count']}")
            print(f"Avg:{stats['avg_time']*1000:.2f} ms")
            print(f"Min:{stats['min_time']*1000:.2f} ms")
            print(f"Max:{stats['max_time']*1000:.2f} ms")
            print(f"Throughput:{stats['throughput_per_sec']:.2f} ops/sec")
    
    # Counters
    if data['counters']:
        for name, value in sorted(data['counters'].items()):
            print(f"  {name}: {value}")
    
    print(f"\n\nTotal Time: {data['elapsed_seconds']:.2f} seconds")

def main():
    #Configure normal network and create ring
    configure_network_profile(delay_ms=0, jitter_ms=0, drop_rate=0)
    nodes = create_ring(num_nodes=4, base_port=5000)
    
    #Run workload and collect metrics
    run_workload(nodes, num_operations=20, read_ratio=0.7)
    results = metrics_registry.snapshot()
    
    output_file = "experiment_1.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    print_metrics_summary(results)
    
    #Shutdown nodes
    print("\nShutting down nodes...")
    for i, node in enumerate(nodes):
        try:
            node.shutdown()
            print(f"  Node {i} shutdown")
        except Exception as e:
            print(f"  Node {i} shutdown error: {e}")
    
    time.sleep(1) 
    sys.exit(0) 

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
