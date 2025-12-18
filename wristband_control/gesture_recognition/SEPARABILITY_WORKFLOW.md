# Gesture Separability Testing Workflow

## Quick Start: Test Before You Invest Time

Before collecting hundreds of samples, verify your gestures are actually distinguishable!

### Step 1: Collect 10 Samples Per Gesture (~7 minutes)

```bash
python collect_data_auto.py
```

When prompted, select the **"Separability Test (10 per gesture)"** option.

**Note**: This takes about 7 minutes (not 2!) because:
- 10 samples × 6 gestures = 60 samples
- Each sample: 3s countdown + 1s collection + 1s display + 2s rest = 7s
- Total: 60 × 7s ≈ 7 minutes

**IMPORTANT - Make gestures VERY EXAGGERATED:**
- Hold each gesture steady during collection
- Make movements large and distinct
- Keep electrode placement consistent

### Step 2: Check Separability

```bash
python quick_data_check.py
```

This automatically analyzes your most recent session.

Or specify a session:
```bash
python quick_data_check.py session_name_here
```

### Step 3: Interpret Results

**Look at the "SEPARABILITY SCORE":**

- **Ratio > 2.5**: ✓ EXCELLENT - Go collect 300+ samples per gesture
- **Ratio 1.5-2.5**: ⚠ MARGINAL - Adjust gestures, try again
- **Ratio < 1.5**: ✗ POOR - Fix issues before collecting more data

**Check the visualizations:**
- `data_check_signals.png`: See raw EMG signals
- `data_check_features.png`: **KEY INSIGHT** - boxes should barely overlap

### Step 4: Troubleshooting Poor Separability

If separability ratio < 2.0:

1. **Make gestures MORE exaggerated**:
   - Forward: Bend wrist UP as far as possible
   - Backward: Bend wrist DOWN as far as possible
   - Stop: Completely relax (loose hand)
   - Jump: SPREAD fingers as wide as possible

2. **Check electrode placement**:
   - See ELECTRODE_GUIDE.md
   - Electrodes should be on muscle belly (forearm)
   - Clean skin before placing electrodes

3. **Reduce number of gestures**:
   - Try just 4 gestures: forward, backward, stop, jump
   - Skip left/right (they're often too similar to others)

4. **Perform gestures consistently**:
   - Same position/intensity for same gesture
   - Hold steady during 1-second collection window
   - Take breaks if muscles get fatigued

### Step 5: Once Separability is Good (>2.0)

Collect a proper dataset:

```bash
python collect_data_auto.py
```

Select:
- **"15-Minute Standard Session"** for 50 samples/gesture (300 total)
- **"30-Minute Extended Session"** for 100 samples/gesture (600 total)

### Step 6: Train and Test

```bash
# Train the model
python train_model_svm.py

# Test in real-time
python classify_realtime.py
```

## Expected Results by Dataset Size

| Samples/Gesture | Total Samples | Expected Accuracy | Recommendation |
|-----------------|---------------|-------------------|----------------|
| 10              | 60            | N/A               | Separability test only |
| 50              | 300           | 60-75%            | Minimum for basic use |
| 100             | 600           | 75-85%            | Good for testing |
| 300+            | 1800+         | 85-95%            | Production quality |

## Changes Made to Fix Data Quality Issues

1. **Fixed variable-length bug**: Samples now exactly 200 time points
2. **Updated rest duration**: 2 seconds between gestures (was 1-3s)
3. **New separability preset**: Quick 10-sample test before full collection

## Key Insight

**Separability ratio is MORE important than dataset size!**

- Good separability + 300 samples = 75-85% accuracy ✓
- Poor separability + 3000 samples = 40-60% accuracy ✗

Always test separability first before investing time in data collection.
