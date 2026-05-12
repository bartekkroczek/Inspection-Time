#!/usr/bin/env python
import atexit
import csv
import random
from datetime import datetime
from os import makedirs
from os.path import abspath, dirname, join

import yaml
from psychopy import visual, event, gui, core
from psychopy import logging as psy_logging   # Aliased: the stdlib `logging` module has a different API.

from Adaptives.NUpNDown import NUpNDown

# GLOBALS
KEYS = ['left', 'right']
SCREEN_RES = (1920, 1080)
FRAME_RATE = 60      # See the CAUTION block in README.md — must match the monitor's refresh rate.
PART_ID = ''         # Populated from the launch dialog; referenced by the atexit save handler.
SESSION_TS = ''      # ISO 8601 session start; shared by log and CSV filenames.

# Resolve filesystem paths relative to this file so the script works regardless
# of the working directory the user launches it from.
BASE_DIR = dirname(abspath(__file__))
RESULTS_DIR = join(BASE_DIR, 'results')
makedirs(RESULTS_DIR, exist_ok=True)

# Conditions to run, in order. Comment out a line to skip a condition.
# Default: CIRCLES only. Uncomment 'SQUARES' to also run the squares block.
CONDITIONS = [
    # 'SQUARES',
    'CIRCLES',
]

CSV_HEADER = ['PART_ID', 'Trial', 'Stimuli', 'Training', 'FIXTIME', 'MTIME', 'Correct', 'SOA',
              'Level', 'Reversal', 'Reversal_count', 'Latency', 'Rating']
RESULTS = [CSV_HEADER]


@atexit.register
def save_beh_results() -> None:
    """Write the behavioural results CSV. Registered as an atexit hook so any
    exit path (normal, F7 abort, raised exception) flushes what was collected.
    Returns without writing when no trials were recorded (only the header row
    is present), so dialog-cancelled sessions do not litter `results/`.
    """
    if len(RESULTS) <= 1:
        psy_logging.flush()
        return
    path = join(RESULTS_DIR, f'{PART_ID}_{SESSION_TS}_beh.csv')
    with open(path, 'w', encoding='utf-8') as beh_file:
        csv.writer(beh_file).writerows(RESULTS)
    psy_logging.flush()


def read_text_from_file(file_name, insert=''):
    """Read a message text file, stripping leading `#` comment lines and
    optionally substituting a `<--insert-->` line with the given *insert*.
    """
    if not isinstance(file_name, str):
        psy_logging.error('Problem with file reading, filename must be a string')
        raise TypeError('file_name must be a string')
    msg = []
    with open(file_name, encoding='utf-8') as data_file:
        for line in data_file:
            if line.startswith('#'):
                continue
            if line.startswith('<--insert-->'):
                if insert:
                    msg.append(insert)
            else:
                msg.append(line)
    return ''.join(msg)


def check_exit(key='f7'):
    """Poll for the abort key; if pressed, raise via abort_with_error()."""
    if event.getKeys(keyList=[key]):
        abort_with_error(f'Experiment finished by user! {key} pressed.')


def show_info(win, file_name, insert='', text_size=20):
    """Render the message in *file_name* full-screen and wait for a keypress."""
    text = read_text_from_file(file_name, insert=insert)
    stim = visual.TextStim(win, color='grey', text=text, height=text_size, wrapWidth=SCREEN_RES[0])
    stim.draw()
    win.flip()
    key = event.waitKeys(keyList=['f7', 'return', 'space'] + KEYS)
    if 'f7' in (key or []):
        abort_with_error('Experiment finished by user on info screen! F7 pressed.')
    win.flip()


def abort_with_error(err):
    """Log a critical message and raise. Used for user aborts (F7) and for
    unrecoverable configuration errors.
    """
    psy_logging.critical(err)
    raise Exception(err)


def _corr_to_csv(corr):
    """Map tri-state correctness (True / False / None) to a CSV value (1 / 0 / NA)."""
    if corr is True:
        return 1
    if corr is False:
        return 0
    return 'NA'


def main():
    # PART_ID and SESSION_TS are mutated here but read by the atexit handler,
    # so they must remain module globals.
    global PART_ID, SESSION_TS

    # === Dialog popup ===
    sex_key = 'PŁEC'
    info = {'IDENTYFIKATOR': '', sex_key: ['M', 'K'], 'WIEK': '20'}
    dialog = gui.DlgFromDict(dictionary=info, title='Czas detekcji wzrokowej')
    if not dialog.OK:
        abort_with_error('Info dialog terminated.')
    if not info['IDENTYFIKATOR'].strip():
        abort_with_error('IDENTYFIKATOR (participant ID) is required and cannot be empty.')

    PART_ID = info['IDENTYFIKATOR'] + info[sex_key] + info['WIEK']
    SESSION_TS = datetime.now().strftime('%Y-%m-%dT%H%M%S')

    # === Scene init ===
    win = visual.Window(SCREEN_RES, fullscr=True, monitor='testMonitor', units='pix', screen=0, color='black')
    event.Mouse(visible=False, win=win)
    psy_logging.LogFile(join(RESULTS_DIR, f'{PART_ID}_{SESSION_TS}.log'),
                        level=psy_logging.INFO)
    psy_logging.info(f'FRAME RATE: {FRAME_RATE}')
    psy_logging.info(f'SCREEN RES: {SCREEN_RES}')

    for proc_version in CONDITIONS:
        # === Load config ===
        # Loaded first so the stim construction below can be parameterised by it.
        with open(join(BASE_DIR, 'configs', f'{proc_version}_config.yaml'), encoding='utf-8') as conf_file:
            conf = yaml.safe_load(conf_file)
        response_clock = core.Clock()

        # Per-condition image stimuli.
        left_stim = visual.ImageStim(win, image=join(BASE_DIR, 'stims', f'{proc_version}_LEFT.bmp'))
        right_stim = visual.ImageStim(win, image=join(BASE_DIR, 'stims', f'{proc_version}_RIGHT.bmp'))
        mask_stim = visual.ImageStim(win, image=join(BASE_DIR, 'stims', f'{proc_version}_MASK.bmp'))

        # On-screen text stimuli; sizes and offsets come from the YAML config.
        fix_stim = visual.TextStim(win, text='+', height=conf['FIX_HEIGHT'], color='grey')
        # Explicit font: the default sans-serif lacks the Arrows Unicode block
        # on some Linux installs and the glyphs would render as tofu boxes.
        arrow_label = visual.TextStim(win, text='←       →', color='grey', font='DejaVu Sans',
                                      height=conf['ARROW_HEIGHT'], pos=(0, conf['ARROW_POS_Y']))
        if proc_version == 'SQUARES':
            question = 'Gdzie pojawił się OBROCONY kwadrat?'
        elif proc_version == 'CIRCLES':
            question = 'Gdzie pojawił się WIĘKSZY okręg?'
        else:
            raise NotImplementedError(f'Stimulus type: {proc_version} not implemented.')
        question_text = visual.TextStim(win, text=question, color='grey',
                                        height=conf['QUESTION_HEIGHT'], pos=(0, conf['QUESTION_POS_Y']))

        # Per-trial feedback stimuli.
        pos_feedb = visual.TextStim(win, text='Poprawna odpowiedź', color='grey',
                                    height=conf['FEEDBACK_HEIGHT'])
        neg_feedb = visual.TextStim(win, text='Niepoprawna odpowiedź', color='grey',
                                    height=conf['FEEDBACK_HEIGHT'])
        no_feedb = visual.TextStim(win, text='Nie udzieliłeś odpowiedzi', color='grey',
                                   height=conf['FEEDBACK_HEIGHT'])

        # === Training ===
        show_info(win, join(BASE_DIR, 'messages', f'{proc_version}_before_training.txt'),
                  text_size=conf['MSG_TEXT_SIZE'])
        fix_time = conf['FIX_TIME']
        if len(conf['TRAINING_TRIALS']) != len(conf['TRAINING_SOAS']):
            abort_with_error(
                f"{proc_version} config: TRAINING_TRIALS and TRAINING_SOAS must have the same length "
                f"(got {len(conf['TRAINING_TRIALS'])} and {len(conf['TRAINING_SOAS'])}).")
        idx = 0
        for no_trials, soa in zip(conf['TRAINING_TRIALS'], conf['TRAINING_SOAS']):
            for idx in range(idx + 1, no_trials + idx + 1):
                corr, rt, rating = run_trial(conf, fix_stim, left_stim, mask_stim, fix_time, right_stim, soa, win,
                                             arrow_label, question_text, response_clock)
                RESULTS.append(
                    [PART_ID, idx, proc_version, 'training', fix_time, conf['MTIME'], _corr_to_csv(corr), soa,
                     '-', '-', '-', rt, rating])

                # Feedback.
                if corr is True:
                    feedb_msg = pos_feedb
                elif corr is False:
                    feedb_msg = neg_feedb
                else:                                  # corr is None: participant did not respond in time.
                    feedb_msg = no_feedb
                for _ in range(conf['FEEDBACK_DURATION']):
                    feedb_msg.draw()
                    check_exit()
                    win.flip()
                win.flip()

                # Break + jitter (REST_TIME_RANGE is inclusive of both bounds).
                low, high = conf['REST_TIME_RANGE']
                wait_time_in_secs = random.choice(range(low, high + 1)) / FRAME_RATE
                core.wait(wait_time_in_secs)

        # === Experiment ===
        experiment = NUpNDown(start_val=conf['START_SOA'], max_revs=conf['MAX_REVS'],
                              n_up=conf['N_UP'], n_down=conf['N_DOWN'])
        old_rev_count_val = -1
        show_info(win, join(BASE_DIR, 'messages', f'{proc_version}_feedback.txt'),
                  text_size=conf['MSG_TEXT_SIZE'])
        for idx, soa in enumerate(experiment, 1):
            corr, rt, rating = run_trial(conf, fix_stim, left_stim, mask_stim, fix_time, right_stim, soa, win,
                                         arrow_label, question_text, response_clock)
            # Timeouts (corr is None) are fed to the staircase as wrong answers.
            # This is conservative: an inattentive participant moves the SOA up
            # (easier) rather than stalling convergence. The CSV column 'Correct'
            # records the distinction as NA so analysis can separate the cases.
            experiment.set_corr(corr is True)
            level, reversal, revs_count = map(int, experiment.get_jump_status())
            if old_rev_count_val != revs_count:
                old_rev_count_val = revs_count
                rev_count_val = revs_count
            else:
                rev_count_val = '-'
            RESULTS.append(
                [PART_ID, idx, proc_version, 'exp', fix_time, conf['MTIME'], _corr_to_csv(corr), soa, level, reversal,
                 rev_count_val, rt, rating])

            # Break + jitter (REST_TIME_RANGE is inclusive of both bounds).
            low, high = conf['REST_TIME_RANGE']
            wait_time_in_secs = random.choice(range(low, high + 1)) / FRAME_RATE
            core.wait(wait_time_in_secs)

    # === Cleanup ===
    psy_logging.flush()
    show_info(win, join(BASE_DIR, 'messages', 'end.txt'))
    win.close()


def run_trial(config, fix_stim, left_stim, mask_stim, fix_time, right_stim, soa, win, arrow_label, question_text,
              response_clock):
    """Run a single trial and return (corr, rt, rating).

    corr is True / False / None where None indicates a no-response timeout.
    rt  is the response latency in seconds (or -1.0 on timeout).
    """
    stim_name = random.choice(['left', 'right'])
    stim = left_stim if stim_name == 'left' else right_stim
    rt = -1.0

    for _ in range(fix_time):                          # Fixation cross.
        fix_stim.draw()
        win.flip()
        check_exit()
    for _ in range(soa):                               # Stimulus presentation.
        stim.draw()
        win.flip()
        check_exit()
    for _ in range(config['MTIME']):                   # Mask presentation.
        mask_stim.draw()
        win.flip()
        check_exit()

    corr = None                                        # Remains None on timeout.
    win.callOnFlip(response_clock.reset)
    event.clearEvents()
    for _ in range(config['RTIME']):                   # Response window.
        arrow_label.draw()
        question_text.draw()
        win.flip()
        keys = event.getKeys(keyList=KEYS)
        if keys:
            corr = keys[0] == stim_name
            rt = response_clock.getTime()
            break
        check_exit()

    # Rating scale is not currently collected; the CSV reserves the column.
    rating = '-'
    win.flip()
    return corr, rt, rating


if __name__ == '__main__':
    main()
