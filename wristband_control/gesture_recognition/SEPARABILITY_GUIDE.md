# Separability Score Interpretation Guide

## What is the Separability Ratio?

The separability ratio measures how distinguishable your gestures are from each other relative to the variability within each gesture.

**Formula**: `Separability Ratio = Average Distance Between Gestures / Average Within-Gesture Spread`

**In simple terms**:
- Higher ratio = gestures are far apart and consistent
- Lower ratio = gestures are too similar or too inconsistent

---

## Score Ranges and What They Mean

### 🟢 **Ratio ≥ 3.0 - EXCELLENT**

**What it means**:
- Gestures are very well-separated
- Low within-gesture variability (consistent performance)
- Ideal data quality

**Expected Model Performance**:
- With 300 samples/gesture: **90-95% accuracy**
- With 600 samples/gesture: **95%+ accuracy**

**Action**:
✓ Immediately collect full dataset (300-500+ samples per gesture)
✓ You've nailed the gestures!

---

### 🟢 **Ratio 2.5 - 3.0 - VERY GOOD**

**What it means**:
- Gestures are well-separated
- Good consistency
- High-quality data

**Expected Model Performance**:
- With 300 samples/gesture: **85-90% accuracy**
- With 600 samples/gesture: **90-95% accuracy**

**Action**:
✓ Collect full dataset (300+ samples per gesture)
✓ Should work well for practical use

---

### 🟡 **Ratio 2.0 - 2.5 - GOOD**

**What it means**:
- Gestures are distinguishable
- Acceptable separation
- Usable but not optimal

**Expected Model Performance**:
- With 300 samples/gesture: **75-85% accuracy**
- With 600 samples/gesture: **80-90% accuracy**

**Action**:
✓ Can proceed with data collection
⚠ Consider making gestures slightly more exaggerated for better results

---

### 🟡 **Ratio 1.5 - 2.0 - MARGINAL**

**What it means**:
- Gestures are somewhat distinguishable
- Significant overlap between some gestures
- May struggle with accuracy

**Expected Model Performance**:
- With 300 samples/gesture: **60-75% accuracy**
- With 600 samples/gesture: **70-80% accuracy**

**Action**:
⚠ You CAN collect data, but results will be mediocre
⚠ BETTER: Improve gestures first
- Make movements MORE exaggerated
- Hold positions more steady
- Check electrode placement
- Run another separability test

**Decision Point**: Is 70% accuracy good enough for your use case?
- If YES: Proceed with caution
- If NO: Fix gestures first

---

### 🔴 **Ratio 1.0 - 1.5 - POOR**

**What it means**:
- Gestures have heavy overlap
- High within-gesture variability
- Data quality issues

**Expected Model Performance**:
- With 300 samples/gesture: **40-60% accuracy**
- With 600 samples/gesture: **50-70% accuracy**

**Action**:
✗ DO NOT collect more data yet!
✗ Fix these issues first:
1. Make gestures MUCH more exaggerated
2. Reduce number of gestures (try just 4 most distinct)
3. Check electrode placement (see ELECTRODE_GUIDE.md)
4. Practice consistent gesture performance
5. Run new separability test

---

### 🔴 **Ratio < 1.0 - VERY POOR**

**What it means**:
- Within-gesture variation is larger than between-gesture differences
- Model cannot learn meaningful patterns
- Fundamental data collection issues

**Expected Model Performance**:
- Any amount of data: **30-50% accuracy** (barely better than random)

**Action**:
✗ STOP - Data collection will waste your time!
✗ Critical fixes needed:
1. Verify electrode placement is correct
2. Check electrode contact (clean skin, good adhesion)
3. Use completely different gestures (more distinct)
4. Consider only 3-4 most different gestures
5. Make movements EXTREMELY exaggerated
6. Ensure you're holding gestures steady

**Example**: Your Jay10_v1 session had ratio 0.61 (VERY POOR)
- This is why it got only 32% accuracy despite proper training

---

## Real-World Examples

### Example 1: Your Jay10_v1 Data
```
Separability Ratio: 0.61
Result: 32% accuracy with SVM
Problem: Gestures too similar, within-gesture variance too high
```

### Example 2: Good Data (Hypothetical)
```
Separability Ratio: 2.8
Result: 87% accuracy with SVM
Success: Well-separated gestures, consistent performance
```

---

## What Affects Separability Score?

### Factors that INCREASE score (good):
- ✓ Exaggerated, distinct gestures
- ✓ Holding gestures steady during collection
- ✓ Consistent electrode placement
- ✓ Good electrode contact (clean skin)
- ✓ Using fundamentally different movements
- ✓ Taking breaks to avoid muscle fatigue

### Factors that DECREASE score (bad):
- ✗ Subtle, similar gestures
- ✗ Fidgeting during collection
- ✗ Inconsistent electrode placement
- ✗ Poor electrode contact
- ✗ Using similar movements for different gestures
- ✗ Muscle fatigue affecting signal quality

---

## Troubleshooting Low Scores

### If ratio < 2.0, try these:

**1. Simplify Gesture Set**
Remove similar gestures. Example:
- Keep: forward, backward, stop, jump
- Remove: left, right (often too similar to others)

**2. Exaggerate Movements**
Don't be subtle:
- Forward: Bend wrist UP as far as possible
- Backward: Bend wrist DOWN to the max
- Stop: Completely relax (dead weight)
- Jump: SPREAD fingers as wide as possible

**3. Check Electrode Placement**
- Should be on forearm muscle belly
- Not on wrist or hand
- See ELECTRODE_GUIDE.md

**4. Hold Steady**
- Don't move during the 1-second collection
- Practice holding each gesture before collecting

**5. Check Signal Quality**
```bash
# First verify you're getting good EMG signals
python ../emg_visualizer.py
```

---

## Quick Reference Table

| Ratio | Quality | Accuracy (300 samples) | Action |
|-------|---------|----------------------|--------|
| ≥ 3.0 | Excellent | 90-95% | ✓ Collect full dataset now |
| 2.5-3.0 | Very Good | 85-90% | ✓ Collect full dataset |
| 2.0-2.5 | Good | 75-85% | ✓ Can proceed |
| 1.5-2.0 | Marginal | 60-75% | ⚠ Improve first |
| 1.0-1.5 | Poor | 40-60% | ✗ Fix issues first |
| < 1.0 | Very Poor | 30-50% | ✗ Stop, major fixes needed |

---

## Remember

**The separability ratio predicts your model's potential.**

- High ratio + more data = excellent accuracy ✓
- Low ratio + more data = still poor accuracy ✗

**Always fix separability BEFORE collecting hundreds of samples!**

Test → Check → Adjust → Repeat until ratio > 2.0
