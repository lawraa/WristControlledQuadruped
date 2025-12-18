# New Gesture Set - Optimized for EMG Separability

## Why These Gestures Should Work Better

Your previous gestures (forward/backward/left/right/stop/jump) had a separability ratio of **1.3** (POOR).

The new gesture set targets **different muscle groups** and uses **antagonistic pairs**, which should produce more distinct EMG signals.

---

## The 6 New Gestures

### 1. **REST** (Baseline)
- **Action**: Relax completely
- **Description**: Let your hand hang naturally with no muscle tension
- **Why it works**: Minimal EMG activity, clear baseline
- **Robot mapping**: Stop/Neutral state

---

### 2. **FIST** (Flexor muscles)
- **Action**: Close hand into tight fist
- **Description**: Squeeze firmly, all fingers curled
- **Why it works**: Strong flexor digitorum activation
- **Robot mapping**: Could be Forward or any command

---

### 3. **HAND OPEN** (Extensor muscles)
- **Action**: Open hand wide, spread fingers
- **Description**: Extend all fingers as far as possible
- **Why it works**: Strong extensor digitorum activation (opposite of fist)
- **Robot mapping**: Could be Jump or any command

---

### 4. **WRIST FLEXION** (Wrist flexors)
- **Action**: Bend wrist downward
- **Description**: Point fingers toward floor, keep hand relaxed
- **Why it works**: Flexor carpi activation
- **Robot mapping**: Could be Backward or Turn

---

### 5. **WRIST EXTENSION** (Wrist extensors)
- **Action**: Bend wrist upward
- **Description**: Point fingers toward ceiling, keep hand relaxed
- **Why it works**: Extensor carpi activation (opposite of flexion)
- **Robot mapping**: Could be Forward or Turn

---

### 6. **PINCH** (Precision grip muscles)
- **Action**: Pinch thumb to index finger
- **Description**: Touch thumb tip to index fingertip, hold firmly
- **Why it works**: Thenar/lumbrical activation (different from power grip)
- **Robot mapping**: Could be special action or unused

---

## Why This Should Improve Separability

### Antagonistic Pairs:
1. **Fist ↔ Hand Open**: Opposite muscle groups (flexors vs extensors)
2. **Wrist Flexion ↔ Wrist Extension**: Opposite wrist movements
3. **Rest**: Baseline with minimal activity

### Different Muscle Activations:
- **Fist/Hand Open**: Finger muscles (digitorum)
- **Wrist movements**: Wrist muscles (carpi)
- **Pinch**: Precision grip muscles (thenar/lumbricals)
- **Rest**: Minimal activation

This diversity should create **much more distinct** EMG patterns.

---

## Expected Improvement

**Previous gestures**:
- Separability: 1.3 (POOR)
- All were subtle wrist/hand positions
- High overlap in muscle activation

**New gestures**:
- Expected separability: **2.0 - 3.0+** (GOOD to EXCELLENT)
- Clear antagonistic pairs
- Distinct muscle groups

---

## Tips for Maximum Separability

1. **REST**: Truly relax - no tension at all
2. **FIST**: Squeeze hard (not just closed fingers)
3. **HAND OPEN**: Spread fingers WIDE, not just extended
4. **WRIST FLEXION**: Bend wrist fully down
5. **WRIST EXTENSION**: Bend wrist fully up
6. **PINCH**: Firm pressure, not light touch

**Key**: Make each gesture EXAGGERATED and hold it STEADY during collection.

---

## How to Collect

```bash
python collect_data_auto.py
# Select [2] - Separability Test (10 per gesture)
```

Then check:
```bash
python check_separability.py
```

**Target**: Separability ratio **> 2.0**

---

## Mapping to Robot Commands (Later)

Once you have good separability and trained model, you can map gestures to robot commands:

| Gesture | Suggested Robot Command |
|---------|------------------------|
| Rest | Stop/Neutral |
| Fist | Forward |
| Hand Open | Jump |
| Wrist Flexion | Backward |
| Wrist Extension | (unused or speed control) |
| Pinch | (unused or special action) |

Or choose your own mapping based on what feels intuitive!

---

## Next Steps

1. Run separability test with new gestures
2. Check if ratio > 2.0
3. If yes → collect full dataset (300+ samples/gesture)
4. If no → try making gestures even more exaggerated
5. Train model
6. Map gestures to robot commands in classify_realtime.py
