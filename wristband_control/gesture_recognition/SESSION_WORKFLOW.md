# Session-Based Data Collection Workflow

## Overview

The gesture recognition system now uses **named sessions** to organize your training data. This gives you flexibility to:
- **Collect data over multiple days** without mixing datasets
- **Compare different electrode placements** or configurations
- **Train on specific sessions** or combine multiple sessions
- **Track your progress** across different collection attempts

## What is a Session?

A session is a single data collection run with a unique name. Each session is stored in its own directory:

```
training_data/
├── morning_session/
│   ├── forward.jsonl
│   ├── backward.jsonl
│   ├── ...
│   └── session_info.json
├── afternoon_session/
│   ├── forward.jsonl
│   ├── ...
│   └── session_info.json
└── 20251217_143022/  (timestamp if no name given)
    ├── forward.jsonl
    ├── ...
    └── session_info.json
```

## Workflow

### 1. Collect Data (Creates a New Session)

Run either collection script:

```bash
./collect_data_auto.py
# or
./collect_data.py
```

**You'll be prompted for a session name:**
- Use descriptive names: `seated_morning`, `standing_v1`, `john_day1`
- Or press Enter to use a timestamp: `20251217_143022`

**The script will:**
- Show you existing sessions (if any)
- Save all data to `training_data/<session_name>/`
- Create a `session_info.json` with metadata

### 2. Train Model (Select Which Sessions to Use)

```bash
./train_model.py
```

**You'll see a list of available sessions:**

```
Available sessions:

  [1] morning_session
      Samples: 300 | Date: 2025-12-17

  [2] afternoon_session
      Samples: 250 | Date: 2025-12-17

  [3] standing_test
      Samples: 150 | Date: 2025-12-16

  [a] All sessions (3 total)

Select session(s) to train on (number, 'a' for all, or comma-separated):
```

**Your options:**
- **Single session**: Enter `1` to train on just morning_session
- **Multiple sessions**: Enter `1,2` to combine morning + afternoon
- **All sessions**: Enter `a` to use all available data

**Why select specific sessions?**
- If electrode placement changed, use only sessions with same placement
- Compare accuracy between different collection days
- Build larger datasets by combining good sessions

### 3. Real-Time Classification

```bash
./classify_realtime.py
```

Uses the most recently trained model (from selected sessions).

## Common Scenarios

### Scenario 1: First Time Setup

```bash
# Day 1: Collect initial dataset
./collect_data_auto.py
> Enter session name: first_attempt
> [Choose preset 3 - Standard]

# Train model
./train_model.py
> Select: 1

# Test
./classify_realtime.py
```

### Scenario 2: Improving Your Model

```bash
# Day 2: Collect more data
./collect_data_auto.py
> Enter session name: day2_more_data
> [Choose preset 3 - Standard]

# Train on BOTH sessions for more data
./train_model.py
> Select: a  (all sessions)

# Or train on just new session to compare
./train_model.py
> Select: 2
```

### Scenario 3: Changed Electrode Placement

```bash
# New electrode configuration
./collect_data_auto.py
> Enter session name: new_electrodes_v2
> [Collect data]

# Train ONLY on new session (don't mix with old placement)
./train_model.py
> Select: 3  (just the new_electrodes_v2 session)
```

### Scenario 4: Different Users

```bash
# User 1
./collect_data_auto.py
> Enter session name: alice_seated

# User 2
./collect_data_auto.py
> Enter session name: bob_seated

# Train separate models
./train_model.py
> Select: 1  (for Alice)

./train_model.py
> Select: 2  (for Bob)
```

## Benefits

✅ **No data loss** - Each collection is preserved independently
✅ **Easy experimentation** - Try different electrode placements without erasing old data
✅ **Incremental improvement** - Add more data over time by combining sessions
✅ **Comparison** - Train on different sessions to see which works best
✅ **Organization** - Clear names help you track what each session represents

## Session Naming Tips

**Good names:**
- `seated_morning` - Describes position and time
- `electrodes_v1` - Version number for different placements
- `john_calibration` - User name and purpose
- `fast_gestures` - Describes the type of data

**Avoid:**
- `test` - Too generic, you'll forget what it was
- `asdf` - Not descriptive
- Just using timestamps - Hard to remember what each was for

## Managing Sessions

**View existing sessions:**
Both collection scripts show existing sessions when you start them.

**Delete old sessions:**
```bash
rm -rf training_data/old_session_name
```

**Rename a session:**
```bash
mv training_data/old_name training_data/new_name
```

**Check session info:**
```bash
cat training_data/session_name/session_info.json
```

## FAQs

**Q: Should I delete old sessions before collecting new data?**
A: No! Keep them. You can choose which sessions to train on later.

**Q: Can I combine data from different days?**
A: Yes! Use `a` or comma-separated numbers when training (e.g., `1,2,3`).

**Q: What if I changed electrode placement?**
A: Create a new session. Only train on sessions with the same electrode placement.

**Q: How many sessions should I collect?**
A: Start with 1-2 good sessions. Add more if you need to improve accuracy or test different conditions.

**Q: Can I add more data to an existing session?**
A: Not directly, but you can create a new session with the same name scheme (e.g., `morning_session_part2`) and combine them during training.

**Q: Do sessions take up a lot of space?**
A: No. Each session is typically 1-5 MB. You can keep dozens without issue.

## Summary

- **Collect**: Name your session, collect data
- **Train**: Select which session(s) to use
- **Classify**: Use the trained model
- **Repeat**: Collect more sessions to improve over time

This workflow gives you full control over your training data while preventing accidental data loss!
