# Inspection-Time

PsychoPy 2-AFC inspection-time task. Two blocks (`SQUARES`, `CIRCLES`) each
run a 3-down-1-up staircase to find a per-participant SOA, then deliver
`NO_TRIALS` test trials at that SOA. EEG triggers are sent over a parallel
port.

[![Demo Video](https://img.youtube.com/vi/C44MOs_Y-XE/0.jpg)](https://www.youtube.com/watch?v=C44MOs_Y-XE)

## Run

```bash
python main.py
```

Requires PsychoPy, `pyparallel`, `pyyaml`, `numpy`. A working parallel port
at the default address is required — without it `main.py` will not import.

A GUI prompts for `IDENTYFIKATOR`, `PŁEĆ` (M/K), `WIEK`. `PART_ID` is the
concatenation of all three (e.g. `01M20`). Results land in `results/`.

### Hardware assumptions

| Setting     | Value                  | Where                |
|-------------|------------------------|----------------------|
| Frame rate  | 60 Hz                  | `main.py:275` (hard) |
| Resolution  | 1920×1080, fullscreen  | `main.py:274` (hard) |
| Response    | `left` / `right` arrow | `main.py:18`         |
| Abort       | `F7`                   | `main.py:69`         |

If your monitor is not 60 Hz, every frame-count config value drifts
proportionally — there is no per-monitor recalibration.

## Procedure flow

Per block (`SQUARES` then `CIRCLES`):

1. Instruction screen.
2. **Training** — `NUpNDown` staircase, ±1 frame, terminates after
   `MAX_REVS` reversals. Trial-by-trial feedback shown.
3. **Converged SOA** = `int(mean(reversal_SOAs[:0.6*N]))` —
   first 60% of reversal points (`main.py:183`).
4. **Experiment** — `NO_TRIALS` trials at the converged SOA. No feedback.
5. End-of-session: `RESTTIME` seconds of fixation cross with `REST_START`
   / `REST_END` triggers (for IAF / resting EEG).

### Single trial

| Stage      | Duration              | Trigger        |
|------------|-----------------------|----------------|
| Fixation   | `TRAIN_FIX_TIME` or `EXP_FIX_TIME` frames | `FIX_START`   |
| Stimulus   | `SOA` frames          | `TRIAL_START`  |
| Mask       | `MTIME` frames        | —              |
| Response   | up to `RTIME` frames  | `TRIAL_ANS` on key |
| Rating     | self-paced, 4 levels (Żadna / Mała / Duża / Całkowita) | — |
| Jitter ITI | 1–2 s (uniform)       | —              |

## Config keys (`configs/{SQUARES,CIRCLES}_config.yaml`)

| Key              | Unit    | Used? | Meaning                                              |
|------------------|---------|-------|------------------------------------------------------|
| `NO_TRIALS`      | trials  | yes   | Experiment-phase trials (post-training).             |
| `START_SOA`      | frames  | yes   | Initial SOA for the staircase.                       |
| `TRAIN_FIX_TIME` | frames  | yes   | Fixation duration during training.                   |
| `EXP_FIX_TIME`   | frames  | yes   | Fixation duration during experiment.                 |
| `MTIME`          | frames  | yes   | Mask presentation duration.                          |
| `RTIME`          | frames  | yes   | Max response window.                                 |
| `RESTTIME`       | **seconds** | yes | End-of-session resting fixation length (note: NOT frames despite the file header comment). |
| `MAX_REVS`       | count   | yes   | Reversals before staircase terminates.               |
| `STEP_UP`        | —       | **no** | Ignored. `NUpNDown` step size hard-defaults to 1.   |
| `STEP_DOWN`      | —       | **no** | Ignored. As above.                                   |
| `FIXTIME` (CIRCLES only) | — | **no** | Ignored. Use `*_FIX_TIME` instead.            |

### Staircase semantics

`NUpNDown(start_val=START_SOA, max_revs=MAX_REVS)` with class defaults
`n_up=3, n_down=1, step_up=1, step_down=1`:

- **3 correct in a row → SOA − 1 frame** (harder).
- **1 incorrect → SOA + 1 frame** (easier).
- Targets ~79.4% accuracy.

To change step size you must edit `main.py:143`, not the YAML.

## Output

`results/{PART_ID}_{NNN}_beh.csv` — one CSV per session, columns:

```
PART_ID, Trial, Stimuli, Training, FIXTIME, MTIME,
Correct, SOA, Level, Reversal, Reversal_count, Latency, Rating
```

`Training` is `1` during staircase, `0` during experiment. During the
experiment phase `Level`, `Reversal`, `Reversal_count` are `'-'`.
`Latency` is `-1.0` on timeout.

`results/{PART_ID}_{NNN}.log` — PsychoPy log (frame rate, errors).

## EEG triggers (parallel port, byte values)

| Value | Event         |
|-------|---------------|
| `0x01`| `REST_START`  |
| `0x02`| `REST_END`    |
| `0x04`| `FIX_START`   |
| `0x08`| `TRIAL_START` |
| `0x10`| `TRIAL_ANS`   |

Each trigger is cleared (`0x00`) ~1 frame after being set.
