# Quick Start: Wiring Your First EMG Electrodes

## What You Need

- OpenBCI Cyton board (powered on)
- 3-5 snap electrodes (Ag/AgCl recommended)
- EMG cables from OpenBCI kit
- Alcohol wipes
- Your forearm

## 5-Minute Setup

### Step 1: Prepare Skin
```
1. Clean forearm with alcohol wipe
2. Let dry (30 seconds)
```

### Step 2: Place Electrodes

Place electrodes on your forearm as shown:

```
        ┌─────── ELBOW ───────┐
        │                     │
        │    [REF]            │  ← Reference electrode on bony part
        │                     │
        │                     │
        │  PALM SIDE:         │     BACK SIDE:
        │  [P]─[N]            │     [P]─[N]
        │   Ch1 (2-3cm)       │      Ch2 (2-3cm)
        │   Flexors           │      Extensors
        │                     │
        │                     │
        └───── WRIST ─────────┘
             [BIAS]  ← On wrist bone or other elbow
```

**Electrode positions:**
- **Ch1-P**: Flexor muscles (palm side, 3 inches below elbow)
- **Ch1-N**: 2-3 cm toward wrist from Ch1-P
- **Ch2-P**: Extensor muscles (back side, 3 inches below elbow)
- **Ch2-N**: 2-3 cm toward wrist from Ch2-P
- **REF (SRB)**: Bony part of elbow
- **BIAS**: Wrist bone or opposite elbow

### Step 3: Wire to OpenBCI Board

Looking at your Cyton board:

```
CHANNEL 1 (Flexors):
    Board Pin → Electrode
    ─────────────────────
    1P (TOP)  → Flexor P (white snap cable)
    1N (BOT)  → Flexor N (black snap cable)

CHANNEL 2 (Extensors):
    Board Pin → Electrode
    ─────────────────────
    2P (TOP)  → Extensor P (white snap cable)
    2N (BOT)  → Extensor N (black snap cable)

REFERENCE & BIAS:
    SRB       → Elbow bone
    BIAS      → Wrist bone
```

### Step 4: Test It!

```bash
cd wristband_control
./openbci_monitor.py
```

You should see:
- ✓ Connected message
- ✓ Streaming started
- ✓ Packet count increasing

### Step 5: Test Muscle Activity

Try these movements and watch for data changes:

1. **Relax arm** - baseline activity
2. **Flex wrist DOWN** - Ch1 should spike
3. **Extend wrist UP** - Ch2 should spike
4. **Make a fist** - Both channels active

If you see packets coming through - SUCCESS! Your EMG is working.

## Troubleshooting

**No packets?**
- Check battery in OpenBCI board
- Verify RF dongle is plugged in
- Power cycle the board

**Packets but no signal changes?**
- Check electrode contact (press firmly)
- Verify P/N connections not swapped
- Make sure reference (SRB) is connected
- Try adding electrode gel

**Noisy signal?**
- Ensure BIAS is connected
- Move away from AC power sources
- Improve skin-electrode contact

## What's Next?

Once you have signals:
1. Use `./emg_visualizer.py` to see live graphs
2. Add more channels for finger control
3. Process signals (filter, rectify, smooth)
4. Map muscle activity to robot commands

## Pin Reference Card

Print this and keep it handy:

```
┌──────────────────────────────────────┐
│   OPENBCI CYTON - TOP 8 CHANNELS     │
├──────────────────────────────────────┤
│ CH │  P (white)  │  N (black)        │
├────┼─────────────┼───────────────────┤
│ 1  │  Flexor +   │  Flexor -         │
│ 2  │  Extensor + │  Extensor -       │
│ 3  │  Fing Flex+ │  Fing Flex-       │
│ 4  │  Fing Ext+  │  Fing Ext-        │
│ 5  │  Thumb +    │  Thumb -          │
│ 6  │  (custom)   │  (custom)         │
│ 7  │  (custom)   │  (custom)         │
│ 8  │  (custom)   │  (custom)         │
├────┴─────────────┴───────────────────┤
│ SRB  → Reference (elbow bone)        │
│ BIAS → Noise reduction (wrist bone)  │
└──────────────────────────────────────┘
```

## Safety Reminders

- Use only on arms/hands (not near heart)
- Don't use on broken skin
- This is NOT medical equipment
- Clean electrodes after use
- Have fun controlling robots with your muscles!
