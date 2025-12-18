#!/usr/bin/env python3
"""
Simple Separability Score Checker
Quick check if gestures are distinguishable
"""

import json
import os
import sys
import numpy as np

def load_session(session_name, target_length=200):
    """Load and normalize session data"""
    session_dir = os.path.join("training_data", session_name)

    if not os.path.exists(session_dir):
        print(f"✗ Session '{session_name}' not found!")
        return None

    data_by_gesture = {}

    for filename in os.listdir(session_dir):
        if filename.endswith('.jsonl'):
            gesture_name = filename.replace('.jsonl', '')
            samples = []

            filepath = os.path.join(session_dir, filename)
            with open(filepath, 'r') as f:
                for line in f:
                    sample = json.loads(line)
                    data = np.array(sample['data'])

                    # Normalize to target_length
                    if len(data) > target_length:
                        data = data[:target_length]
                    elif len(data) < target_length:
                        pad_length = target_length - len(data)
                        padding = np.tile(data[-1], (pad_length, 1))
                        data = np.vstack([data, padding])

                    samples.append(data)

            if samples:
                data_by_gesture[gesture_name] = np.array(samples)

    return data_by_gesture

def calculate_separability(data_by_gesture):
    """Calculate separability ratio"""

    # Extract MAV features
    features_by_gesture = {}
    for gesture, samples in data_by_gesture.items():
        mav_features = []
        for sample in samples:
            mav = np.mean(np.abs(sample), axis=0)
            mav_features.append(mav)
        features_by_gesture[gesture] = np.array(mav_features)

    # Calculate mean features per gesture
    gesture_means = {}
    for gesture, features in features_by_gesture.items():
        gesture_means[gesture] = np.mean(features, axis=0)

    # Calculate pairwise distances between gestures
    gestures = list(gesture_means.keys())
    distances = []
    for i, g1 in enumerate(gestures):
        for j, g2 in enumerate(gestures):
            if i < j:
                dist = np.linalg.norm(gesture_means[g1] - gesture_means[g2])
                distances.append(dist)

    avg_distance = np.mean(distances)
    min_distance = np.min(distances)

    # Calculate within-gesture variance
    avg_std = np.mean([np.mean(np.std(f, axis=0)) for f in features_by_gesture.values()])

    # Separability ratio
    ratio = avg_distance / avg_std if avg_std > 0 else 0

    return ratio, avg_distance, min_distance, avg_std

def main():
    # Get session name from command line or use latest
    if len(sys.argv) > 1:
        session_name = sys.argv[1]
    else:
        training_data_dir = "training_data"
        sessions = [d for d in os.listdir(training_data_dir)
                   if os.path.isdir(os.path.join(training_data_dir, d))]
        if not sessions:
            print("✗ No training data found!")
            return

        # Most recent session
        sessions.sort(key=lambda s: os.path.getmtime(os.path.join(training_data_dir, s)), reverse=True)
        session_name = sessions[0]

    print("=" * 70)
    print("SEPARABILITY SCORE CHECKER")
    print("=" * 70)
    print(f"\nSession: {session_name}")

    # Load data
    data = load_session(session_name)

    if not data:
        print("✗ No data found in session!")
        return

    total_samples = sum(len(samples) for samples in data.values())
    print(f"Gestures: {len(data)}")
    print(f"Total samples: {total_samples}")
    print()

    for gesture, samples in sorted(data.items()):
        print(f"  {gesture:12s}: {len(samples):3d} samples")

    # Calculate separability
    ratio, avg_dist, min_dist, avg_std = calculate_separability(data)

    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)
    print()
    print(f"Avg distance between gestures: {avg_dist:8.0f}")
    print(f"Min distance between gestures: {min_dist:8.0f}")
    print(f"Avg within-gesture spread:     {avg_std:8.0f}")
    print()
    print(f"Separability Ratio: {ratio:.2f}")
    print()
    print("-" * 70)

    # Assessment
    if ratio > 2.5:
        print("✓ EXCELLENT - Gestures are well-separated!")
        print("  → Ready to collect full dataset (300+ samples/gesture)")
        print("  → Expected accuracy: 85-95%")
    elif ratio > 2.0:
        print("✓ GOOD - Gestures are distinguishable")
        print("  → Can collect full dataset")
        print("  → Expected accuracy: 75-85%")
    elif ratio > 1.5:
        print("⚠ MARGINAL - Gestures are somewhat distinguishable")
        print("  → Make gestures MORE exaggerated")
        print("  → Try another separability test")
        print("  → Expected accuracy: 60-75%")
    else:
        print("✗ POOR - Gestures are too similar or too noisy")
        print("  → DO NOT collect more data yet!")
        print("  → Fix issues first:")
        print("    • Make gestures MUCH more exaggerated")
        print("    • Check electrode placement")
        print("    • Ensure consistent gesture performance")
        print("  → Run another separability test after adjustments")

    print("-" * 70)
    print()

    if ratio >= 2.0:
        print("Next step: python collect_data_auto.py")
        print("           Select [6] - 15-Minute Standard Session")
    else:
        print("Next step: Fix gestures, then run another separability test")
        print("           python collect_data_auto.py")
        print("           Select [2] - Separability Test")

    print()
    print("For detailed analysis: python quick_data_check.py")
    print("=" * 70)

if __name__ == "__main__":
    main()
