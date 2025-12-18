#!/usr/bin/env python3
"""
EMG Gesture Model Trainer - CNN for Raw Signal Processing
Convolutional Neural Network learns features directly from raw EMG signals
Can capture complex temporal patterns that manual feature extraction might miss
"""

import json
import os
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, confusion_matrix
import joblib
from datetime import datetime

# Check if TensorFlow is available
try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras import layers, models
    from tensorflow.keras.utils import to_categorical
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False
    print("Warning: TensorFlow not installed. Install with: pip install tensorflow")

class CNNGestureTrainer:
    def __init__(self, sessions=None):
        if not TENSORFLOW_AVAILABLE:
            raise ImportError("TensorFlow is required for CNN training. Install with: pip install tensorflow")

        self.sessions = sessions if sessions else []
        self.model = None
        self.label_encoder = LabelEncoder()
        self.X = None
        self.y = None

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

        # Prepare data for CNN (no feature extraction - use raw signals)
        print("\nPreparing raw signal data for CNN...")
        self.X = np.array(all_samples)  # Shape: (n_samples, window_size, n_channels)

        # Normalize the signals
        print("Normalizing signals...")
        # Normalize each sample independently
        for i in range(len(self.X)):
            for ch in range(self.X.shape[2]):
                channel_data = self.X[i, :, ch]
                if np.std(channel_data) > 0:
                    self.X[i, :, ch] = (channel_data - np.mean(channel_data)) / np.std(channel_data)

        # Encode labels
        self.y = self.label_encoder.fit_transform(all_labels)

        print(f"\nData shape: {self.X.shape}")
        print(f"Labels shape: {self.y.shape}")
        print(f"Number of classes: {len(np.unique(self.y))}")

        # Show class distribution
        print("\nClass distribution:")
        for idx, label in enumerate(self.label_encoder.classes_):
            count = np.sum(self.y == idx)
            print(f"  {label:15} - {count:3d} samples ({100*count/len(self.y):.1f}%)")

    def build_cnn_model(self, input_shape, num_classes):
        """
        Build a 1D CNN for EMG signal classification

        Architecture:
        - Conv1D layers to extract temporal features
        - MaxPooling to reduce dimensionality
        - Dropout for regularization
        - Dense layers for classification
        """
        model = models.Sequential([
            # First convolutional block
            layers.Conv1D(64, kernel_size=5, activation='relu', input_shape=input_shape),
            layers.BatchNormalization(),
            layers.MaxPooling1D(pool_size=2),
            layers.Dropout(0.3),

            # Second convolutional block
            layers.Conv1D(128, kernel_size=5, activation='relu'),
            layers.BatchNormalization(),
            layers.MaxPooling1D(pool_size=2),
            layers.Dropout(0.3),

            # Third convolutional block
            layers.Conv1D(256, kernel_size=3, activation='relu'),
            layers.BatchNormalization(),
            layers.MaxPooling1D(pool_size=2),
            layers.Dropout(0.4),

            # Flatten and fully connected layers
            layers.Flatten(),
            layers.Dense(128, activation='relu'),
            layers.BatchNormalization(),
            layers.Dropout(0.5),
            layers.Dense(64, activation='relu'),
            layers.Dropout(0.3),

            # Output layer
            layers.Dense(num_classes, activation='softmax')
        ])

        return model

    def train(self, epochs=50, batch_size=32):
        """Train CNN classifier"""
        print("\n" + "=" * 70)
        print("Training CNN Classifier")
        print("=" * 70)

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            self.X, self.y, test_size=0.2, random_state=42, stratify=self.y
        )

        # Convert labels to categorical
        num_classes = len(np.unique(self.y))
        y_train_cat = to_categorical(y_train, num_classes)
        y_test_cat = to_categorical(y_test, num_classes)

        print(f"\nTraining set: {len(X_train)} samples")
        print(f"Test set: {len(X_test)} samples")
        print(f"Input shape: {X_train.shape[1:]}")
        print(f"Number of classes: {num_classes}")

        # Build model
        print("\nBuilding CNN architecture...")
        self.model = self.build_cnn_model(
            input_shape=(X_train.shape[1], X_train.shape[2]),
            num_classes=num_classes
        )

        # Compile model
        self.model.compile(
            optimizer='adam',
            loss='categorical_crossentropy',
            metrics=['accuracy']
        )

        print("\nModel Summary:")
        self.model.summary()

        # Callbacks
        early_stop = keras.callbacks.EarlyStopping(
            monitor='val_loss',
            patience=10,
            restore_best_weights=True
        )

        reduce_lr = keras.callbacks.ReduceLROnPlateau(
            monitor='val_loss',
            factor=0.5,
            patience=5,
            min_lr=1e-6
        )

        # Train
        print("\nTraining model...")
        history = self.model.fit(
            X_train, y_train_cat,
            validation_data=(X_test, y_test_cat),
            epochs=epochs,
            batch_size=batch_size,
            callbacks=[early_stop, reduce_lr],
            verbose=1
        )

        print("\n✓ Training complete!")

        # Evaluate
        print("\n" + "=" * 70)
        print("Evaluation Results")
        print("=" * 70)

        train_loss, train_acc = self.model.evaluate(X_train, y_train_cat, verbose=0)
        test_loss, test_acc = self.model.evaluate(X_test, y_test_cat, verbose=0)

        print(f"\nTraining accuracy: {train_acc:.3f}")
        print(f"Test accuracy: {test_acc:.3f}")
        print(f"Test loss: {test_loss:.3f}")

        # Classification report
        y_pred = np.argmax(self.model.predict(X_test, verbose=0), axis=1)
        print("\nClassification Report:")
        print(classification_report(
            y_test,
            y_pred,
            target_names=self.label_encoder.classes_
        ))

        # Confusion matrix
        print("Confusion Matrix:")
        cm = confusion_matrix(y_test, y_pred)
        labels = self.label_encoder.classes_

        print("\n" + " " * 15, end="")
        for label in labels:
            print(f"{label[:10]:>10}", end="")
        print()

        for i, label in enumerate(labels):
            print(f"{label[:15]:15}", end="")
            for j in range(len(labels)):
                print(f"{cm[i][j]:10d}", end="")
            print()

        return history

    def save_model(self, output_path="models/gesture_model_cnn.h5"):
        """Save trained CNN model"""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Save Keras model
        self.model.save(output_path)

        # Save metadata separately
        metadata_path = output_path.replace('.h5', '_metadata.pkl')
        metadata = {
            'label_encoder': self.label_encoder,
            'gestures': list(self.label_encoder.classes_),
            'training_date': datetime.now().isoformat(),
            'n_samples': len(self.y),
            'method': 'CNN with raw signal processing',
            'input_shape': self.X.shape[1:],
            'feature_type': 'raw'
        }

        joblib.dump(metadata, metadata_path)

        print(f"\n✓ Model saved to {output_path}")
        print(f"✓ Metadata saved to {metadata_path}")
        print(f"  Method: Convolutional Neural Network")
        print(f"  Input: Raw EMG signals (no manual feature extraction)")

    def run(self, epochs=50, batch_size=32):
        """Run complete training pipeline"""
        print("=" * 70)
        print("EMG Gesture Recognition - CNN Training")
        print("=" * 70)
        print()

        try:
            self.load_data()
            self.train(epochs=epochs, batch_size=batch_size)
            self.save_model()

            print("\n" + "=" * 70)
            print("✓ Training Complete!")
            print("=" * 70)
            print("\nCNN advantages:")
            print("  - Learns features automatically from raw signals")
            print("  - Can capture complex temporal patterns")
            print("  - No manual feature engineering required")
            print("  - Often achieves higher accuracy with sufficient data")
            print("\nNote: CNN models are larger and slower than traditional ML models")
            print("Use this model for real-time classification (requires separate script)")

        except Exception as e:
            print(f"\n✗ Error: {e}")
            import traceback
            traceback.print_exc()

def main():
    if not TENSORFLOW_AVAILABLE:
        print("Error: TensorFlow not installed!")
        print("Install with: pip install tensorflow")
        return

    print("=" * 70)
    print("EMG Gesture Recognition - CNN Training")
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

    # Training parameters
    epochs_input = input("Number of epochs (default=50): ").strip()
    epochs = int(epochs_input) if epochs_input.isdigit() else 50

    batch_input = input("Batch size (default=32): ").strip()
    batch_size = int(batch_input) if batch_input.isdigit() else 32

    print()
    input("Press Enter to begin training...")

    trainer = CNNGestureTrainer(sessions=selected_sessions)
    trainer.run(epochs=epochs, batch_size=batch_size)

if __name__ == "__main__":
    main()
