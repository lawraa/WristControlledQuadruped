# EMG Gesture Recognition Training Methods

This document explains the different training methods available for EMG gesture recognition and when to use each one.

## Available Training Scripts

### 1. **train_model.py** - Random Forest (Original/Default)
**Algorithm:** Random Forest Classifier
**Feature Extraction:** 5 time-domain features per channel
**Model File:** `models/gesture_model.pkl`

#### Features Extracted (per channel):
- **RMS** (Root Mean Square): Overall signal power
- **MAV** (Mean Absolute Value): Average magnitude
- **WL** (Waveform Length): Signal complexity
- **ZC** (Zero Crossings): Frequency content
- **VAR** (Variance): Signal variability

#### Characteristics:
- **Training Speed:** Fast
- **Inference Speed:** Very fast
- **Accuracy:** Good (typically 70-85%)
- **Data Requirements:** Moderate (works with 50+ samples per gesture)
- **Robustness:** Good resistance to overfitting

#### When to Use:
- Default choice for most applications
- When you have moderate amounts of training data
- When you need fast, reliable performance
- Good starting point for experimentation

---

### 2. **train_model_svm.py** - SVM with MAV (myo_ecn style)
**Algorithm:** Support Vector Machine (RBF kernel)
**Feature Extraction:** 3 simplified features per channel
**Model File:** `models/gesture_model_svm.pkl`

#### Features Extracted (per channel):
- **MAV** (Mean Absolute Value): Primary feature (smoothed absolute signal)
- **RMS** (Root Mean Square): Signal power
- **VAR** (Variance): Signal variability

#### Characteristics:
- **Training Speed:** Moderate (slower with grid search)
- **Inference Speed:** Fast
- **Accuracy:** Often best (typically 75-90%)
- **Data Requirements:** Works well with limited data
- **Robustness:** Excellent with proper hyperparameter tuning

#### Hyperparameter Tuning:
The script includes optional grid search for:
- **C**: Regularization parameter (0.1, 1, 10, 100)
- **gamma**: Kernel coefficient (scale, auto, 0.001, 0.01)
- **kernel**: Kernel type (rbf, linear)

#### When to Use:
- **Recommended for best accuracy**
- Based on proven myo_ecn repository approach
- When you have limited training data
- When you want automatic hyperparameter optimization
- When maximum classification accuracy is the priority

---

### 3. **train_model_lda.py** - Linear Discriminant Analysis
**Algorithm:** Linear Discriminant Analysis
**Feature Extraction:** 8 comprehensive time-domain features per channel
**Model File:** `models/gesture_model_lda.pkl`

#### Features Extracted (per channel):
- **MAV** (Mean Absolute Value)
- **RMS** (Root Mean Square)
- **WL** (Waveform Length)
- **ZC** (Zero Crossings)
- **SSC** (Slope Sign Changes): Additional frequency info
- **VAR** (Variance)
- **IEMG** (Integrated EMG): Total signal energy
- **WA** (Willison Amplitude): Signal transitions

#### Characteristics:
- **Training Speed:** Very fast
- **Inference Speed:** Extremely fast (fastest of all methods)
- **Accuracy:** Good (typically 65-80%)
- **Data Requirements:** Works with minimal data
- **Robustness:** Good, includes dimensionality reduction

#### Advantages:
- Automatic dimensionality reduction
- Linear decision boundaries (computationally efficient)
- No hyperparameters to tune
- Very fast real-time performance

#### When to Use:
- When you need the absolute fastest inference
- When training data is very limited
- When computational resources are constrained
- For embedded or real-time systems with strict latency requirements

---

### 4. **train_model_cnn.py** - Convolutional Neural Network
**Algorithm:** 1D CNN (Deep Learning)
**Feature Extraction:** None (learns from raw signals)
**Model Files:** `models/gesture_model_cnn.h5` + `models/gesture_model_cnn_metadata.pkl`

#### Architecture:
```
Input (200 samples × 4 channels)
    ↓
Conv1D (64 filters, kernel=5) → BatchNorm → MaxPool → Dropout
    ↓
Conv1D (128 filters, kernel=5) → BatchNorm → MaxPool → Dropout
    ↓
Conv1D (256 filters, kernel=3) → BatchNorm → MaxPool → Dropout
    ↓
Flatten → Dense(128) → BatchNorm → Dropout → Dense(64) → Dropout
    ↓
Output (Softmax)
```

#### Characteristics:
- **Training Speed:** Slow (requires GPU for practical use)
- **Inference Speed:** Moderate (slower than traditional ML)
- **Accuracy:** Can be highest (80-95% with sufficient data)
- **Data Requirements:** High (needs 200+ samples per gesture)
- **Robustness:** Prone to overfitting with small datasets

#### Requirements:
- TensorFlow: `pip install tensorflow`
- More training data than other methods
- Longer training time (uses early stopping)

#### When to Use:
- When you have lots of training data (200+ samples per gesture)
- When you want to maximize accuracy
- When you don't want to hand-craft features
- When you have GPU available for training
- **NOT recommended for limited data scenarios**

---

## Comparison Summary

| Method | Accuracy | Speed | Data Needed | Complexity | Best For |
|--------|----------|-------|-------------|------------|----------|
| **Random Forest** | ★★★☆☆ | ★★★★★ | Moderate | Low | General purpose, balanced |
| **SVM (myo_ecn)** | ★★★★★ | ★★★★☆ | Low-Moderate | Medium | **Best accuracy, recommended** |
| **LDA** | ★★★☆☆ | ★★★★★ | Low | Low | Speed-critical, embedded |
| **CNN** | ★★★★★ | ★★★☆☆ | High | High | Maximum accuracy with data |

## Recommendations

### For Most Users: **train_model_svm.py**
- Proven approach based on myo_ecn repository
- Best accuracy in most scenarios
- Includes automatic hyperparameter tuning
- Works well even with limited data

### For Limited Data: **train_model_lda.py**
- Fastest training and inference
- Works with minimal samples
- No tuning required

### For Maximum Accuracy: **train_model_cnn.py**
- Only if you have 200+ samples per gesture
- Requires TensorFlow installation
- Longer training time but can achieve best results

### Quick Prototyping: **train_model.py**
- Fast to train and test
- Good baseline performance
- No additional dependencies

---

## Usage Instructions

### Training a Model

1. **Collect training data first:**
   ```bash
   ./collect_data_auto.py
   ```

2. **Choose a training method and run:**
   ```bash
   # Option 1: SVM (recommended)
   ./train_model_svm.py

   # Option 2: LDA (fastest)
   ./train_model_lda.py

   # Option 3: Random Forest (default)
   ./train_model.py

   # Option 4: CNN (if you have lots of data + TensorFlow)
   ./train_model_cnn.py
   ```

3. **The script will:**
   - Show available training sessions
   - Let you select which sessions to use
   - Extract features and train the model
   - Show accuracy metrics and confusion matrix
   - Save the model to the `models/` directory

### Using a Model for Real-time Classification

```bash
./classify_realtime.py
```

The classification script will:
1. Show all available trained models
2. Display their method, sample count, and training date
3. Let you select which model to use
4. Run real-time gesture classification

---

## Feature Extraction Details

### Why Different Features?

**Simple Features (SVM):**
- MAV is the most discriminative single feature
- Less prone to overfitting
- More robust to noise
- Faster computation

**Complex Features (LDA):**
- More features → more information
- LDA reduces dimensionality automatically
- Captures different aspects of signal

**No Features (CNN):**
- Learns optimal features from data
- Can find patterns humans might miss
- Requires more data to learn effectively

---

## Troubleshooting

### Model Has Low Accuracy

1. **Collect more training data** - especially for under-represented gestures
2. **Try SVM with grid search** - often gives best results
3. **Check gesture consistency** - perform gestures the same way each time
4. **Verify sensor placement** - keep wristband in same position
5. **Try different methods** - some work better for certain gesture sets

### Model Doesn't Work in Real-time

1. **Check feature extraction** - must match training method
2. **Verify scaling** - SVM/LDA require the same scaler used in training
3. **Collect more varied data** - include different arm positions
4. **Reduce motion artifacts** - keep arm steady during gestures

### Grid Search Takes Too Long (SVM)

- Use default parameters by answering 'n' to grid search prompt
- Or reduce parameter grid in `train_model_svm.py`

---

## Technical Notes

### Feature Scaling
- **Random Forest:** No scaling required (tree-based)
- **SVM:** Requires scaling (included automatically)
- **LDA:** Requires scaling (included automatically)
- **CNN:** Normalizes raw signals per-sample

### Model Persistence
All models include metadata:
- Training date
- Number of samples
- Gesture list
- Method name
- Feature type

This ensures the classifier uses the correct feature extraction method automatically.

### Real-time Performance
Typical classification latency:
- **Random Forest:** ~1-2ms
- **SVM:** ~2-3ms
- **LDA:** ~1ms (fastest)
- **CNN:** ~5-10ms (depends on hardware)

All methods are fast enough for real-time control (>10Hz update rate).

---

## References

- **myo_ecn approach:** Based on https://github.com/smetanadvorak/myo_ecn
- **Time-domain features:** Standard EMG literature (Hudgins et al.)
- **CNN architecture:** Adapted from recent EMG gesture recognition papers

---

## Summary

**Start with `train_model_svm.py`** - it provides the best balance of accuracy, robustness, and ease of use. The myo_ecn approach has been proven in practice and consistently delivers excellent results.

If you need faster inference or have very limited data, try `train_model_lda.py`.

Only use `train_model_cnn.py` if you have substantial training data and want to invest time in deep learning optimization.
