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

# GLOBALS
TEXT_SIZE = 30
VISUAL_OFFSET = 90
KEYS = ['left', 'right']

RESULTS = list()
RESULTS.append(['PART_ID', 'Trial', 'Stimuli', 'Training', 'FIXTIME', 'MTIME', 'Correct', 'SOA',
                'Level', 'Reversal', 'Reversal_count', 'Latency', 'Rating'])


class CorrectStim(object):  # Correct Stimulus Enumerator
    LEFT = 1
    RIGHT = 2


# @atexit.register
def save_beh_results():
    with open(join('results', PART_ID + "_" + str(random.choice(range(100, 1000))) + '_beh.csv'), 'w') as beh_file:
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
    msg = visual.TextStim(win, color='grey', text=msg, height=TEXT_SIZE - 10, wrapWidth=SCREEN_RES[0])
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
    info = {'IDENTYFIKATOR': '', u'P\u0141EC': ['M', "K"], 'WIEK': '20'}
    dictDlg = gui.DlgFromDict(dictionary=info, title='Czas detekcji wzrokowej')
    if not dictDlg.OK:
        abort_with_error('Info dialog terminated.')

    # === Scene init ===
    win = visual.Window(SCREEN_RES, fullscr=True, monitor='testMonitor', units='pix', screen=0, color='black')
    event.Mouse(visible=False, newPos=None, win=win)  # Make mouse invisible
    PART_ID = info['IDENTYFIKATOR'] + info[u'P\u0141EC'] + info['WIEK']
    logging.LogFile(join('.', 'results',  f"{PART_ID}_{str(random.choice(range(100, 1000)))}.log"), level=logging.INFO)  # errors logging
    logging.info('FRAME RATE: {}'.format(FRAME_RATE))
    logging.info('SCREEN RES: {}'.format(SCREEN_RES))
    pos_feedb = visual.TextStim(win, text=u'Poprawna odpowied\u017A', color='grey', height=40)
    neg_feedb = visual.TextStim(win, text=u'Niepoprawna odpowied\u017A', color='grey', height=40)
    no_feedb = visual.TextStim(win, text=u'Nie udzieli\u0142e\u015B odpowiedzi', color='grey', height=40)
    show_info(win, join('.', 'messages', 'hello.txt'))

    for proc_version in ['SQUARES','CIRCLES']:
        left_stim = visual.ImageStim(win, image=join('.', 'stims', f'{proc_version}_LEFT.bmp'))
        right_stim = visual.ImageStim(win, image=join('.', 'stims', f'{proc_version}_RIGHT.bmp'))
        mask_stim = visual.ImageStim(win, image=join('.', 'stims', f'{proc_version}_MASK.bmp'))
        # fix_stim = visual.TextStim(win, text='+', height=100, color='grey')
        fix_stim = visual.ImageStim(win, image=join('.', 'stims', 'PRE_STIMULI.bmp'))
        arrow_label = visual.TextStim(win, text=u"\u2190       \u2192", color='grey', height=30,
                                      pos=(0, -200))
        if proc_version == 'SQUARES':
            question = u'Gdzie pojawi\u0142 si\u0119 OBROCONY kwadrat?'
        elif proc_version == 'CIRCLES':
            question = u'Gdzie pojawi\u0142 si\u0119 WI\u0118KSZY okr\u0119g?'
        else:
            raise NotImplementedError(f'Stimulus type: {proc_version} not implemented.')

        question_text = visual.TextStim(win, text=question, color='grey', height=20,
                                      pos=(0, -180))

        # === Load data, configure log ===

        response_clock = core.Clock()
        conf = yaml.load(open(join('.', 'configs', f'{proc_version}_config.yaml')))


        show_info(win, join('.', 'messages', f'{proc_version}_before_training.txt'))
        # === Training ===

        training = NUpNDown(start_val=conf['START_SOA'], max_revs=conf['MAX_REVS'])

        old_rev_count_val = -1
        correct_trials = 0
        for idx, soa in enumerate(training):
            corr, rt, rating = run_trial(conf, fix_stim, left_stim, mask_stim, right_stim, soa, win, arrow_label,
                                 question_text, response_clock)
            training.set_corr(corr)
            level, reversal, revs_count = map(int, training.get_jump_status())
            if old_rev_count_val != revs_count:
                old_rev_count_val = revs_count
                rev_count_val = revs_count
            else:
                rev_count_val = '-'

            RESULTS.append(
                [PART_ID, idx, proc_version, 1, conf['FIXTIME'], conf['MTIME'], int(corr), soa, level, reversal,
                 rev_count_val, rt, rating])

            ### FEEDBACK
            if corr == 1:
                feedb_msg = pos_feedb
                correct_trials += 1
            elif corr == 0:
                feedb_msg = neg_feedb
            else:
                feedb_msg = no_feedb
            for _ in range(30):
                feedb_msg.draw()
                check_exit()
                win.flip()


        # === experiment ===
        experiment = [soa] * conf['NO_TRIALS']

        show_info(win, join('.', 'messages', f'{proc_version}_feedback.txt'))

        for idx in range(idx,conf['NO_TRIALS']+idx):
            corr, rt, rating = run_trial(conf, fix_stim, left_stim, mask_stim, right_stim, soa, win, arrow_label,
                                    question_text, response_clock)
            corr = int(corr)
            correct_trials += corr
            RESULTS.append(
                [PART_ID, idx, proc_version, 0, conf['FIXTIME'], conf['MTIME'], corr, soa, '-', '-',
                    '-', rt, rating])


    # === Cleaning time ===
    save_beh_results()
    logging.flush()
    show_info(win, join('.', 'messages', 'end.txt'))
    win.close()


def run_trial(config, fix_stim, left_stim, mask_stim, right_stim, soa, win, arrow_label,question_text, response_clock):
    trial_type = random.choice([CorrectStim.LEFT, CorrectStim.RIGHT])
    stim = left_stim if trial_type == CorrectStim.LEFT else right_stim
    stim_name = 'left' if trial_type == CorrectStim.LEFT else 'right'
    rt = -1.0
    for _ in range(config['FIXTIME']):  # Fixation octagon
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
        question_text.draw()
        win.flip()
        keys = event.getKeys(keyList=KEYS)
        if keys:
            corr = True if keys[0] == stim_name else False
            rt = response_clock.getTime()
            break
        check_exit()
    # Rating Scale
    
    ratingScale = visual.RatingScale(win, size = 0.8, noMouse=True, 
    markerStart = 2, stretch= 1.4, scale="Okre\u015bl swoj\u0105 pewno\u015b\u0107 co do udzielonej odpowiedzi", acceptPreText= 'Wybierz',choices=["\u017badna", "Ma\u0142a", "Du\u017ca", "Ca\u0142kowita"])
    while ratingScale.noResponse:
        ratingScale.draw()
        win.flip()
    rating = ratingScale.getRating()
    win.flip()
    # break + jitter
    wait_time_in_secs = 1 + random.choice(range(0, 120))/ 60.0
    core.wait(wait_time_in_secs)
    return corr, rt, rating


if __name__ == '__main__':
    PART_ID = ''
    SCREEN_RES = [1920, 1080]
    FRAME_RATE = 60
    main()
