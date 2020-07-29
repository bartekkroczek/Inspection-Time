#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import csv
import yaml
import codecs
import atexit
import random
import pylink

from os.path import join
from psychopy import visual, core, logging, event, gui, monitors
from EyeLinkCoreGraphicsPsychoPy import EyeLinkCoreGraphicsPsychoPy

DEBUG = False

@atexit.register
def save_beh_results():
    global PART_ID
    with open(join('results', 'beh', PART_ID + '_beh.csv'), 'w') as beh_file:
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
    if len(stop) > 0:
        logging.critical(
            'Experiment finished by user! {} pressed.'.format(key))
        exit(1)


def show_info(win, file_name, insert=''):
    """
    Clear way to show info message into screen.
    :param win:
    :return:
    """
    msg = read_text_from_file(file_name, insert=insert)
    msg = visual.TextStim(win, color='black', text=msg, height=20)
    msg.draw()
    win.flip()
    key = event.waitKeys(keyList=['f7', 'return', 'space'])
    if key == ['f7']:
        abort_with_error(
            'Experiment finished by user on info screen! F7 pressed.')
    flip_time = win.flip()
    return flip_time


def abort_with_error(err):
    logging.critical(err)
    raise Exception(err)


class StimulusCanvas(object):
    def __init__(self, win, figs_desc, scale=1.0, frame_color=u'crimson', pos=None):
        self._figures = list()
        self._frame = visual.Rect(
            win, width=375 * scale, height=375 * scale, lineColor=frame_color, lineWidth=5)
        inner_shift = 90 * scale
        shifts = [(-inner_shift, inner_shift),
                  (inner_shift, inner_shift), (0, -inner_shift)]
        for fig_desc, inner_shift in zip(figs_desc, shifts):
            fig = "{hat}_{sweater}_{arms}_{legs}.png".format(**fig_desc)
            fig = join(STIMULI_PATH, fig)
            fig = visual.ImageStim(win, fig, interpolate=True)
            fig.size = fig.size[0] * scale * 0.17, fig.size[1] * scale * 0.17
            fig.pos += inner_shift
            self._figures.append(fig)
        if pos:
            self.setPos(pos)

    def setFrameColor(self, color):
        self._frame.setLineColor(color)

    def setAutoDraw(self, draw):
        self._frame.setAutoDraw(draw)
        [x.setAutoDraw(draw) for x in self._figures]

    def draw(self):
        self._frame.draw()
        [x.draw() for x in self._figures]

    def setPos(self, pos):
        self._frame.pos += pos
        for fig in self._figures:
            fig.pos += pos


def runTrial(item, feedb, trial_index):

    A = StimulusCanvas(win=win, figs_desc=item['A'], scale=SCALE,
                       frame_color=u'black', pos=(-790, 370))
    B = StimulusCanvas(win=win, figs_desc=item['B'], scale=SCALE,
                       frame_color=u'black', pos=(-790, 7))
    C = StimulusCanvas(win=win, figs_desc=item['C'], scale=SCALE,
                       frame_color=u'black', pos=(-790, -353))
    figures = [A, B, C]
    solutions_order = item['order']
    solutions = [StimulusCanvas(win, item['D' + str(i)], SCALE, frame_color='dimgray') for i in solutions_order]
    [solution.setPos((150, 0)) for solution in solutions]
    shifts = [(-476,  182),
              (   0,  182),
              ( 476,  182),
              (-476, -182),
              (   0, -182),
              ( 476, -182)]

    for solution, shift in zip(solutions, shifts):
        solution.setPos(shift)
    figures.extend(solutions)
    mouse = event.Mouse()
    choosed_option = -1
    ans_accept = False
    rt = -1
    trial_start = True
    stime = None

    # put the tracker in idle mode before we transfer the backdrop image
    tk.setOfflineMode()
    pylink.pumpDelay(100)
    pid = PART_ID.split('_')[0]
    bgImage = join('.','results', 'screens',f'scr_{pid}',  f"scr_{trial_index}.png")

    # send the standard "TRIALID" message to mark the start of a trial
    tk.sendMessage('TRIALID %d' % trial_index)

    # record_status_message : show some info on the Host PC - OPTIONAL
    tk.sendCommand("record_status_message 'TRIAL: %d'" % trial_index) 

    # drift check
    # the doDriftCorrect() function requires target position in integers
    # the last two arguments: draw_target (1-default, 0-user draw the target then call this function)
    #                         allow_setup (1-press ESCAPE to recalibrate, 0-not allowed)
    try:
        err = tk.doDriftCorrect(int(scnWidth/2), 0, 1, 1)
    except:
        tk.doTrackerSetup()

    # put the tracker in idle mode before we start recording
    tk.setOfflineMode()
    pylink.pumpDelay(100)

    # start recording
    # arguments: sample_to_file, events_to_file, sample_over_link, event_over_link (1-yes, 0-no)

    err = tk.startRecording(1, 1, 1, 1)
    pylink.pumpDelay(100)  # wait for 100 ms to cache some samples

    # which eye(s) are available: 0-left, 1-right, 2-binocular
    eyeTracked = tk.eyeAvailable()
    if eyeTracked == 2:  # use right eye data if tracking binocularly
        eyeTracked = 1

    tk.sendMessage('image_onset')
    # # send over a message to specify where the image is stored relative to the EDF data file
    tk.sendMessage('!V IMGLOAD CENTER %s %d %d' %
                   (bgImage, int(scnWidth/2), int(scnHeight/2)))

    # # store interest area info in the EDF data file, if needed
    # # here we set a rectangular IA, just to illustrate how the IA messages look like
    # # format: !V IAREA RECTANGLE <id> <left> <top> <right> <bottom> [label string]
    # # see Data Viewer User Manual, Section 7: Protocol for EyeLink Data to Viewer Integration
    tk.sendMessage('!V IAREA RECTANGLE %d %d %d %d %d %s' % (1, 20,  25, 320,  315, 'A'))
    tk.sendMessage('!V IAREA RECTANGLE %d %d %d %d %d %s' % (2, 20, 385, 320,  680, 'B'))
    tk.sendMessage('!V IAREA RECTANGLE %d %d %d %d %d %s' % (3, 20, 745, 320, 1040, 'C'))

    tk.sendMessage('!V IAREA RECTANGLE %d %d %d %d %d %s' % (4,  485, 205,  785, 505, solutions_order[0]))
    tk.sendMessage('!V IAREA RECTANGLE %d %d %d %d %d %s' % (5,  960, 205, 1255, 505, solutions_order[1]))
    tk.sendMessage('!V IAREA RECTANGLE %d %d %d %d %d %s' % (6, 1435, 205, 1735, 505, solutions_order[2]))
    tk.sendMessage('!V IAREA RECTANGLE %d %d %d %d %d %s' % (7,  485, 570,  785, 870, solutions_order[3]))
    tk.sendMessage('!V IAREA RECTANGLE %d %d %d %d %d %s' % (8,  960, 570, 1255, 870, solutions_order[4]))
    tk.sendMessage('!V IAREA RECTANGLE %d %d %d %d %d %s' % (9, 1435, 570, 1735, 870, solutions_order[5]))

    # show the image indefinitely until a key is pressed; move the Aperture to follow the gaze
    [fig.setAutoDraw(True) for fig in figures]
    [lab.setAutoDraw(True) for lab in LABELS]
    event.clearEvents()  # clear cached (keyboard/mouse etc.) events if there are any
    timer = core.CountdownTimer(item['time'])
    win.callOnFlip(timer.reset, item['time'])
    tk.sendMessage("trial_run")
    while timer.getTime() > 0.0 and not ans_accept:
        for trial_index, sol in zip(solutions_order, solutions):
            if mouse.isPressedIn(accept_box) and choosed_option != -1:
                ans_accept = True
                rt = item['time'] - timer.getTime()
                break
            if mouse.isPressedIn(sol._frame):
                sol.setFrameColor('green')
                choosed_option = trial_index
            if choosed_option != trial_index:# close the EDF data file and put the tracker in idle mode
                if sol._frame.contains(mouse):
                    sol.setFrameColor('yellow')
                else:
                    sol.setFrameColor('gray')
        time_left_label.setText(
            '{} sekund.'.format(int(timer.getTime())))
        flip_time = win.flip()
        if trial_start:
            trial_start = False
            stime = flip_time
        check_exit()
    if choosed_option != -1:
        choosed_option = 'D' + str(choosed_option)
    corr = choosed_option == 'D6'  # Teraz corr == D6 ? Bylo == D1
    [fig.setAutoDraw(False) for fig in figures]
    [lab.setAutoDraw(False) for lab in LABELS]
    flip_time = win.flip()
    etime = flip_time

    tk.sendMessage('trial_finished')

    # clear the screen
    win.flip()
    tk.sendMessage('blank_screen')

    # stop recording
    tk.stopRecording()
    # clear the host display, this command is needed if you have backdrop image on the Host
    tk.sendCommand('clear_screen 0')
    # send over the standard 'TRIAL_RESULT' message to mark the end of trial
    tk.sendMessage('TRIAL_RESULT 0')
    if feedb:
        next_message = visual.TextStim(win, text=u'Aby kontunouwać, naciśnij spację.', height=30, color = u'crimson', pos=(20, -370))
        if choosed_option == -1:
            message = visual.TextStim(win, text=u'Nie udzieliłeś odpowiedzi.', color=u'crimson', height=20)
            message.draw()
            win.flip()
            event.waitKeys(keyList=['space'])
            win.flip()
        else:
            if corr:
                message = visual.TextStim(win, text=u'Brawo. Odpowiedź poprawna.', color=u'crimson', height=20)
            elif not corr:
                message = visual.TextStim(win, text=u'Odpowiedź niepoprawna. Poprawną oznaczamy kolorem zielonym, a twoją: żółtym', color=u'crimson', height=20, wrapWidth=1800, pos=(0, 0))

            message.draw()
            next_message.draw()
            for trial_index, sol in zip(solutions_order, solutions):
                if trial_index == int(choosed_option[-1]):
                    sol.setFrameColor('yellow')
                if trial_index == 6:
                    sol.setFrameColor('green')
            [fig.setAutoDraw(True) for fig in figures]
            [lab.setAutoDraw(True) for lab in LABELS]
            win.flip()
            event.waitKeys(keyList=['space'])
            [fig.setAutoDraw(False) for fig in figures]
            [lab.setAutoDraw(False) for lab in LABELS]
            win.flip()

    item['wait'] = 3
    item['feedb'] = feedb
    item['rel'] = rel_dict[item['type']][choosed_option]
    item['answers'] = solutions_order
    RESULTS.append([PART_ID, stime, etime, choosed_option, ans_accept, rt, corr, item['time'], item['rel'], item['feedb'],
                    item['wait'], item['exp'], item['type'], item['answers']])
    core.wait(item['wait'])

# init

rel_dict = {}
rel_dict['v1'] = {'D1': .166, 'D2': .333, 'D3': .5 , 'D4': .666 , 'D5': .833, 'D6':1, -1: 0}
rel_dict['v2'] = {'D1': 0, 'D2': .333, 'D3': .333 , 'D4': .666 , 'D5': .666, 'D6':1, -1: 0}

STIMULI_PATH = join('.', 'stimulus')
VISUAL_OFFSET = 150
TEXT_SIZE = 25
SCALE = 0.8
RESULTS = [['session_id', 'start_time', 'end_time', 'choosed_option', 'ans_accept',
            'rt', 'corr', 'time', 'rel', 'feedb', 'wait', 'exp', 'type', 'answers']]


info = {'Part_id': '', 'Part_age': '20', 'Part_sex': ['MALE', "FEMALE"],
        'ExpDate': '06.2016'}
dictDlg = gui.DlgFromDict(dictionary=info, title='FAN', fixed=['ExpDate'])
if not dictDlg.OK:
    exit(1)

PART_ID = f"{info['Part_id']}_{info['Part_age']}_{info['Part_sex'][0]}"
logging.LogFile(join('results', 'log', PART_ID + '.log'), level=logging.INFO)
scnWidth, scnHeight = SCREEN_RES = [1920, 1080]

if DEBUG:
    tk = pylink.EyeLink(None)  # Simulation mode
else:
    tk = pylink.EyeLink('100.1.1.1')

dataFileName = f"{PART_ID}.EDF"
tk.openDataFile(dataFileName)
# add personalized data file header (preamble text)
tk.sendCommand(f"add_file_preamble_text 'FAN ECO EyeTracking EXP PART_ID: {PART_ID}'")


# we need to set monitor parameters to use the different PsychoPy screen "units"
mon = monitors.Monitor('myMonitor', width=53.0, distance=100.0)
mon.setSizePix(SCREEN_RES)
win = visual.Window(SCREEN_RES, fullscr=(not DEBUG), monitor=mon, color='Gainsboro', winType='pyglet', units='pix', allowStencil=True)
genv = EyeLinkCoreGraphicsPsychoPy(tk, win)

# set background and foreground colors, (-1,-1,-1)=black, (1,1,1)=white
genv.backgroundColor = (0,0,0)
genv.foregroundColor = (-1,-1,-1)
genv.enableBeep = True
genv.targetSize = 32
genv.calTarget = 'circle'

pylink.openGraphicsEx(genv)

tk.setOfflineMode()
pylink.pumpDelay(100)

# see Eyelink Installation Guide, Section 8.4: Customizing Your PHYSICAL.INI Settings
tk.sendCommand("screen_pixel_coords = 0 0 %d %d" % (scnWidth-1, scnHeight-1))
# save screen resolution in EDF data, so Data Viewer can correctly load experimental graphics
tk.sendMessage("DISPLAY_COORDS = 0 0 %d %d" % (scnWidth-1, scnHeight-1))
# sampling rate, 250, 500, 1000, or 2000; this command is not supported for EyeLInk II/I trackers
tk.sendCommand("sample_rate 1000")
# detect eye events based on "GAZE" (or "HREF") data
tk.sendCommand("recording_parse_type = GAZE")
# Saccade detection thresholds: 0-> standard/coginitve, 1-> sensitive/psychophysiological
tk.sendCommand("select_parser_configuration 0")
# choose a calibration type, H3, HV3, HV5, HV13 (HV = horiztonal/vertical),
tk.sendCommand("calibration_type = HV9")


# tracker hardware, 1-EyeLink I, 2-EyeLink II, 3-Newer models (1000/1000Plus/Portable DUO)
hardware_ver = tk.getTrackerVersion()

# tracking software version
software_ver = 0
if hardware_ver == 3:
    tvstr = tk.getTrackerVersionString()
    vindex = tvstr.find("EYELINK CL")
    software_ver = float(tvstr.split()[-1])

# sample and event data saved in EDF data file
tk.sendCommand(
    "file_event_filter = LEFT,RIGHT,FIXATION,SACCADE,BLINK,MESSAGE,BUTTON,INPUT")
if software_ver >= 4:
    tk.sendCommand(
        "file_sample_data  = LEFT,RIGHT,GAZE,GAZERES,PUPIL,HREF,AREA,STATUS,HTARGET,INPUT")
else:
    tk.sendCommand(
        "file_sample_data  = LEFT,RIGHT,GAZE,GAZERES,PUPIL,HREF,AREA,STATUS,INPUT")

# sample and event data available over the link
tk.sendCommand(
    "link_event_filter = LEFT,RIGHT,FIXATION,FIXUPDATE,SACCADE,BLINK,BUTTON,INPUT")
if software_ver >= 4:
    tk.sendCommand(
        "link_sample_data  = LEFT,RIGHT,GAZE,GAZERES,PUPIL,HREF,AREA,STATUS,HTARGET,INPUT")
else:
    tk.sendCommand(
        "link_sample_data  = LEFT,RIGHT,GAZE,GAZERES,PUPIL,HREF,AREA,STATUS,INPUT")

msg = visual.TextStim(win, text='Press ENTER twice to calibrate the tracker\n' +
                                'In the task, press any key to end a trial', color='black')
msg.draw()
win.flip()
event.waitKeys()

tk.doTrackerSetup()

to_label = visual.TextStim(win, text=u'Do:', color=u'black', height=40, pos=(-800, 190))
is_like_label = visual.TextStim(win, text=u'Jest jak:', color=u'black', height=40, pos=(-800, -170))
line = visual.Line(win, start=(-600, -550), end=(-600, 550), lineColor=u'black', lineWidth=8)
to_choose_one_label = visual.TextStim(win, text=u'Do: (Wybierz jedno)', color=u'black', height=40, pos=(0, 400), wrapWidth=700)
time_left_label = visual.TextStim(win, text=u'16 sekund.', height=40, color=u'black', pos=(-300, -470))
accept_box = visual.Rect(win, fillColor=u'dimgray', width=600, height=100, pos=(660, -490), lineColor=u'black')
accept_label = visual.TextStim(win, text=u'Zaakceptuj', height=50, color=u'ghostwhite', pos=(700, -490))
LABELS = [to_label, is_like_label, line, to_choose_one_label, time_left_label, accept_box, accept_label]

with open(join('.', 'results', 'trials', f'trials_{info["Part_id"]}.yaml'), 'r') as f:
    trials = yaml.safe_load(f)

training = trials['training']
experiment = trials['exp']
instr_1 = visual.ImageStim(win, image=join('.', 'messages', 'instruction_1.jpg'))
instr_2 = visual.ImageStim(win, image=join('.', 'messages', 'instruction_2.jpg'))

instr_1.draw()
win.flip()
event.waitKeys()
instr_2.draw()
win.flip()
event.waitKeys()
event.clearEvents()
# training
show_info(win, join('.', 'messages', 'instruction1.txt'))
for idx, trial in enumerate(training):
    trial['time'] = 120
    trial['exp'] = False
    runTrial(item=trial, feedb=True, trial_index=idx)
# experiment
show_info(win, join('.', 'messages', 'instruction2.txt'))
for idx, trial in enumerate(experiment, len(training)):
    trial['time'] = 120
    trial['exp'] = True
    runTrial(item=trial, feedb=False, trial_index=idx)

show_info(win, join('.', 'messages', 'end.txt'))


# close the EDF data file and put the tracker in idle mode
tk.setOfflineMode()
pylink.pumpDelay(100)
tk.closeDataFile()

# download EDF file to Display PC and put it in local folder ('edfData')
msg = 'EDF data is transfering from EyeLink Host PC...'
edfTransfer = visual.TextStim(win, text=msg, color='black')
edfTransfer.draw()
win.flip()
pylink.pumpDelay(500)

# make sure the 'edfData' folder is there, create one if not
dataFolder = join('.', 'results', 'edfData')
if not os.path.exists(dataFolder):
    os.makedirs(dataFolder)
tk.receiveDataFile(dataFileName, dataFolder + os.sep + dataFileName)


# clean
save_beh_results()
tk.close()
logging.flush()
core.quit()
window.close()
