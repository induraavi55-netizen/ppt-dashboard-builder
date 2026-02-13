import sys
import os
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent))

import pandas as pd
from app.services.metric_classifier import classify_metric
from app.services.dataset_profiler import profile_dataset

def test_percent_classification():
    print("\n--- Testing Percent Classification ---")
    
    cases = [
        ("Avg Performance", [18, 17, 17], "percent", "Values 0-100 with 'performance' in name"),
        ("Avg Performance (%)", [18, 17, 17], "percent", "Explicit % in name"),
        ("Participation %", [0.85, 0.90, 0.88], "percent", "Explicit % in name with 0-1 range"),
        ("Subject", ["English", "Math", "Science"], "generic", "Generic dimension"),
        ("Total Students", [40, 45, 38], "count", "Total/count pattern"),
        ("Growth", [5, 10, -2], "generic", "Numeric but out of normal percent 0-100 range and no name hint"),
    ]
    
    for name, vals, expected, desc in cases:
        result = classify_metric(name, vals)
        status = "PASS" if result == expected else "FAIL"
        print(f"{status} [{name}] -> {result} (Expected: {expected}) | {desc}")
        if result != expected:
            sys.exit(1)

def test_profiler_integration():
    print("\n--- Testing Profiler Integration ---")
    
    dataset = {
        "name": "all_subjects_perf_summary",
        "schema": {
            "dimensions": ["Subject"],
            "metrics": ["Avg Performance"]
        },
        "preview": [
            {"Subject": "English", "Avg Performance": 18},
            {"Subject": "Math", "Avg Performance": 17},
            {"Subject": "Science", "Avg Performance": 17}
        ]
    }
    
    profile = profile_dataset(dataset)
    
    print(f"Dataset Family: {profile['dataset_family']}")
    print(f"Metric Types: {profile['metric_types']}")
    print(f"Dataset Type: {profile['type']}")
    
    if profile['metric_types'].get("Avg Performance") == "percent":
        print("PASS: Profiler correctly identified numeric performance column as percent.")
    else:
        print("FAIL: Profiler failed to identify percent.")
        sys.exit(1)

if __name__ == "__main__":
    try:
        test_percent_classification()
        test_profiler_integration()
        print("\nAll tests passed!")
    except Exception as e:
        print(f"\nTest failed with exception: {e}")
        sys.exit(1)
