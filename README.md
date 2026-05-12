# Inspection-Time

A PsychoPy-based **Inspection Time** experiment measuring the minimum stimulus
onset asynchrony (SOA) at which a participant can still reliably make a forced-
choice visual judgement. Threshold is estimated with an adaptive
**N-up-N-down** staircase. Two conditions are run back-to-back:

| Condition   | Task                                              |
|-------------|---------------------------------------------------|
| `SQUARES`   | Which side shows the **rotated** square?          |
| `CIRCLES`   | Which side shows the **larger** circle?           |

[![Demo Video](https://img.youtube.com/vi/C44MOs_Y-XE/0.jpg)](https://www.youtube.com/watch?v=C44MOs_Y-XE)

---

> [!CAUTION]
> ## REQUIRES A 60 Hz DISPLAY — NO EXCEPTIONS
>
> **Every timing value in this experiment is specified in video frames, not
> milliseconds.** The script hard-codes `FRAME_RATE = 60` (`main.py`) and does
> **not** measure or adapt to your monitor's actual refresh rate.
>
> If you run this on a 75 Hz, 120 Hz, 144 Hz, or variable-refresh display:
>
> - **Every SOA, mask, fixation, and response window will be wrong.**
> - The staircase will converge on a meaningless threshold.
> - Collected data will be **silently corrupted** — no error is raised.
>
> **Before every session you MUST:**
>
> 1. Confirm the monitor is set to exactly **60 Hz** in the OS display settings.
> 2. Disable adaptive sync (G-Sync / FreeSync / VRR).
> 3. Disable any "motion smoothing" or frame interpolation.
> 4. Check the `FRAME RATE:` line in the session `.log` file in `results/` —
>    PsychoPy reports the measured refresh rate there. It should read 60.
>
> If your hardware cannot run at 60 Hz, **do not use this code as-is.** Change
> `FRAME_RATE` in `main.py` and recompute *every* frame count in both YAML
> configs to preserve the intended millisecond durations.

---

## Requirements

- Python 3.8+
- [PsychoPy](https://www.psychopy.org/) (`visual`, `event`, `core`, `gui`, `logging`)
- PyYAML
- **A 60 Hz display.** See the caution box above — this is a hard requirement,
  not a recommendation.

Install with:

```bash
pip install psychopy pyyaml
```

## Running

```bash
python main.py
```

A dialog appears asking for:

- `IDENTYFIKATOR` — participant ID (any string)
- `PŁEC` — sex (`M` / `K`)
- `WIEK` — age

These are concatenated into `PART_ID` (e.g. `S01M22`) and used to name the
output files.

**Abort key:** `F7` — press at any time to stop the experiment cleanly.
Already-collected trials are still saved by the `atexit` handler.

## Procedure

By default the experiment runs **CIRCLES only**. To also run SQUARES, see
[Running only one condition](#running-only-one-condition).

1. Hello message
2. CIRCLES — training (with feedback) + adaptive experiment
3. *(SQUARES — disabled by default; enable in `main.py` if needed)*
4. End message

Each trial: fixation `+` → stimulus pair (SOA frames) → mask (280 ms) →
response window → jittered blank.

---

## Configuration

There are **two** config files, one per condition, in `configs/`:

- `configs/SQUARES_config.yaml`
- `configs/CIRCLES_config.yaml`

Both share the same schema. **All time values are in video frames** (60 Hz → 1
frame ≈ 16.67 ms).

> [!WARNING]
> The frame-to-millisecond conversion below is only valid at **60 Hz**. See
> the caution box at the top of this README before changing displays.

Shared schema (annotated):

```yaml
# All values in no. of frames.
TRAINING_TRIALS: [ ... ]      # n trials per training block
TRAINING_SOAS:   [ ... ]      # SOA used in each training block
# ^ these two lists MUST be the same length — asserted at runtime

START_SOA: <int>              # initial SOA for the adaptive staircase
FIX_TIME:  <int>              # fixation cross duration
MTIME:     <int>              # mask duration
RTIME:     <int>              # max response time
RESTTIME:  <int>              # currently unused
REST_TIME_RANGE: [ <int>, <int> ]  # inter-trial jitter range, in frames

MAX_REVS: <int>               # reversals before the staircase terminates
N_UP:     <int>               # correct-in-a-row before SOA decreases (harder)
N_DOWN:   <int>               # incorrect-in-a-row before SOA increases (easier)
```

The YAML files themselves are commented — open
`configs/SQUARES_config.yaml` / `configs/CIRCLES_config.yaml` to see the
current values and per-field documentation.

### Field reference

| Field             | Meaning                                                                 |
|-------------------|-------------------------------------------------------------------------|
| `TRAINING_TRIALS` | List of training-block sizes. Each block is run with the matching SOA. |
| `TRAINING_SOAS`   | SOA (frames) for each training block. Must match `TRAINING_TRIALS` length. |
| `START_SOA`       | SOA used on the first trial of the adaptive (experimental) phase.      |
| `FIX_TIME`        | Duration of the fixation cross before each trial.                      |
| `MTIME`           | Duration the mask is shown after stimulus offset.                      |
| `RTIME`           | Maximum time the participant has to respond. Timeout counts as wrong.  |
| `REST_TIME_RANGE` | `[min, max]` frames for the jittered ITI. A random integer from this range is divided by 60 to get seconds. |
| `MAX_REVS`        | Staircase stops after this many reversals. Total trials is **variable**. |
| `N_UP` / `N_DOWN` | Staircase rule. `N_UP` correct in a row → harder; `N_DOWN` wrong in a row → easier. With `N_DOWN = 1` the rule converges on the SOA where the participant is correct with probability *p* satisfying *p^N_UP = 0.5* — so `2/1` ≈ 71%, `3/1` ≈ 79%. |

### Running only one condition

The list of conditions to run is defined at the top of `main.py`. **The
default is CIRCLES only** — `'SQUARES'` is commented out:

```python
CONDITIONS = [
    # 'SQUARES',
    'CIRCLES',
]
```

To **also run SQUARES**, uncomment the line:

```python
CONDITIONS = [
    'SQUARES',
    'CIRCLES',
]
```

The same trick works to run SQUARES only, or to change the order. Save the
file and run `python main.py` as usual — no other changes are needed.

### Why the two configs differ

Size discrimination (`CIRCLES`) is perceptually harder than the rotated-square
task, so the CIRCLES config:

- starts the staircase at a longer SOA (`START_SOA: 10` vs `6`),
- uses longer training SOAs (`[20, 10]` vs `[12, 6]`),
- uses a stricter `3-down-1-up` rule (`N_UP: 3`) instead of `2-down-1-up`,
  targeting a higher accuracy criterion (~79% vs ~71%).

The stricter CIRCLES staircase will, on average, run more trials per
reversal — expect the CIRCLES block to take noticeably longer than SQUARES.
Tune these per condition if you replace the stimuli.

---

## Stimuli and messages

- `stims/{SQUARES,CIRCLES}_{LEFT,RIGHT,MASK}.bmp` — stimulus images.
  Replace these to change the task; filenames must stay the same.
- `messages/{SQUARES,CIRCLES}_before_training.txt` — instructions shown before
  each training block (Polish).
- `messages/{SQUARES,CIRCLES}_feedback.txt` — message shown before the
  experimental block.
- `messages/end.txt` — final screen.

Lines starting with `#` in message files are treated as comments and skipped.
`<--insert-->` is a placeholder that can be filled with a runtime string.

---

## Output

Two files per session are written to `results/`. Both share the same ISO 8601
session timestamp generated at the start of the run, so a behavioural CSV
and its matching PsychoPy log always pair up by filename:

- `{PART_ID}_{YYYY-MM-DDTHHMMSS}_beh.csv` — behavioural data
- `{PART_ID}_{YYYY-MM-DDTHHMMSS}.log` — PsychoPy log (frame rate, screen res, errors)

If the run aborts before any trial is collected (e.g. the launch dialog is
dismissed), no CSV is written.

CSV columns:

```
PART_ID, Trial, Stimuli, Training, FIXTIME, MTIME, Correct, SOA,
Level, Reversal, Reversal_count, Latency, Rating
```

- `Training` is `"training"` for training trials, `"exp"` for the staircase.
- `Correct` is `1` (correct response), `0` (wrong response), or `NA`
  (participant did not respond within `RTIME`). Timeout trials are fed to the
  staircase as if they were wrong — see the comment in `main.py` — but the
  CSV records them distinctly so analysis can separate the two cases.
- `Latency` is `-1` whenever `Correct` is `NA` (no response was made).
- `Reversal` is `1` on the trial where the staircase reverses direction.
- `Rating` is currently inactive — the confidence rating scale is commented
  out in `run_trial` (`main.py`). Re-enable that block if you need it.

---

## Tuning checklist

When adapting the experiment for a new study, change these in order:

1. **Refresh rate (critical)** — confirm the monitor is running at exactly
   60 Hz and that adaptive sync is off. See the caution box at the top of
   this README. Anything other than 60 Hz silently corrupts the data unless
   you also update `FRAME_RATE` in `main.py` *and* recompute every frame
   count in both YAML configs.
2. **Screen resolution** — set `SCREEN_RES` in `main.py` (`__main__` block).
3. **Stimuli** — drop new BMPs into `stims/` with the same names.
4. **Instructions** — edit the files in `messages/`.
5. **Timing / staircase** — tune the two YAML configs.


