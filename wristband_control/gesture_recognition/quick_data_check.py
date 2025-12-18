#!/usr/bin/env python3
"""Quick data quality check - handles variable-length samples"""

import json
import os
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt

def load_and_normalize(session_name="Jay10_v1", target_length=200):
    """Load data and normalize to fixed length"""
    session_dir = os.path.join("training_data", session_name)

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

                    # Truncate or pad to target_length
                    if len(data) > target_length:
                        data = data[:target_length]
                    elif len(data) < target_length:
                        # Pad with last value
                        pad_length = target_length - len(data)
                        padding = np.tile(data[-1], (pad_length, 1))
                        data = np.vstack([data, padding])

                    samples.append(data)

            if samples:
                data_by_gesture[gesture_name] = np.array(samples)
                print(f"{gesture_name:12s}: {len(samples):3d} samples, shape {samples[0].shape}")

    return data_by_gesture

def extract_mav_features(data_by_gesture):
    """Extract Mean Absolute Value features"""
    features_by_gesture = {}

    for gesture, samples in data_by_gesture.items():
        mav_features = []
        for sample in samples:
            # Calculate MAV for each channel
            mav = np.mean(np.abs(sample), axis=0)
            mav_features.append(mav)
        features_by_gesture[gesture] = np.array(mav_features)

    return features_by_gesture

def analyze_separability(features_by_gesture):
    """Check if gestures are distinguishable"""
    print("\n" + "=" * 70)
    print("GESTURE SEPARABILITY ANALYSIS")
    print("=" * 70)

    # Show mean features
    print("\nMean MAV per channel:")
    gestures = sorted(features_by_gesture.keys())

    print(f"\n{'Gesture':<12}", end="")
    for ch in range(4):
        print(f"  Ch{ch+1:d}  ", end="")
    print()
    print("-" * 50)

    gesture_means = {}
    for gesture in gestures:
        features = features_by_gesture[gesture]
        mean_mav = np.mean(features, axis=0)
        gesture_means[gesture] = mean_mav

        print(f"{gesture:<12}", end="")
        for ch in range(4):
            print(f"{mean_mav[ch]:7.0f}", end="")
        print()

    # Calculate pairwise distances
    print("\n" + "=" * 70)
    print("PAIRWISE GESTURE DISTANCES")
    print("=" * 70)

    print(f"\n{'':<12}", end="")
    for g in gestures:
        print(f"{g[:8]:>10}", end="")
    print()

    all_distances = []
    for i, g1 in enumerate(gestures):
        print(f"{g1:<12}", end="")
        for j, g2 in enumerate(gestures):
            if i == j:
                print(f"{'---':>10}", end="")
            else:
                dist = np.linalg.norm(gesture_means[g1] - gesture_means[g2])
                all_distances.append(dist)
                print(f"{dist:>10.0f}", end="")
        print()

    # Calculate within-gesture variance
    print("\n" + "=" * 70)
    print("WITHIN-GESTURE VARIABILITY")
    print("=" * 70)

    print()
    for gesture in gestures:
        features = features_by_gesture[gesture]
        std = np.mean(np.std(features, axis=0))
        print(f"{gesture:<12}: std = {std:7.0f}")

    # Overall assessment
    avg_distance = np.mean(all_distances)
    min_distance = np.min(all_distances)
    avg_std = np.mean([np.mean(np.std(f, axis=0)) for f in features_by_gesture.values()])

    print("\n" + "=" * 70)
    print("SEPARABILITY SCORE")
    print("=" * 70)

    ratio = avg_distance / avg_std if avg_std > 0 else 0

    print(f"\nAvg distance between gestures: {avg_distance:.0f}")
    print(f"Min distance between gestures: {min_distance:.0f}")
    print(f"Avg within-gesture spread:     {avg_std:.0f}")
    print(f"\nSeparability ratio: {ratio:.2f}")
    print("  (higher is better, want > 2.0)")

    if ratio > 2.5:
        print("\n  ✓ GOOD: Gestures should be learnable")
        return "good"
    elif ratio > 1.5:
        print("\n  ⚠ MARGINAL: Gestures are somewhat distinguishable")
        print("    Collect more data to improve reliability")
        return "marginal"
    else:
        print("\n  ✗ POOR: Gestures are too similar or too noisy")
        print("    Problems:")
        print("    - Gestures may not be distinct enough")
        print("    - Electrode placement may be inconsistent")
        print("    - Not performing gestures consistently")
        return "poor"

def visualize_data(data_by_gesture, features_by_gesture):
    """Create visualizations"""
    print("\n" + "=" * 70)
    print("CREATING VISUALIZATIONS")
    print("=" * 70)

    gestures = sorted(data_by_gesture.keys())

    # Plot 1: Sample signals
    fig, axes = plt.subplots(len(gestures), 4, figsize=(16, 2*len(gestures)), sharex=True)

    for g_idx, gesture in enumerate(gestures):
        sample = data_by_gesture[gesture][0]  # First sample

        for ch in range(4):
            ax = axes[g_idx, ch]
            ax.plot(sample[:, ch], linewidth=0.7, color='steelblue')

            if g_idx == 0:
                ax.set_title(f"Channel {ch+1}", fontsize=10, fontweight='bold')

            if ch == 0:
                ax.set_ylabel(gesture, fontsize=9, fontweight='bold')

            ax.grid(True, alpha=0.3)
            ax.tick_params(labelsize=7)

    axes[-1, 0].set_xlabel("Time Sample", fontsize=8)
    plt.suptitle("Sample EMG Signals by Gesture", fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig("data_check_signals.png", dpi=120, bbox_inches='tight')
    print("  ✓ Saved: data_check_signals.png")

    # Plot 2: MAV feature distributions
    fig, axes = plt.subplots(1, 4, figsize=(16, 5))

    for ch in range(4):
        ax = axes[ch]

        positions = []
        labels = []

        for gesture in gestures:
            features = features_by_gesture[gesture][:, ch]
            positions.append(features)
            labels.append(gesture)

        bp = ax.boxplot(positions, labels=labels, patch_artist=True, showmeans=True)

        # Color boxes
        colors = plt.cm.Set3(np.linspace(0, 1, len(labels)))
        for patch, color in zip(bp['boxes'], colors):
            patch.set_facecolor(color)
            patch.set_alpha(0.7)

        ax.set_title(f"Channel {ch+1} MAV", fontsize=12, fontweight='bold')
        ax.set_ylabel("MAV Value", fontsize=10)
        ax.grid(True, alpha=0.3, axis='y')
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right', fontsize=9)

    plt.suptitle("MAV Feature Distributions - Are Gestures Distinguishable?",
                 fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig("data_check_features.png", dpi=120, bbox_inches='tight')
    print("  ✓ Saved: data_check_features.png")

    plt.close('all')

def main():
    import sys

    print("=" * 70)
    print("QUICK EMG DATA QUALITY CHECK")
    print("=" * 70)

    # Get session name from command line or use latest
    if len(sys.argv) > 1:
        session_name = sys.argv[1]
    else:
        # Find most recent session
        training_data_dir = "training_data"
        sessions = [d for d in os.listdir(training_data_dir)
                   if os.path.isdir(os.path.join(training_data_dir, d))]
        if not sessions:
            print("✗ No training data found!")
            return

        # Sort by modification time, most recent first
        sessions.sort(key=lambda s: os.path.getmtime(os.path.join(training_data_dir, s)), reverse=True)
        session_name = sessions[0]

    print(f"\nLoading session: {session_name}...")
    data = load_and_normalize(session_name, target_length=200)

    if not data:
        print("✗ No data found!")
        return

    total_samples = sum(len(samples) for samples in data.values())
    print(f"\nTotal: {total_samples} samples across {len(data)} gestures")

    print("\nExtracting MAV features...")
    features = extract_mav_features(data)

    quality = analyze_separability(features)
    visualize_data(data, features)

    print("\n" + "=" * 70)
    print("VERDICT")
    print("=" * 70)

    print(f"\nTotal samples: {total_samples}")
    print(f"Data quality: {quality.upper()}")

    if total_samples < 300:
        print(f"\n⚠ DATASET TOO SMALL")
        print(f"   Current: {total_samples} samples")
        print(f"   Minimum needed: 600 samples (100 per gesture)")
        print(f"   Recommended: 1800+ samples (300 per gesture)")
        print(f"   You need ~{max(0, 600-total_samples)} more samples")

    if quality == "good":
        print("\n✓ Data looks good! But still need much more data.")
        print("  The gestures ARE distinguishable.")
        print("  With 10x more data, you should get 80-90% accuracy.")
    elif quality == "marginal":
        print("\n⚠ Data is OK but not great.")
        print("  Collect more data and try to make gestures more distinct.")
    else:
        print("\n✗ Data quality issues detected!")
        print("  Before collecting more data:")
        print("  1. Check electrode placement")
        print("  2. Make sure gestures are VERY distinct")
        print("  3. Perform gestures consistently")

    print("\n" + "=" * 70)

if __name__ == "__main__":
    main()
