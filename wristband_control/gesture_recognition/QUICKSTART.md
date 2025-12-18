# Quick Start Guide

## Installation

```bash
pip3 install -r requirements.txt
```

## Session-Based Workflow

**Each data collection creates a named session.** You can:
- Collect multiple sessions (different days, electrode placements, etc.)
- Train on a specific session
- Train on multiple sessions combined
- Compare different sessions

Sessions are stored in `training_data/<session_name>/`

## Three-Step Process

### Step 1: Collect Training Data

**Option A: Automated Collection (RECOMMENDED)**

```bash
./collect_data_auto.py
```

1. **Enter a session name** (e.g., "morning_session", "seated_v1", "john_day1")
   - Or press Enter to use timestamp
2. **Choose a preset:**
- **[1] 5-Minute Quick** - 15 samples/gesture (good for testing)
- **[2] 10-Minute Fast** - 30 samples/gesture (minimum recommended)
- **[3] 15-Minute Standard** - 50 samples/gesture (best balance)
- **[4] 30-Minute Extended** - 100 samples/gesture (maximum accuracy)

The system automatically:
- Prompts you for each gesture with 3-second countdown
- Shows exactly what action to perform
- Collects data for the gesture duration
- Gives you rest periods between gestures
- Randomizes gesture order for balanced training

**Option B: Manual Collection**

```bash
./collect_data.py
```

- Choose gesture number (1-6) manually
- Get ready when prompted
- System collects 200-sample window
- Repeat 30-50 times per gesture
- Press 'q' when done

**Target: 30-50 samples per gesture (180-300 total samples)**

### Step 2: Train Model (< 1 minute)

```bash
./train_model.py
```

**Select which session(s) to train on:**
- Select a single session by number
- Select `a` for all sessions (combines data)
- Select multiple: `1,3,4` (comma-separated)

What it does:
- Loads data from selected session(s)
- Extracts features (RMS, MAV, Waveform Length, Zero Crossings, Variance)
- Trains Random Forest classifier
- Shows accuracy metrics
- Saves model to `models/gesture_model.pkl`

**Target: >90% test accuracy**

### Step 3: Real-time Classification

```bash
./classify_realtime.py
```

- Loads trained model
- Classifies gestures in real-time
- Shows current command and confidence
- Press Ctrl+C to exit

## Gestures

| # | Gesture | Action | Command |
|---|---------|--------|---------|
| 1 | Forward | Extend wrist up | ↑ FORWARD |
| 2 | Backward | Flex wrist down | ↓ BACKWARD |
| 3 | Left | Tilt toward pinky | ← LEFT |
| 4 | Right | Tilt toward thumb | → RIGHT |
| 5 | Stop | Relax/neutral | ■ STOP |
| 6 | Jump | Spread fingers | ⤊ JUMP |

## Tips

- **Consistency is key**: Perform each gesture the same way every time
- **Start with "stop"**: Record neutral position first
- **Take breaks**: Avoid muscle fatigue
- **Check electrodes**: Ensure good skin contact throughout
- **Retrain if needed**: If you reposition electrodes, collect new data

## Troubleshooting

- **Low accuracy?** → Collect more samples (50+ per gesture)
- **Confused gestures?** → Check confusion matrix, collect more data for those specific gestures
- **Inconsistent?** → Verify electrode contact, retrain with fresh data
- **No connection?** → Check OpenBCI is on `/dev/ttyUSB0`, not `/dev/ttyUSB1`
