# Chord DHT - Experiments

Python implementation of Chord DHT with performance evaluation experiments.

## Available Experiments

### 1. Simple Experiment (`experiment_1.py`)
Basic 4-node Chord ring experiment with mixed GET/SET workload.

**Run:**
```bash
python3 experiment_1.py
```

**Output:**
- `experiment_1.json` - Metrics and latency data
- Console output with performance summary

---

### 2. Comprehensive Experiments (`run_all_experiments.py`)
Three experiments evaluating different aspects of Chord DHT:

1. **Scaling (2-256 nodes)** - Tests O(log N) lookup complexity
2. **WAN Latency (5-20ms)** - Measures network delay impact  
3. **Node Failures** - Tests fault tolerance and recovery

**Run all experiments:**
```bash
python3 run_all_experiments.py
```

**Run individual experiment:**
```bash
python3 run_all_experiments.py --experiment 1  # Scaling
python3 run_all_experiments.py --experiment 2  # WAN
python3 run_all_experiments.py --experiment 3  # Node Failures
```

**Output:**
- `results/experiment_scaling.json`
- `results/experiment_wan.json`
- `results/experiment_node_failures.json`

**Generate visualization:**
```bash
.venv/bin/python plot_all_experiments.py
```
- Creates: `plots/experiments_summary.png` (3-panel figure)

---

## Quick Start

```bash
# Setup
python3 -m venv .venv
source .venv/bin/activate
pip install matplotlib

# Run experiments
python3 experiment_1.py                    # Simple test
python3 run_all_experiments.py             # All 3 experiments
.venv/bin/python plot_all_experiments.py   # Generate plots
```

---

## Results Location

- **Simple experiment**: `experiment_1.json` (in current directory)
- **Comprehensive experiments**: `results/` directory
  - `experiment_scaling.json`
  - `experiment_wan.json`
  - `experiment_node_failures.json`
- **Visualization**: `plots/experiments_summary.png`
```

## Key Modifications to Original Code

### 1. `chord.py`
- **SO_REUSEADDR**: Added socket option to allow port reuse after node restart
- **Error Handling**: Added exception handling in `fix_fingers()` and `send_to_socket()` to prevent thread crashes

### 2. `dht.py`
- **Dictionary Iteration Fix**: Fixed `RuntimeError` by creating snapshot with `list(self.data_.keys())`
- **Migration Error Handling**: Added exception handling for socket errors during data migration

### 3. `remote.py`
- **Empty Response Handling**: Added JSONDecodeError handling in `successor()` method

### 4. New Files
- `metrics.py`: Metrics collection system
- `network.py`: Network simulation layer
- `run_all_experiments.py`: Comprehensive experiment runner
- `plot_all_experiments.py`: Visualization script

## Experiments

### Experiment 1: Scaling (2-256 nodes)
**Goal**: Measure lookup performance as ring size increases  
**Scenarios**: 2, 4, 8, 16, 32, 64, 128, 256 nodes  
**Result**: Sublinear growth consistent with O(log N)

### Experiment 2: WAN Latency Simulation
**Goal**: Quantify impact of network delay  
**Scenarios**: 0ms (LAN), 5ms, 10ms, 20ms one-way delay  
**Result**: Multi-hop lookups compound delay (57x at 20ms)

### Experiment 5: Node Failures and Recovery
**Goal**: Assess availability during crashes  
**Scenario**: 8-node ring, crash 2 nodes (25%), restart  
**Result**: Zero failed RPCs, automatic recovery

## Running the Experiments

### Prerequisites
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install matplotlib
```

### Run All Experiments
```bash
python3 run_all_experiments.py
```

### Run Individual Experiments
```bash
python3 run_all_experiments.py --experiment 1  # Scaling
python3 run_all_experiments.py --experiment 2  # WAN
python3 run_all_experiments.py --experiment 5  # Node failures
```

### Generate Plots
```bash
.venv/bin/python plot_all_experiments.py
```

## Results

Results are saved as JSON in `results/`:
- `experiment_scaling.json`
- `experiment_wan.json`
- `experiment_node_failures.json`

Plots are saved in `plots/experiments_summary.png`

## Original Implementation

Based on: Stoica, I., Morris, R., Karger, D., Kaashoek, M. F., & Balakrishnan, H. (2001). Chord: A scalable peer-to-peer lookup service for internet applications. *ACM SIGCOMM*, 31(4), 149-160.

Original repository: [gingaramo/python-chord](https://github.com/gingaramo/python-chord)

## License

See [LICENSE](LICENSE) file.