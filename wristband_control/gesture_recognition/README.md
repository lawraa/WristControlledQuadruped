# EMG Gesture Recognition System

Real-time gesture recognition system for controlling a quadruped robot using 4-channel EMG wristband.

## Overview

This system uses machine learning to classify 6 wrist gestures that map to quadruped movement commands:

| Gesture | Muscle Action | Robot Command |
|---------|---------------|---------------|
| **Forward** | Wrist extension (hand up) | Move forward |
| **Backward** | Wrist flexion (hand down) | Move backward |
| **Left** | Ulnar deviation (toward pinky) | Turn left |
| **Right** | Radial deviation (toward thumb) | Turn right |
| **Stop** | Rest/neutral position | Stop |
| **Jump** | Spread fingers wide | Jump |

## Hardware Setup

### Electrode Configuration
- **4 differential pairs** on palm side of forearm
- **Pair 1**: Top/Bottom N1P
- **Pair 2**: Top/Bottom N2P
- **Pair 3**: Top/Bottom N5P
- **Pair 4**: Top/Bottom N6P
- **Reference**: Bottom BIAS pin (on bony area of wrist)

### Important
In OpenBCI GUI, turn OFF SRB2 for channels 1, 2, 5, and 6.

## Workflow

### 1. Collect Training Data

**Automated Collection (Recommended):**

```bash
cd gesture_recognition
python3 collect_data_auto.py
```

Choose a preset session:
- **5-Minute Quick**: 15 samples/gesture (testing)
- **10-Minute Fast**: 30 samples/gesture (minimum)
- **15-Minute Standard**: 50 samples/gesture (recommended)
- **30-Minute Extended**: 100 samples/gesture (best accuracy)

Features:
- Automatic gesture prompting with countdowns
- Clear instructions for each gesture
- Randomized gesture order
- Timed rest periods
- Progress tracking

**Manual Collection:**

```bash
python3 collect_data.py
```

**Instructions:**
- Record 30-50 samples per gesture
- Maintain consistent muscle activation
- Take breaks between recordings
- Samples are saved to `training_data/` directory

**Tips:**
- Start with "stop" (neutral) gesture first
- Keep electrode contact consistent
- Perform gestures naturally and smoothly

### 2. Train the Model

```bash
python3 train_model.py
```

This will:
- Load all collected samples
- Extract features (RMS, MAV, Waveform Length, Zero Crossings, Variance)
- Train a Random Forest classifier
- Evaluate with cross-validation
- Save model to `models/gesture_model.pkl`

**Expected Performance:**
- Target accuracy: >90%
- If accuracy is low:
  - Collect more samples
  - Ensure consistent electrode placement
  - Check for noisy data

### 3. Real-time Classification

```bash
python3 classify_realtime.py
```

This will:
- Load the trained model
- Stream EMG data in real-time
- Classify gestures with confidence scores
- Display current command

## Features

### Data Collection
**`collect_data_auto.py` (Automated - Recommended)**
- Four preset session lengths (5, 10, 15, 30 minutes)
- Automatic gesture prompting with countdowns
- Detailed action descriptions for each gesture
- Randomized gesture ordering
- Timed rest periods between gestures
- Real-time progress tracking
- Balanced data collection

**`collect_data.py` (Manual)**
- Interactive menu for selecting gestures
- Automatic windowing (200 samples @ ~1000Hz)
- Incremental saving (data preserved if interrupted)
- Statistics display

### Training (`train_model.py`)
- 5 features per channel (20 total features)
- Random Forest classifier (robust, fast)
- Cross-validation for reliable performance
- Feature importance analysis
- Confusion matrix

### Real-time Classification (`classify_realtime.py`)
- Sliding window approach
- Prediction smoothing (majority vote over 5 windows)
- Confidence scores
- Visual feedback

## Files and Directories

```
gesture_recognition/
├── collect_data_auto.py      # AUTOMATED data collection (recommended)
├── collect_data.py           # Manual data collection
├── train_model.py            # Model training script
├── classify_realtime.py      # Real-time classifier
├── README.md                 # Complete documentation
├── QUICKSTART.md             # Quick reference guide
├── requirements.txt          # Python dependencies
├── training_data/            # Collected samples (created on first run)
│   ├── forward.jsonl
│   ├── backward.jsonl
│   ├── left.jsonl
│   ├── right.jsonl
│   ├── stop.jsonl
│   ├── jump.jsonl
│   └── dataset_summary.json
└── models/                   # Trained models (created on first run)
    └── gesture_model.pkl
```

## Dependencies

```bash
pip3 install numpy scikit-learn joblib pyserial
```

Or install from requirements file:

```bash
pip3 install -r requirements.txt
```

## Troubleshooting

### Low Classification Accuracy
- **Collect more samples** - 50+ per gesture
- **Check electrode contact** - Ensure good skin contact
- **Consistent placement** - Electrodes should be in same position each session
- **Remove noise** - Check reference electrode on bony area

### Inconsistent Predictions
- **Increase smoothing** - Modify `gesture_history` maxlen in `classify_realtime.py`
- **Retrain with more data** - Especially for confused gestures
- **Check for electrode drift** - Reposition if needed

### Connection Issues
- Ensure OpenBCI is powered on
- Check USB cable connection
- Verify port is not `/dev/ttyUSB1` (Dynamixel)
- Run `ls /dev/ttyUSB*` to see available ports

### Model Not Found
- Run `train_model.py` first to create the model
- Check `models/gesture_model.pkl` exists

## Advanced Usage

### Retrain Model
To add more data to existing dataset:
1. Run `collect_data.py` again (data appends to existing files)
2. Run `train_model.py` to retrain with all data

### Adjust Window Size
- Default: 200 samples (~200ms at 1000Hz)
- Modify `WINDOW_SIZE` in all three scripts
- Larger window = more stable but slower response
- Smaller window = faster but less stable

### Change Classifier
In `train_model.py`, replace RandomForestClassifier with:
- SVM: `SVC(kernel='rbf', probability=True)`
- Neural Network: `MLPClassifier(hidden_layer_sizes=(100, 50))`

## Integration with Quadruped

To integrate with robot control, modify `classify_realtime.py`:

```python
def send_command_to_robot(self, gesture):
    """Send command to quadruped based on gesture"""
    command_map = {
        'forward': self.robot.move_forward,
        'backward': self.robot.move_backward,
        'left': self.robot.turn_left,
        'right': self.robot.turn_right,
        'stop': self.robot.stop,
        'jump': self.robot.jump
    }

    if gesture in command_map:
        command_map[gesture]()
```

## Performance Tips

1. **Calibration**: Retrain model if you reposition electrodes
2. **Consistency**: Perform gestures the same way each time
3. **Rest state**: Always return to neutral "stop" position between gestures
4. **Muscle fatigue**: Take breaks during long sessions
5. **Electrode gel**: Use conductive gel for better signal quality

## Next Steps

After successful gesture recognition, you can:
- Add more gestures (modify `GESTURES` dict in `collect_data.py`)
- Implement gesture sequences (e.g., double-tap for special commands)
- Add confidence thresholds (only execute if confidence > 80%)
- Log gesture data for analysis
- Integrate with quadruped motor control system

## Support

For issues or questions:
- Check electrode connections and OpenBCI settings
- Review the troubleshooting section
- Ensure dependencies are installed correctly
