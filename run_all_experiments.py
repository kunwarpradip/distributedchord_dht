#!/usr/bin/env python3

import sys
import time
import json
import os
from address import Address
from dht import DHT
from metrics import metrics_registry
from network import configure_network_profile

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.join(BASE_DIR, 'results')

def ensure_results_dir():
    os.makedirs(RESULTS_DIR, exist_ok=True)

def save_results(name, data):
    path = os.path.join(RESULTS_DIR, f'experiment_{name}.json')
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

def create_ring(num_nodes, base_port=6000):
    nodes = []
    
    try:
        bootstrap = Address("127.0.0.1", base_port)
        node0 = DHT(bootstrap)
        nodes.append(node0)
        time.sleep(1.5)
        
        for i in range(1, num_nodes):
            addr = Address("127.0.0.1", base_port + i)
            node = DHT(addr, bootstrap)
            nodes.append(node)
            time.sleep(0.5) 
        
        if num_nodes > 16:
            time.sleep(2.0)
    
        return nodes
    except Exception as e:
        for node in nodes:
            try:
                node.shutdown()
            except:
                pass
        time.sleep(2.0)
        raise

def seed_data(nodes, num_keys=10):
    for i in range(num_keys):
        nodes[0].set(f"key_{i}", f"value_{i}")
        time.sleep(0.05)

def run_workload(nodes, num_ops=20, read_ratio=0.7):
    import random  
    keys = [f"key_{i}" for i in range(10)]
    num_gets = int(num_ops * read_ratio)
    num_sets = num_ops - num_gets
    ops = ['get'] * num_gets + ['set'] * num_sets
    random.shuffle(ops)
    
    for i, op in enumerate(ops):
        node = random.choice(nodes)
        key = random.choice(keys)
        try:
            if op == 'get':
                node.get(key)
            else:
                node.set(key, f"updated_value_{i}")
        except Exception as e:
            print(f"Op {i} failed: {e}")

        time.sleep(0.05)

def cleanup_nodes(nodes):
    for node in nodes:
        try:
            node.shutdown()
        except:
            pass
    time.sleep(3.0)

def experiment_1_scaling():
    node_counts = [2, 4, 8, 16, 32, 64, 128, 256]
    results = []
    
    for idx, N in enumerate(node_counts):
        print(f"Testing N={N} nodes...")
        
        metrics_registry.reset()
        configure_network_profile(delay_ms=0, drop_rate=0)
        
        # Use different port range for each iteration to avoid conflicts
        base_port = 6000 + (idx * 300)
        
        # Create ring and run workload
        nodes = create_ring(N, base_port=base_port)
        seed_data(nodes, num_keys=10)
        run_workload(nodes, num_ops=20)
        
        snapshot = metrics_registry.snapshot()

        get_latency = snapshot['latencies'].get('rpc.latency.get', {}).get('avg_time', 0) * 1000
        set_latency = snapshot['latencies'].get('rpc.latency.set', {}).get('avg_time', 0) * 1000
        
        results.append({
            'num_nodes': N,
            'log2_nodes': __import__('math').log2(N),
            'get_latency_ms': get_latency,
            'set_latency_ms': set_latency,
            'full_snapshot': snapshot
        })
        cleanup_nodes(nodes)
        time.sleep(1.0)
    
    save_results('scaling', {'scenarios': results})
    return results

def experiment_2_wan():
    # Using lower delays to avoid timeouts (delays multiply across hops)
    delay_configs = [
        {'delay_ms': 0, 'jitter_ms': 0, 'label': 'Baseline (LAN)'},
        {'delay_ms': 5, 'jitter_ms': 2, 'label': 'Light WAN (5ms)'},
        {'delay_ms': 10, 'jitter_ms': 3, 'label': 'WAN (10ms)'},
        {'delay_ms': 20, 'jitter_ms': 5, 'label': 'High latency (20ms)'},
    ]
    
    results = []
    
    for i, config in enumerate(delay_configs):
        print(f"Testing: {config['label']}...")
        
        metrics_registry.reset()
        configure_network_profile(
            delay_ms=config['delay_ms'],
            jitter_ms=config['jitter_ms'],
            drop_rate=0
        )
        
        # Use different port range for each iteration (high ports to avoid conflicts)
        base_port = 17000 + (i * 100)
        nodes = create_ring(4, base_port=base_port)
        seed_data(nodes, num_keys=10)
        run_workload(nodes, num_ops=20)
        
        snapshot = metrics_registry.snapshot()
        get_lat = snapshot['latencies'].get('rpc.latency.get', {}).get('avg_time', 0) * 1000
        set_lat = snapshot['latencies'].get('rpc.latency.set', {}).get('avg_time', 0) * 1000
        
        results.append({
            'config': config,
            'get_latency_ms': get_lat,
            'set_latency_ms': set_lat,
            'full_snapshot': snapshot
        })
        
        cleanup_nodes(nodes)
        time.sleep(1.0)
    
    save_results('wan', {'scenarios': results})
    return results


def experiment_3_node_failures():

    metrics_registry.reset()
    configure_network_profile(delay_ms=0, drop_rate=0)
    
    nodes = create_ring(8, base_port=10000)
    seed_data(nodes, num_keys=20)
    run_workload(nodes, num_ops=30)
    
    snapshot_baseline = metrics_registry.snapshot()
    baseline_success = snapshot_baseline['counters'].get('rpc.success', 0)

    nodes[2].shutdown()
    nodes[3].shutdown()
    
    time.sleep(2.0)  # Let ring detect failures
    
    metrics_registry.reset()
    run_workload([nodes[0], nodes[1], nodes[4], nodes[5], nodes[6], nodes[7]], num_ops=20)
    
    snapshot_failure = metrics_registry.snapshot()
    failure_success = snapshot_failure['counters'].get('rpc.success', 0)
    failure_failures = snapshot_failure['counters'].get('rpc.failure', 0)
    time.sleep(5.0)

    bootstrap = Address("127.0.0.1", 10000)
    nodes[2] = DHT(Address("127.0.0.1", 10002), bootstrap)
    nodes[3] = DHT(Address("127.0.0.1", 10003), bootstrap)
    time.sleep(3.0)  
    
    metrics_registry.reset()
    run_workload(nodes, num_ops=20)
    
    snapshot_recovery = metrics_registry.snapshot()
    recovery_success = snapshot_recovery['counters'].get('rpc.success', 0)
    
    cleanup_nodes(nodes)
    
    results = {
        'baseline': {
            'success_count': baseline_success,
            'full_snapshot': snapshot_baseline
        },
        'during_failure': {
            'success_count': failure_success,
            'failure_count': failure_failures,
            'full_snapshot': snapshot_failure
        },
        'after_recovery': {
            'success_count': recovery_success,
            'full_snapshot': snapshot_recovery
        }
    }
    
    save_results('node_failures', results)
    return results


def main():

    import argparse
    parser = argparse.ArgumentParser(description='Run Chord DHT experiments')
    parser.add_argument('--experiment', type=int, choices=[1,2,3], 
                       help='Run only specified experiment (1-3)')
    args = parser.parse_args()
    
    ensure_results_dir()
    start_time = time.time()
    
    try:
        if args.experiment == 1 or not args.experiment:
            experiment_1_scaling()
        if args.experiment == 2 or not args.experiment:
            experiment_2_wan()
        if args.experiment == 3 or not args.experiment:
            experiment_3_node_failures()
        
        elapsed = time.time() - start_time
        
    except KeyboardInterrupt:
        print("\n\nExperiments interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
