#!/usr/bin/env python
# -*- coding: latin-1 -*-
import atexit
import codecs
import csv
import random
from os.path import join

import yaml
from psychopy import visual, event, logging, gui, core

from Adaptives.NUpNDown import NUpNDown
from misc.screen_misc import get_screen_res, get_frame_rate

# GLOBALS
TEXT_SIZE = 30
VISUAL_OFFSET = 90
KEYS = ['left', 'right']

RESULTS = list()
RESULTS.append(['PART_ID', 'Trial', 'Stimuli', 'Training', 'Training_level', 'FIXTIME', 'MTIME', 'Correct', 'SOA',
                'Level', 'Reversal', 'Latency'])


class CorrectStim(object):  # Correct Stimulus Enumerator
    LEFT = 1
    RIGHT = 2


@atexit.register
def save_beh_results():
    with open(join('results', PART_ID + '_beh.csv'), 'w') as beh_file:
        beh_writer = csv.writer(beh_file)
        beh_writer.writerows(RESULTS)
    logging.flush()


def read_text_from_file(file_name, insert=''):
    """
    Method that read message from text file, and optionally add some
    dynamically generated info.
    :param file_name: Name of file to read
    :param insert:
    :return: message
    """
    if not isinstance(file_name, str):
        logging.error('Problem with file reading, filename must be a string')
        raise TypeError('file_name must be a string')
    msg = list()
    with codecs.open(file_name, encoding='utf-8', mode='r') as data_file:
        for line in data_file:
            if not line.startswith('#'):  # if not commented line
                if line.startswith('<--insert-->'):
                    if insert:
                        msg.append(insert)
                else:
                    msg.append(line)
    return ''.join(msg)


def check_exit(key='f7'):
    stop = event.getKeys(keyList=[key])
    if stop:
        abort_with_error('Experiment finished by user! {} pressed.'.format(key))


def show_info(win, file_name, insert=''):
    """
    Clear way to show info message into screen.
    :param win:
    :return:
    """
    msg = read_text_from_file(file_name, insert=insert)
    msg = visual.TextStim(win, color='white', text=msg, height=TEXT_SIZE - 10, wrapWidth=SCREEN_RES['width'])
    msg.draw()
    win.flip()
    key = event.waitKeys(keyList=['f7', 'return', 'space', 'left', 'right'] + KEYS)
    if key == ['f7']:
        abort_with_error('Experiment finished by user on info screen! F7 pressed.')
    win.flip()


def abort_with_error(err):
    logging.critical(err)
    raise Exception(err)


def main():
    global PART_ID  # PART_ID is used in case of error on @atexit, that's why it must be global
    # === Dialog popup ===
    info = {'Part_id': '', 'Part_age': '20', 'Part_sex': ['MALE', "FEMALE"], 'ExpDate': '09.2017'}
    dictDlg = gui.DlgFromDict(dictionary=info, title='Inspection time Visual Lines', fixed=['ExpDate'])
    if not dictDlg.OK:
        abort_with_error('Info dialog terminated.')
    #
    PART_ID = info['Part_id'] + info['Part_sex'] + info['Part_age']
    logging.LogFile('results/' + PART_ID + '.log', level=logging.INFO)  # errors logging

    # === Scene init ===
    win = visual.Window(SCREEN_RES.values(), fullscr=True, monitor='testMonitor', units='pix', screen=0, color='black')
    event.Mouse(visible=False, newPos=None, win=win)  # Make mouse invisible
    FRAME_RATE = get_frame_rate(win)
    left_stim = visual.ImageStim(win, image=join('.', 'stims', 'IP_linie_left.bmp'))
    right_stim = visual.ImageStim(win, image=join('.', 'stims', 'IP_linie_right.bmp'))
    mask_stim = visual.ImageStim(win, image=join('.', 'stims', 'IP_linie_maska.bmp'))
    fix_stim = visual.TextStim(win, text='+', height=3 * TEXT_SIZE, color='white')
    arrow_label = visual.TextStim(win, text=u"\u2190       \u2192", color='white', height=3 * TEXT_SIZE,
                                  pos=(0, -2.5 * VISUAL_OFFSET))

    config = yaml.load(open('config.yaml'))
    experiment = NUpNDown()

    show_info(win, join('.', 'messages', 'before_training.txt'))

    training_reps = 6
    training = [config['Training_level_1']] * training_reps + \
               [config['Training_level_2']] * training_reps + \
               [config['Training_level_3']] * training_reps + \
               [config['Training_level_4']] * training_reps
    response_clock = core.Clock()
    correct_trials = 0
    for idx, soa in enumerate(training):
        corr, rt = run_trial(config, fix_stim, left_stim, mask_stim, right_stim, soa, win, arrow_label, response_clock)
        correct_trials += int(corr)
        RESULTS.append(
            [PART_ID, idx, 'LINES', 1, int(idx / training_reps) + 1, config['FIXTIME'], config['MTIME'], int(corr), soa,
             '-', '-', rt])
    show_info(win, join('.', 'messages', 'feedback.txt'), insert=str(int((float(correct_trials)/len(training))*100)))
    show_info(win, join('.', 'messages', 'after_training.txt'))

    for idx, soa in enumerate(experiment, len(training)):
        corr, rt = run_trial(config, fix_stim, left_stim, mask_stim, right_stim, soa, win, arrow_label, response_clock)
        level, reversal = experiment.get_jump_status()
        RESULTS.append(
            [PART_ID, idx, 'LINES', 0, '-', config['FIXTIME'], config['MTIME'], int(corr), soa, level, int(reversal), rt])

        experiment.set_corr(corr)

    # clear all mess
    save_beh_results()
    logging.flush()
    show_info(win, join('.', 'messages', 'end.txt'))
    win.close()


def run_trial(config, fix_stim, left_stim, mask_stim, right_stim, soa, win, arrow_label, response_clock):
    trial_type = random.choice([CorrectStim.LEFT, CorrectStim.RIGHT])
    stim = left_stim if trial_type == CorrectStim.LEFT else right_stim
    stim_name = 'left' if trial_type == CorrectStim.LEFT else 'right'
    for _ in range(config['FIXTIME']):  # Fixation cross
        fix_stim.draw()
        win.flip()
        check_exit()
    for _ in range(soa):  # Stimulus presentation
        stim.draw()
        win.flip()
        check_exit()
    for _ in range(config['MTIME']):  # Mask presentation
        mask_stim.draw()
        win.flip()
        check_exit()
    corr = False  # Used if timeout
    win.callOnFlip(response_clock.reset)
    event.clearEvents()
    for _ in range(config['RTIME']):  # Time for reaction
        arrow_label.draw()
        win.flip()
        keys = event.getKeys(keyList=KEYS)
        if keys:
            corr = True if keys[0] == stim_name else False
            rt = response_clock.getTime()
            break
        check_exit()
    return corr, rt


if __name__ == '__main__':
    PART_ID = ''
    SCREEN_RES = get_screen_res()
    main()
