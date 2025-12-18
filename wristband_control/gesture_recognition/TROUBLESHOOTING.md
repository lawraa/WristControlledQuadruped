# EMG Model Training Troubleshooting Guide

## Problem: Low Accuracy (32%) with 109 Samples

### Root Causes
1. **Dataset too small**: 109 samples split into 6 classes = only ~14-17 samples per class for training
2. **Test set unreliable**: Only 3-4 samples per class makes evaluation metrics unreliable
3. **EMG signal complexity**: EMG data is noisy and requires significantly more samples than other sensor data

### Solutions (in order of priority)

#### 1. Collect More Data (CRITICAL)
**Minimum recommended samples per gesture: 100-200**
**Target for good performance: 300-500 per gesture**

```bash
# Use collect_data_auto.py with longer session presets
python collect_data_auto.py
# Select "30-Minute Comprehensive Session" or longer
```

#### 2. Combine Multiple Sessions
Train on ALL available sessions to increase dataset size:

When running train_model_svm.py, select option 'a' (all sessions)

Current available sessions:
- Jay10_v1: 109 samples
- jay_01_v1: 12 samples
- test01: 12 samples
- 20251218_020132: 6 samples
- **Total if combined: ~139 samples** (still too small, but better)

#### 3. Data Collection Best Practices

**For better quality data:**
- Perform each gesture consistently
- Rest between gestures to avoid muscle fatigue
- Keep electrode placement constant within a session
- Collect data in multiple sessions over different days
- Ensure good electrode contact (clean skin, proper placement)

**Session structure:**
- Take 30-second breaks every 5 minutes
- Vary gesture intensity slightly (don't be too robotic)
- Record at different times of day if possible

#### 4. Short-term Improvements (for current small dataset)

If you must work with limited data, try these:

**a) Data Augmentation (add to training code)**
```python
# Add noise augmentation
def augment_sample(sample, noise_level=0.05):
    noise = np.random.normal(0, noise_level, sample.shape)
    return sample + noise

# In load_data(), create augmented copies
for sample in all_samples:
    all_samples.append(augment_sample(sample))
```

**b) Simpler Models**
- Try LDA (Linear Discriminant Analysis) - works better with small datasets
- Already available in train_model_lda.py

**c) Reduce Number of Gestures**
Start with 3-4 most distinct gestures instead of 6:
- forward, backward, stop, jump (skip left/right for now)

**d) Cross-validation instead of fixed split**
The training code already does 5-fold CV - pay more attention to CV scores than test scores

#### 5. Expected Performance by Dataset Size

| Total Samples | Samples/Class | Expected Accuracy |
|---------------|---------------|-------------------|
| 100-150       | 15-25         | 30-50% (unreliable) |
| 300-600       | 50-100        | 60-75% (marginal)   |
| 900-1500      | 150-250       | 75-85% (good)       |
| 1800+         | 300+          | 85-95% (excellent)  |

**Current status: 109 samples = unreliable results expected**

### Diagnostic Checklist

- [ ] Collected at least 100 samples per gesture
- [ ] Electrode placement is consistent
- [ ] Gestures are performed distinctly (not similar movements)
- [ ] EMG signal quality is good (check with emg_visualizer.py)
- [ ] Training accuracy is reasonable (>80%)
- [ ] Cross-validation scores are consistent (low std deviation)

### Next Steps

1. **Immediate**: Collect more data using 30-minute sessions
2. **Short-term**: Combine all existing sessions for training
3. **Long-term**: Collect 300+ samples per gesture across multiple sessions
4. **Monitor**: Use CV scores to track if you're overfitting

### When to Use Each Training Method

| Method | Best For | Minimum Samples Needed |
|--------|----------|------------------------|
| LDA    | Very small datasets | 50-100 per class |
| SVM    | Medium datasets | 100-200 per class |
| CNN    | Large datasets with temporal patterns | 300+ per class |

**Current recommendation for 109 samples: Try LDA first, then collect more data**
