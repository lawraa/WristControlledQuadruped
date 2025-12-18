#!/usr/bin/env python3
"""
EMG Gesture Model Trainer
Extracts features from collected data and trains a gesture recognition model
"""

import json
import os
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, confusion_matrix
import joblib
from datetime import datetime

class GestureModelTrainer:
    def __init__(self, sessions=None):
        self.sessions = sessions if sessions else []
        self.model = None
        self.gesture_labels = []
        self.X = None
        self.y = None

    def extract_features(self, window_data):
        """
        Extract time-domain features from EMG window
        Features per channel:
        - RMS (Root Mean Square)
        - MAV (Mean Absolute Value)
        - WL (Waveform Length)
        - ZC (Zero Crossings)
        """
        features = []

        # window_data shape: (window_size, 4 channels)
        num_channels = window_data.shape[1]

        for ch in range(num_channels):
            channel_data = window_data[:, ch]

            # RMS
            rms = np.sqrt(np.mean(channel_data**2))

            # MAV
            mav = np.mean(np.abs(channel_data))

            # Waveform Length
            wl = np.sum(np.abs(np.diff(channel_data)))

            # Zero Crossings (with threshold to reduce noise)
            threshold = 0.01 * np.max(np.abs(channel_data))
            zc = np.sum(np.diff(np.sign(channel_data)) != 0)

            # Variance
            var = np.var(channel_data)

            features.extend([rms, mav, wl, zc, var])

        return np.array(features)

    def load_data(self):
        """Load all collected gesture data from selected sessions"""
        print("Loading data...")
        print(f"Sessions: {', '.join(self.sessions)}")
        print()

        all_samples = []
        all_labels = []

        # Load data from each session
        for session in self.sessions:
            session_dir = os.path.join("training_data", session)

            if not os.path.exists(session_dir):
                print(f"  Warning: Session '{session}' not found, skipping...")
                continue

            print(f"  Session: {session}")

            # Load all .jsonl files in session directory
            for filename in os.listdir(session_dir):
                if filename.endswith('.jsonl'):
                    filepath = os.path.join(session_dir, filename)
                    gesture_name = filename.replace('.jsonl', '')

                    with open(filepath, 'r') as f:
                        count = 0
                        for line in f:
                            sample = json.loads(line)
                            all_samples.append(np.array(sample['data']))
                            all_labels.append(sample['gesture'])
                            count += 1

                    if count > 0:
                        print(f"    {gesture_name}: {count} samples")

        if not all_samples:
            raise ValueError("No data found! Run collect_data_auto.py or collect_data.py first.")

        print(f"\nTotal samples loaded: {len(all_samples)}")

        # Extract features from all samples
        print("\nExtracting features...")
        X = []
        for i, window in enumerate(all_samples):
            features = self.extract_features(window)
            X.append(features)

            if (i + 1) % 50 == 0:
                print(f"  Processed {i + 1}/{len(all_samples)} samples")

        self.X = np.array(X)
        self.y = np.array(all_labels)

        print(f"\nFeature matrix shape: {self.X.shape}")
        print(f"Labels shape: {self.y.shape}")

        # Show class distribution
        print("\nClass distribution:")
        unique, counts = np.unique(self.y, return_counts=True)
        for label, count in zip(unique, counts):
            print(f"  {label:15} - {count:3d} samples ({100*count/len(self.y):.1f}%)")

    def train(self):
        """Train Random Forest classifier"""
        print("\n" + "=" * 70)
        print("Training Random Forest Classifier")
        print("=" * 70)

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            self.X, self.y, test_size=0.2, random_state=42, stratify=self.y
        )

        print(f"\nTraining set: {len(X_train)} samples")
        print(f"Test set: {len(X_test)} samples")

        # Train Random Forest
        print("\nTraining model...")
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1
        )

        self.model.fit(X_train, y_train)
        print("✓ Training complete!")

        # Evaluate on test set
        print("\n" + "=" * 70)
        print("Evaluation Results")
        print("=" * 70)

        train_score = self.model.score(X_train, y_train)
        test_score = self.model.score(X_test, y_test)

        print(f"\nTraining accuracy: {train_score:.3f}")
        print(f"Test accuracy: {test_score:.3f}")

        # Cross-validation
        print("\nPerforming 5-fold cross-validation...")
        cv_scores = cross_val_score(self.model, self.X, self.y, cv=5)
        print(f"CV scores: {cv_scores}")
        print(f"CV mean: {cv_scores.mean():.3f} (+/- {cv_scores.std():.3f})")

        # Classification report
        y_pred = self.model.predict(X_test)
        print("\nClassification Report:")
        print(classification_report(y_test, y_pred))

        # Confusion matrix
        print("Confusion Matrix:")
        cm = confusion_matrix(y_test, y_pred)
        labels = sorted(set(self.y))

        # Print header
        print("\n" + " " * 15, end="")
        for label in labels:
            print(f"{label[:10]:>10}", end="")
        print()

        # Print matrix
        for i, label in enumerate(labels):
            print(f"{label[:15]:15}", end="")
            for j in range(len(labels)):
                print(f"{cm[i][j]:10d}", end="")
            print()

        # Feature importance
        print("\n" + "=" * 70)
        print("Feature Importance (Top 10)")
        print("=" * 70)

        feature_names = []
        for ch in range(4):
            for feat in ['RMS', 'MAV', 'WL', 'ZC', 'VAR']:
                feature_names.append(f"Ch{ch+1}_{feat}")

        importances = self.model.feature_importances_
        indices = np.argsort(importances)[::-1][:10]

        for i, idx in enumerate(indices):
            print(f"{i+1:2d}. {feature_names[idx]:15} - {importances[idx]:.4f}")

    def save_model(self, output_path="models/gesture_model.pkl"):
        """Save trained model"""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        model_data = {
            'model': self.model,
            'feature_names': [
                f"Ch{ch+1}_{feat}"
                for ch in range(4)
                for feat in ['RMS', 'MAV', 'WL', 'ZC', 'VAR']
            ],
            'gestures': sorted(set(self.y)),
            'training_date': datetime.now().isoformat(),
            'n_samples': len(self.y)
        }

        joblib.dump(model_data, output_path)
        print(f"\n✓ Model saved to {output_path}")

    def run(self):
        """Run complete training pipeline"""
        print("=" * 70)
        print("EMG Gesture Recognition - Model Training")
        print("=" * 70)
        print()

        try:
            self.load_data()
            self.train()
            self.save_model()

            print("\n" + "=" * 70)
            print("✓ Training Complete!")
            print("=" * 70)
            print("\nYou can now use the trained model for real-time classification.")
            print("Run: ./classify_realtime.py")

        except Exception as e:
            print(f"\n✗ Error: {e}")
            import traceback
            traceback.print_exc()

def main():
    print("=" * 70)
    print("EMG Gesture Recognition - Model Training")
    print("=" * 70)
    print()

    # List available sessions
    training_data_dir = "training_data"
    if not os.path.exists(training_data_dir):
        print("Error: No training data directory found!")
        print("Run collect_data_auto.py or collect_data.py first.")
        return

    available_sessions = [d for d in os.listdir(training_data_dir)
                         if os.path.isdir(os.path.join(training_data_dir, d))]

    if not available_sessions:
        print("Error: No sessions found!")
        print("Run collect_data_auto.py or collect_data.py first.")
        return

    print("Available sessions:")
    print()

    session_info_list = []
    for i, session in enumerate(sorted(available_sessions), 1):
        session_info_file = os.path.join(training_data_dir, session, "session_info.json")
        if os.path.exists(session_info_file):
            with open(session_info_file, 'r') as f:
                info = json.load(f)
                print(f"  [{i}] {session}")
                print(f"      Samples: {info['total_samples']} | Date: {info['collection_date'][:10]}")
                session_info_list.append((session, info))
        else:
            print(f"  [{i}] {session} (no info available)")
            session_info_list.append((session, None))
        print()

    print(f"  [a] All sessions ({len(available_sessions)} total)")
    print()
    print("=" * 70)
    print()

    # Get user selection
    choice = input("Select session(s) to train on (number, 'a' for all, or comma-separated): ").strip().lower()

    selected_sessions = []

    if choice == 'a':
        selected_sessions = [s[0] for s in session_info_list]
    elif ',' in choice:
        # Multiple selections
        indices = [int(x.strip()) - 1 for x in choice.split(',') if x.strip().isdigit()]
        selected_sessions = [session_info_list[i][0] for i in indices if 0 <= i < len(session_info_list)]
    elif choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(session_info_list):
            selected_sessions = [session_info_list[idx][0]]

    if not selected_sessions:
        print("Error: Invalid selection!")
        return

    print()
    print(f"Training on {len(selected_sessions)} session(s): {', '.join(selected_sessions)}")
    print()
    input("Press Enter to begin training...")

    trainer = GestureModelTrainer(sessions=selected_sessions)
    trainer.run()

if __name__ == "__main__":
    main()
