#!/usr/bin/env python
# -*- coding: latin-1 -*-
import atexit
import codecs
import csv
import random
from os.path import join
from Adaptives import NUpNDown

from psychopy import visual, core, event, logging

from misc.screen_misc import get_screen_res, get_frame_rate

# GLOBALS
TEXT_SIZE = 30
VISUAL_OFFSET = 90
FIGURES_SCALE = 0.5
HEIGHT_OFFSET = 1.0 * VISUAL_OFFSET
KEYS = ['lctrl', 'rctrl']
LABELS = ['Lewa krotsza', 'Prawa krotsza']
STIM_TIME = 1.1
BREAK_TIME = [0.5, 0.8, 1]
TIMEOUT_TIME = 1.0
RESULTS = list()
RESULTS.append(['NR', 'PART_ID', 'SEX', 'AGE', 'GROUP', 'TRIAL', 'TRIAL_GROUP', 'RT', 'CORR'])


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
    msg = visual.TextStim(win, color='black', text=msg, height=TEXT_SIZE - 10, wrapWidth=SCREEN_RES['width'])
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
    global PART_ID
    info = {'Part_id': '', 'Part_age': '20', 'Part_sex': ['MALE', "FEMALE"], 'ExpDate': '08.2017',
            'Group': ['WK', 'WP', 'NK', 'NP']}
    # dictDlg = gui.DlgFromDict(dictionary=info, title='Szopa LIE', fixed=['ExpDate'])
    # if not dictDlg.OK:
    # abort_with_error('Info dialog terminated.')
    # PART_ID = info['Part_id'] + info['Part_sex'] + info['Part_age']
    # logging.LogFile('results/' + PART_ID + '.log', level=logging.INFO)
    win = visual.Window(SCREEN_RES.values(), fullscr=True, monitor='testMonitor', units='pix', screen=0,
                        color='black')
    event.Mouse(visible=False, newPos=None, win=win)
    FRAME_RATE = get_frame_rate(win)
    left = visual.ImageStim(win, image=join('.', 'stims', 'IP_linie_left.bmp'))
    right = visual.ImageStim(win, image=join('.', 'stims', 'IP_linie_right.bmp'))
    mask = visual.ImageStim(win, image=join('.', 'stims', 'IP_linie_maska.bmp'))
    left.draw()
    win.flip()
    core.wait(2)
    exit()

    response_clock = core.Clock()
    left_label = visual.TextStim(win, text=LABELS[0], color='black', height=TEXT_SIZE,
                                 pos=(-2.5 * VISUAL_OFFSET, -2 * VISUAL_OFFSET))
    right_label = visual.TextStim(win, text=LABELS[1], color='black', height=TEXT_SIZE,
                                  pos=(2.5 * VISUAL_OFFSET, -2 * VISUAL_OFFSET))

    problem_number = 0
    # show_info(win, join('.', 'messages', 'after_training.txt'))
    no_train_trials = 24

    experiment = NUpNDown()

    while not experiment.is_finished():
        trial_soa = experiment.get_next_val()


    show_training = True
    for block in [train_stims, exp_stims]:
        if show_training:
            show_info(win, join('.', 'messages', 'training.txt'))
            show_training = False
        else:
            show_info(win, join('.', 'messages', 'experiment.txt'))
        for trial in block:
            rt = -1
            corr = -1
            stim_label.setText(trial)
            left_label.setAutoDraw(True)
            right_label.setAutoDraw(True)
            event.clearEvents()
            win.callOnFlip(response_clock.reset)
            for _ in range(int(STIM_TIME * FRAME_RATE)):
                stim_label.draw()
                keys = event.getKeys(keyList=KEYS)
                if keys:
                    rt = response_clock.getTime()
                    win.flip()
                    break
                check_exit()
                win.flip()
            if not keys:
                too_slow_label.draw()
                stim_label.draw()
                check_exit()
                win.flip()
                keys = event.waitKeys(keyList=KEYS)
                rt = response_clock.getTime()

            if keys[0] == KEYS[0]:  # Tak, rozpoznaje
                if trial in stims['important']:
                    corr = 1
                else:
                    corr = 0
            else:
                if trial in stims['important']:
                    corr = 0
                else:
                    corr = 1
            left_label.setAutoDraw(False)
            right_label.setAutoDraw(False)
            win.flip()
            core.wait(random.choice(BREAK_TIME))
            problem_number += 1

            if trial in stims['important']:
                trial_group = 'important'
            elif trial in stims['target']:
                trial_group = 'target'
            else:
                trial_group = 'unimportant'
            RESULTS.append([problem_number, info['Part_id'], info['Part_sex'], info['Part_age'], info['Group'],
                            ''.join([x for x in trial if ord(x) < 128]), trial_group, rt, corr])  # collect results

    # clear all mess
    save_beh_results()
    logging.flush()
    show_info(win, join('.', 'messages', 'end.txt'))
    win.close()


if __name__ == '__main__':
    PART_ID = ''
    SCREEN_RES = get_screen_res()
    main()
