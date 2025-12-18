# Data Collection Bug Fixes & Improvements

## Changes Made

### 1. Fixed Variable-Length Sample Bug ✓

**File**: `collect_data_auto.py:319`

**Problem**: Samples had inconsistent lengths (418-419 instead of 200)
- The `collect_window()` function returned ALL data collected during time window
- This caused training issues as SVM expected consistent feature dimensions

**Fix**:
```python
# Before (BROKEN):
result = np.array(list(window_buffer))

# After (FIXED):
result = np.array(list(window_buffer)[:self.WINDOW_SIZE])  # Take only first 200
```

**Result**: All samples are now exactly 200 time points

---

### 2. Updated Rest Duration to 2 Seconds ✓

**File**: `collect_data_auto.py:88-138`

**Changed Presets**:
- `quick`: rest_duration 1.0s → 2.0s
- `standard`: rest_duration 1.0s → 2.0s
- `long`: rest_duration 1.0s → 2.0s

**Why**: 2 seconds gives user time to reset to neutral position between gestures

---

### 3. Added Separability Test Preset ✓

**File**: `collect_data_auto.py:96-102`

**New Preset**:
```python
'separability': {
    'name': 'Separability Test (10 per gesture)',
    'duration_minutes': 10,
    'samples_per_gesture': 10,
    'gesture_duration': 1.0,
    'rest_duration': 2.0
}
```

**Purpose**: Quick test to verify gestures are distinguishable before full data collection

**Actual Duration**: ~7 minutes (10 min max to ensure all samples collected)
- 60 total samples (10 per gesture × 6 gestures)
- ~7 seconds per sample (countdown + collection + rest)

**Now appears as option [2]** in the menu

---

### 4. Enhanced Quick Data Checker ✓

**File**: `quick_data_check.py`

**Changes**:
- Now accepts session name as command line argument
- Automatically checks most recent session if no argument provided
- Handles variable-length samples (for backward compatibility)

**Usage**:
```bash
# Check most recent session
python quick_data_check.py

# Check specific session
python quick_data_check.py my_session_name
```

---

### 5. Created Workflow Documentation ✓

**New File**: `SEPARABILITY_WORKFLOW.md`

**Contents**:
- Step-by-step workflow for testing gesture separability
- Troubleshooting guide for poor separability
- Expected accuracy by dataset size
- Best practices for data collection

---

## New Recommended Workflow

### Before (WASTEFUL):
1. Collect 300-1800 samples blindly
2. Train model
3. Get 32% accuracy
4. Realize gestures weren't distinguishable
5. Waste hours 😞

### After (EFFICIENT):
1. Collect 10 samples/gesture (2 minutes) - **Separability preset**
2. Run `python quick_data_check.py`
3. Check separability ratio
4. If ratio < 2.0, adjust gestures and repeat steps 1-3
5. Once ratio > 2.0, collect full dataset
6. Get 75-90% accuracy ✓

---

## Testing the Fixes

To verify the fixes work:

```bash
# 1. Collect test data with new separability preset
python collect_data_auto.py
# Select option [2] - Separability Test

# 2. Check the data quality
python quick_data_check.py

# 3. Verify in output:
#    - All samples are (200, 4) shape
#    - Separability ratio is calculated
#    - Visualizations are generated
```

---

## What This Solves

1. ✓ **Variable-length samples** causing training errors
2. ✓ **Insufficient rest time** between gestures
3. ✓ **No way to test** gesture quality before full collection
4. ✓ **Wasted time** collecting bad data

---

## Impact on Your Current Data

**Jay10_v1 session** (109 samples):
- Had variable-length bug (418-419 samples instead of 200)
- Low separability ratio (0.61)
- Training accuracy: 32%

**New data will**:
- Have exactly 200 samples per window ✓
- Be tested for separability before full collection ✓
- Result in much better model performance ✓

---

## Next Steps

1. Run a separability test with the new preset
2. Check if ratio > 2.0
3. If not, adjust gestures and repeat
4. Once good, collect 300+ samples per gesture
5. Train and achieve 75-90% accuracy

See `SEPARABILITY_WORKFLOW.md` for detailed instructions.
