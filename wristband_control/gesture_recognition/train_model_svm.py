#!/usr/bin/env python3
"""
EMG Gesture Model Trainer - SVM with MAV Features
Based on myo_ecn approach: simplified feature extraction using Mean Absolute Value
Uses Support Vector Machine classifier for gesture recognition
"""

import json
import os
import numpy as np
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.metrics import classification_report, confusion_matrix
import joblib
from datetime import datetime

class SVMGestureTrainer:
    def __init__(self, sessions=None):
        self.sessions = sessions if sessions else []
        self.model = None
        self.scaler = StandardScaler()
        self.gesture_labels = []
        self.X = None
        self.y = None

    def extract_features_mav(self, window_data):
        """
        Extract Mean Absolute Value (MAV) features - myo_ecn style
        Simpler and often more robust than complex features

        Features per channel:
        - MAV: Mean Absolute Value (smoothed absolute signal)
        - Optionally add variance for more discriminability
        """
        features = []
        num_channels = window_data.shape[1]

        for ch in range(num_channels):
            channel_data = window_data[:, ch]

            # Mean Absolute Value (primary feature in myo_ecn)
            mav = np.mean(np.abs(channel_data))

            # Root Mean Square (related to signal power)
            rms = np.sqrt(np.mean(channel_data**2))

            # Variance (captures signal variability)
            var = np.var(channel_data)

            features.extend([mav, rms, var])

        return np.array(features)

    def load_data(self):
        """Load all collected gesture data from selected sessions"""
        print("Loading data...")
        print(f"Sessions: {', '.join(self.sessions)}")
        print()

        all_samples = []
        all_labels = []

        for session in self.sessions:
            session_dir = os.path.join("training_data", session)

            if not os.path.exists(session_dir):
                print(f"  Warning: Session '{session}' not found, skipping...")
                continue

            print(f"  Session: {session}")

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

        # Extract MAV features
        print("\nExtracting MAV features...")
        X = []
        for i, window in enumerate(all_samples):
            features = self.extract_features_mav(window)
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

    def train(self, grid_search=True):
        """Train SVM classifier with optional hyperparameter tuning"""
        print("\n" + "=" * 70)
        print("Training SVM Classifier (myo_ecn style)")
        print("=" * 70)

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            self.X, self.y, test_size=0.2, random_state=42, stratify=self.y
        )

        print(f"\nTraining set: {len(X_train)} samples")
        print(f"Test set: {len(X_test)} samples")

        # Scale features (important for SVM)
        print("\nScaling features...")
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        if grid_search:
            # Grid search for best hyperparameters
            print("\nPerforming grid search for optimal hyperparameters...")
            param_grid = {
                'C': [0.1, 1, 10, 100],
                'gamma': ['scale', 'auto', 0.001, 0.01],
                'kernel': ['rbf', 'linear']
            }

            grid = GridSearchCV(
                SVC(random_state=42, probability=True),
                param_grid,
                cv=3,
                scoring='accuracy',
                n_jobs=-1,
                verbose=1
            )

            grid.fit(X_train_scaled, y_train)

            print(f"\nBest parameters: {grid.best_params_}")
            print(f"Best CV score: {grid.best_score_:.3f}")

            self.model = grid.best_estimator_
        else:
            # Use default RBF kernel SVM
            print("\nTraining SVM with default parameters...")
            self.model = SVC(
                kernel='rbf',
                C=10,
                gamma='scale',
                random_state=42,
                probability=True
            )
            self.model.fit(X_train_scaled, y_train)

        print("✓ Training complete!")

        # Evaluate on test set
        print("\n" + "=" * 70)
        print("Evaluation Results")
        print("=" * 70)

        train_score = self.model.score(X_train_scaled, y_train)
        test_score = self.model.score(X_test_scaled, y_test)

        print(f"\nTraining accuracy: {train_score:.3f}")
        print(f"Test accuracy: {test_score:.3f}")

        # Cross-validation
        print("\nPerforming 5-fold cross-validation...")
        X_scaled = self.scaler.transform(self.X)
        cv_scores = cross_val_score(self.model, X_scaled, self.y, cv=5)
        print(f"CV scores: {cv_scores}")
        print(f"CV mean: {cv_scores.mean():.3f} (+/- {cv_scores.std():.3f})")

        # Classification report
        y_pred = self.model.predict(X_test_scaled)
        print("\nClassification Report:")
        print(classification_report(y_test, y_pred))

        # Confusion matrix
        print("Confusion Matrix:")
        cm = confusion_matrix(y_test, y_pred)
        labels = sorted(set(self.y))

        print("\n" + " " * 15, end="")
        for label in labels:
            print(f"{label[:10]:>10}", end="")
        print()

        for i, label in enumerate(labels):
            print(f"{label[:15]:15}", end="")
            for j in range(len(labels)):
                print(f"{cm[i][j]:10d}", end="")
            print()

    def save_model(self, output_path="models/gesture_model_svm.pkl"):
        """Save trained SVM model"""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'feature_names': [
                f"Ch{ch+1}_{feat}"
                for ch in range(4)
                for feat in ['MAV', 'RMS', 'VAR']
            ],
            'gestures': sorted(set(self.y)),
            'training_date': datetime.now().isoformat(),
            'n_samples': len(self.y),
            'method': 'SVM with MAV features (myo_ecn style)',
            'feature_type': 'MAV'
        }

        joblib.dump(model_data, output_path)
        print(f"\n✓ Model saved to {output_path}")
        print(f"  Method: SVM with MAV features")
        print(f"  Feature extraction: Mean Absolute Value (myo_ecn approach)")

    def run(self, grid_search=True):
        """Run complete training pipeline"""
        print("=" * 70)
        print("EMG Gesture Recognition - SVM Training (myo_ecn approach)")
        print("=" * 70)
        print()

        try:
            self.load_data()
            self.train(grid_search=grid_search)
            self.save_model()

            print("\n" + "=" * 70)
            print("✓ Training Complete!")
            print("=" * 70)
            print("\nThis model uses the myo_ecn approach:")
            print("  - Simplified MAV (Mean Absolute Value) features")
            print("  - SVM classifier with RBF kernel")
            print("  - Feature scaling for optimal performance")
            print("\nUse this model for real-time classification with classify_realtime.py")

        except Exception as e:
            print(f"\n✗ Error: {e}")
            import traceback
            traceback.print_exc()

def main():
    print("=" * 70)
    print("EMG Gesture Recognition - SVM Training (myo_ecn style)")
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

    # Ask about grid search
    grid_search_choice = input("Perform grid search for optimal hyperparameters? (y/n, default=y): ").strip().lower()
    grid_search = grid_search_choice != 'n'

    print()
    input("Press Enter to begin training...")

    trainer = SVMGestureTrainer(sessions=selected_sessions)
    trainer.run(grid_search=grid_search)

if __name__ == "__main__":
    main()
