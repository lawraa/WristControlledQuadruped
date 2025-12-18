#!/usr/bin/env python3
"""
Data Quality Checker for EMG Training Data
Analyzes collected gesture data to verify quality before extensive training
"""

import json
import os
import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict

def load_session_data(session_name):
    """Load all data from a session"""
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
                    samples.append(np.array(sample['data']))

            if samples:
                # Stack samples with explicit shape checking
                try:
                    data_by_gesture[gesture_name] = np.stack(samples)
                except ValueError as e:
                    # Handle variable-length samples
                    print(f"Warning: Variable-length samples in {gesture_name}, using list")
                    data_by_gesture[gesture_name] = samples

    return data_by_gesture

def analyze_signal_quality(data_by_gesture):
    """Check basic signal quality metrics"""
    print("=" * 70)
    print("SIGNAL QUALITY ANALYSIS")
    print("=" * 70)

    issues = []

    for gesture, samples in data_by_gesture.items():
        # Convert to numpy array if it's a list
        if isinstance(samples, list):
            samples = np.array([s for s in samples if len(s) > 0])

        print(f"\n{gesture.upper()}:")
        print(f"  Samples: {len(samples)}")
        print(f"  Shape: {samples.shape}")

        # Check for constant signals (dead channels)
        for ch in range(samples.shape[2]):
            ch_data = samples[:, :, ch]
            std_val = np.std(ch_data)
            if std_val < 1.0:  # Very low variation
                issue = f"  ⚠ WARNING: Channel {ch+1} has very low variation (std={std_val:.2f})"
                print(issue)
                issues.append(issue)

        # Check for all-zero samples
        zero_samples = np.sum(np.all(samples == 0, axis=(1,2)))
        if zero_samples > 0:
            issue = f"  ⚠ WARNING: {zero_samples} all-zero samples found"
            print(issue)
            issues.append(issue)

        # Signal statistics per channel
        print(f"  Channel statistics:")
        for ch in range(samples.shape[2]):
            ch_data = samples[:, :, ch].flatten()
            print(f"    Ch{ch+1}: mean={np.mean(ch_data):9.1f}, std={np.std(ch_data):9.1f}, "
                  f"min={np.min(ch_data):9.1f}, max={np.max(ch_data):9.1f}")

    return issues

def calculate_feature_separability(data_by_gesture):
    """Calculate MAV features and check if gestures are separable"""
    print("\n" + "=" * 70)
    print("FEATURE SEPARABILITY ANALYSIS")
    print("=" * 70)

    # Extract MAV features for each gesture
    features_by_gesture = {}

    for gesture, samples in data_by_gesture.items():
        # Convert to numpy array if it's a list
        if isinstance(samples, list):
            samples = np.array([s for s in samples if len(s) > 0])

        mav_features = []
        for sample in samples:
            # Calculate MAV for each channel
            mav = np.mean(np.abs(sample), axis=0)
            mav_features.append(mav)
        features_by_gesture[gesture] = np.array(mav_features)

    # Calculate mean MAV per gesture per channel
    print("\nMean MAV by gesture (per channel):")
    print("=" * 70)

    gesture_means = {}
    for gesture, features in features_by_gesture.items():
        mean_mav = np.mean(features, axis=0)
        gesture_means[gesture] = mean_mav
        print(f"\n{gesture:12s}: ", end="")
        for ch in range(len(mean_mav)):
            print(f"Ch{ch+1}={mean_mav[ch]:6.1f}  ", end="")

    # Calculate inter-gesture distances
    print("\n\n" + "=" * 70)
    print("INTER-GESTURE DISTANCES (Euclidean)")
    print("=" * 70)

    gestures = list(gesture_means.keys())
    print("\n" + " " * 15, end="")
    for g in gestures:
        print(f"{g[:10]:>12}", end="")
    print()

    distances = []
    for i, g1 in enumerate(gestures):
        print(f"{g1[:15]:15}", end="")
        for j, g2 in enumerate(gestures):
            if i == j:
                print(f"{'---':>12}", end="")
            else:
                dist = np.linalg.norm(gesture_means[g1] - gesture_means[g2])
                distances.append(dist)
                print(f"{dist:>12.1f}", end="")
        print()

    # Analyze separability
    print("\n" + "=" * 70)
    print("SEPARABILITY ASSESSMENT")
    print("=" * 70)

    avg_distance = np.mean(distances)
    min_distance = np.min(distances)
    max_distance = np.max(distances)

    print(f"\nAverage inter-gesture distance: {avg_distance:.1f}")
    print(f"Minimum inter-gesture distance: {min_distance:.1f}")
    print(f"Maximum inter-gesture distance: {max_distance:.1f}")

    # Calculate within-gesture variance
    print("\nWithin-gesture variance (spread):")
    for gesture, features in features_by_gesture.items():
        variance = np.mean(np.var(features, axis=0))
        print(f"  {gesture:12s}: {variance:7.1f}")

    # Assessment
    print("\n" + "=" * 70)
    avg_within_variance = np.mean([np.mean(np.var(f, axis=0)) for f in features_by_gesture.values()])

    ratio = avg_distance / np.sqrt(avg_within_variance)
    print(f"Separability ratio: {ratio:.2f}")
    print("  (distance between gestures / within-gesture spread)")

    if ratio > 3.0:
        print("  ✓ GOOD: Gestures are well-separated")
    elif ratio > 1.5:
        print("  ⚠ MARGINAL: Gestures are somewhat distinguishable")
    else:
        print("  ✗ POOR: Gestures are too similar or data is too noisy")

    return features_by_gesture

def visualize_sample_signals(data_by_gesture, num_samples=3):
    """Visualize sample signals from each gesture"""
    print("\n" + "=" * 70)
    print("GENERATING VISUALIZATIONS")
    print("=" * 70)

    gestures = list(data_by_gesture.keys())
    num_gestures = len(gestures)

    # Convert first gesture to array to get num_channels
    first_samples = data_by_gesture[gestures[0]]
    if isinstance(first_samples, list):
        first_samples = np.array([s for s in first_samples if len(s) > 0])
    num_channels = first_samples.shape[2]

    # Plot 1: Sample signals from each gesture
    fig, axes = plt.subplots(num_gestures, num_channels,
                            figsize=(15, 2.5*num_gestures), sharex=True)

    if num_channels == 1:
        axes = axes.reshape(-1, 1)

    for g_idx, gesture in enumerate(gestures):
        samples = data_by_gesture[gesture]
        # Convert to numpy array if it's a list
        if isinstance(samples, list):
            samples = np.array([s for s in samples if len(s) > 0])
        # Take first sample (or random if you prefer)
        sample = samples[0]

        for ch in range(num_channels):
            ax = axes[g_idx, ch]
            ax.plot(sample[:, ch], linewidth=0.5)
            ax.set_ylabel(f"{gesture}\nCh{ch+1}", fontsize=8)
            ax.grid(True, alpha=0.3)

            if g_idx == 0:
                ax.set_title(f"Channel {ch+1}", fontsize=10)
            if g_idx == num_gestures - 1:
                ax.set_xlabel("Sample", fontsize=8)

    plt.suptitle("Sample EMG Signals by Gesture", fontsize=12, fontweight='bold')
    plt.tight_layout()
    plt.savefig("data_quality_signals.png", dpi=150, bbox_inches='tight')
    print("  ✓ Saved: data_quality_signals.png")

    # Plot 2: MAV features comparison
    features_by_gesture = {}
    for gesture, samples in data_by_gesture.items():
        # Convert to numpy array if it's a list
        if isinstance(samples, list):
            samples = np.array([s for s in samples if len(s) > 0])
        mav_features = []
        for sample in samples:
            mav = np.mean(np.abs(sample), axis=0)
            mav_features.append(mav)
        features_by_gesture[gesture] = np.array(mav_features)

    fig, axes = plt.subplots(1, num_channels, figsize=(15, 5))
    if num_channels == 1:
        axes = [axes]

    for ch in range(num_channels):
        ax = axes[ch]
        positions = []
        labels = []

        for idx, (gesture, features) in enumerate(features_by_gesture.items()):
            ch_features = features[:, ch]
            positions.append(ch_features)
            labels.append(gesture)

        bp = ax.boxplot(positions, labels=labels, patch_artist=True)

        # Color the boxes
        colors = plt.cm.Set3(np.linspace(0, 1, len(labels)))
        for patch, color in zip(bp['boxes'], colors):
            patch.set_facecolor(color)

        ax.set_title(f"Channel {ch+1} MAV Distribution", fontsize=12, fontweight='bold')
        ax.set_ylabel("MAV Value", fontsize=10)
        ax.set_xlabel("Gesture", fontsize=10)
        ax.grid(True, alpha=0.3, axis='y')
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')

    plt.suptitle("MAV Feature Distributions by Gesture", fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig("data_quality_features.png", dpi=150, bbox_inches='tight')
    print("  ✓ Saved: data_quality_features.png")

    plt.close('all')

def main():
    print("=" * 70)
    print("EMG DATA QUALITY CHECKER")
    print("=" * 70)

    # List available sessions
    training_data_dir = "training_data"
    available_sessions = [d for d in os.listdir(training_data_dir)
                         if os.path.isdir(os.path.join(training_data_dir, d))]

    print("\nAvailable sessions:")
    for i, session in enumerate(sorted(available_sessions), 1):
        session_info_file = os.path.join(training_data_dir, session, "session_info.json")
        if os.path.exists(session_info_file):
            with open(session_info_file, 'r') as f:
                info = json.load(f)
                print(f"  [{i}] {session} - {info['total_samples']} samples")
        else:
            print(f"  [{i}] {session}")

    print()
    choice = input("Select session to analyze (number or name): ").strip()

    if choice.isdigit():
        idx = int(choice) - 1
        selected_session = sorted(available_sessions)[idx]
    else:
        selected_session = choice

    print(f"\nAnalyzing session: {selected_session}")
    print("=" * 70)

    # Load data
    data_by_gesture = load_session_data(selected_session)

    if not data_by_gesture:
        print("✗ No data found in session!")
        return

    print(f"\nLoaded {len(data_by_gesture)} gestures:")
    for gesture, samples in data_by_gesture.items():
        if isinstance(samples, list):
            # Check shapes of samples in list
            shapes = [np.array(s).shape for s in samples[:5]]
            print(f"  {gesture}: {len(samples)} samples, example shapes: {shapes}")
            # Convert to numpy array
            data_by_gesture[gesture] = np.array([s for s in samples if len(s) > 0])
        else:
            print(f"  {gesture}: {len(samples)} samples, shape {samples.shape}")

    # Run analyses
    issues = analyze_signal_quality(data_by_gesture)
    features = calculate_feature_separability(data_by_gesture)
    visualize_sample_signals(data_by_gesture)

    # Final summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    total_samples = sum(len(samples) for samples in data_by_gesture.values())
    print(f"\nTotal samples: {total_samples}")
    print(f"Gestures: {len(data_by_gesture)}")
    print(f"Samples per gesture: {total_samples // len(data_by_gesture)}")

    if issues:
        print(f"\n⚠ Found {len(issues)} potential issues:")
        for issue in issues[:5]:  # Show first 5
            print(issue)
    else:
        print("\n✓ No major signal quality issues detected")

    print("\n" + "=" * 70)
    print("RECOMMENDATIONS")
    print("=" * 70)

    if total_samples < 300:
        print("\n✗ CRITICAL: Dataset too small")
        print(f"  Current: {total_samples} samples")
        print(f"  Minimum recommended: 600 samples (100 per gesture)")
        print(f"  Target for good results: 1800+ samples (300 per gesture)")
        print(f"  You need to collect ~{max(0, 600-total_samples)} more samples")

    if issues:
        print("\n⚠ Signal quality issues detected")
        print("  - Check electrode placement")
        print("  - Ensure good skin contact")
        print("  - Verify wristband is properly positioned")

    print("\n✓ Analysis complete!")
    print("  Check generated images: data_quality_signals.png, data_quality_features.png")

if __name__ == "__main__":
    main()
