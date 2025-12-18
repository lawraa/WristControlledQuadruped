# OpenBCI Electrode Setup Guide for Wrist EMG

## Hardware Overview

Your OpenBCI Cyton 16-channel board has:
- **8 channels on Cyton board** (channels 1-8)
- **8 channels on Daisy expansion** (channels 9-16, if you have it)
- **Each channel has**: N (negative), P (positive) inputs
- **Shared pins**: SRB (reference), BIAS (noise reduction)

## What You Need

### Electrodes
- **Wet electrodes**: Disposable Ag/AgCl snap electrodes (recommended for starting)
- **Dry electrodes**: Reusable metal electrodes (for final wristband)
- **Electrode gel** (if using wet electrodes)

### Cables
- EMG snap cables that come with OpenBCI
- Each cable has 3 wires: P (positive), N (negative), and usually a pin for reference

## OpenBCI Pin Configuration

Looking at your Cyton board, you'll see pins for each channel:

```
Channel 1:  1P (white)  1N (black)
Channel 2:  2P (white)  2N (black)
Channel 3:  3P (white)  3N (black)
...
Channel 8:  8P (white)  8N (black)

Shared:
- SRB (reference) - multiple pins available
- BIAS (active noise reduction) - multiple pins available
```

## EMG Electrode Placement for Wrist Control

### Basic 2-Channel Setup (Start Here)

**Channel 1 - Wrist Flexors:**
- **P (positive)**: Place on belly of flexor carpi radialis (palm side of forearm, 2-3 inches below elbow)
- **N (negative)**: Place 2-3 cm away along the same muscle
- These muscles activate when you flex your wrist downward

**Channel 2 - Wrist Extensors:**
- **P (positive)**: Place on extensor carpi radialis (back of forearm, 2-3 inches below elbow)
- **N (negative)**: Place 2-3 cm away along the same muscle
- These muscles activate when you extend your wrist upward

**Reference (SRB):**
- Place on a bony, electrically neutral spot
- **Best location**: Elbow (olecranon process - the bony point)
- Or: Back of hand over a knuckle

**BIAS:**
- Place on another neutral location
- **Good location**: Opposite elbow or wrist bone

### Visual Placement

```
ARM VIEW (Palm up):

        Elbow ← [REFERENCE]
          |
    Flexor side (palm facing up)
    [Channel 1: P---N] (2-3cm apart)
          |
          |
    ← Wrist


ARM VIEW (Palm down):

        Elbow ← [REFERENCE]
          |
    Extensor side (back of hand up)
    [Channel 2: P---N] (2-3cm apart)
          |
          |
    ← Wrist
```

## Step-by-Step Connection

### 1. Prepare the Skin
- Clean the skin with alcohol wipe
- Let it dry completely
- (Optional) Lightly abrade with prep pad to reduce impedance

### 2. Apply Electrodes
- Apply electrode gel if using wet electrodes
- Press electrodes firmly on the skin
- Place them along the muscle fiber direction (lengthwise)

### 3. Connect to OpenBCI

**For Channel 1 (Flexors):**
```
OpenBCI Pin → Electrode Location
1P (white)  → Flexor muscle (proximal - closer to elbow)
1N (black)  → Flexor muscle (distal - 2-3cm toward wrist)
SRB         → Elbow bone
BIAS        → Other neutral location
```

**For Channel 2 (Extensors):**
```
OpenBCI Pin → Electrode Location
2P (white)  → Extensor muscle (proximal)
2N (black)  → Extensor muscle (distal - 2-3cm toward wrist)
(Share same SRB and BIAS)
```

### 4. Check Connection
- Power on the OpenBCI board
- Run the monitor script: `./openbci_monitor.py`
- You should now see data packets coming in
- Flex/extend your wrist - you should see the packet rate or data change

## Advanced: 4-6 Channel Setup

For better control, you can add more muscles:

**Channel 3 - Finger Flexors (Flexor Digitorum)**
- Deeper in forearm, palm side
- Activates when closing fist

**Channel 4 - Finger Extensors (Extensor Digitorum)**
- Back of forearm
- Activates when opening hand

**Channel 5 - Thumb Muscles (Thenar)**
- Base of thumb on palm
- Thumb movements

**Channel 6 - Pronator/Supinator**
- Forearm rotation muscles
- For twisting motions

## Troubleshooting

### No Signal / Flat Line
- Check that board is powered on
- Verify cables are firmly connected to board
- Check electrode contact with skin
- Ensure reference (SRB) is connected

### Noisy Signal
- Add more electrode gel (wet electrodes)
- Improve skin contact
- Connect BIAS electrode
- Keep away from AC power sources
- Use shielded cables if possible

### Signal Too Small
- Place electrodes directly over muscle belly
- Increase distance between P and N electrodes (not more than 4cm)
- Clean skin better
- Press electrodes more firmly

### Signal Saturating
- Electrodes might be too far apart
- Reduce distance between P and N
- Check for loose connections causing artifacts

## Electrode Spacing Guidelines

- **Optimal spacing**: 2-3 cm between P and N electrodes
- **Direction**: Along the muscle fibers (lengthwise)
- **Avoid**: Crossing over different muscles
- **Avoid**: Placing over tendons or bones

## Testing Your Setup

1. **Baseline test**: Relax arm completely - should see low amplitude noise
2. **Flex test**: Flex wrist down - Channel 1 should show large spike
3. **Extend test**: Extend wrist up - Channel 2 should show large spike
4. **Isolation test**: Try to activate one channel without the other

## Next Steps

Once you have good signals:
1. Create a signal processing pipeline (filtering, rectification, smoothing)
2. Extract features (amplitude, frequency, patterns)
3. Map muscle activations to robot controls
4. Train a classifier for gesture recognition

## Quick Reference Card

```
MUSCLE               | LOCATION           | ACTION
---------------------|--------------------|-----------------
Flexor Carpi R.      | Palm side, outer   | Wrist down
Extensor Carpi R.    | Back side, outer   | Wrist up
Flexor Digitorum     | Palm side, center  | Fist close
Extensor Digitorum   | Back side, center  | Fingers open
Pronator Teres       | Palm side, upper   | Palm down rotation
Supinator            | Back side, upper   | Palm up rotation
```

## Safety Notes

- Use only electrodes designed for biopotential recording
- Don't use near the heart or on damaged skin
- Clean and dry electrodes after use
- Dispose of wet electrodes properly
- The OpenBCI board is NOT medical grade - for research/hobby use only
