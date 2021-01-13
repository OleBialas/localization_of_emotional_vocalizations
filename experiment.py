import slab
import time
from freefield import main
import numpy as np
from pathlib import Path
DIR = Path(__file__).parent.resolve()  # location of the main folder

# global variables for experiment configuration:
# SPEAKERS = main.get_speaker_list(list(range(9, 25)))  # 13 speakers, 24 in the middle, 6 to each side
N_FILES = 30  # number of .wav files that contain the stimuli (per condition)
SAMPLERATE = 48828  # sample rate that the processors run under
NOISE_DUR=1.0

def priming(speakers, kind='positive', n_files=7):  # 'negative', or 'neutral

    if kind not in ('positive', 'negative', 'neutral'):
        raise ValueError('Unknown run type. Should be positive, negative, or neutral.')
    # randomly choose one of the 7 files to play
    file = DIR/"stimuli"/"priming_auditory"/"negative"/f"{np.random.randint(1, n_files+1)}.wav"
    priming_stimulus = slab.Sound.read(str(file)).channel(0)
    # priming_stimulus.level -= 5 * (len(speakers) - 1)  # reduce loudness by 5 dB for each additional speaker
    print("writing sound into buffer ...")
    main.write(tag="priming", value=priming_stimulus.data.flatten(), procs=["RX81", "RX82"])
    main.write(tag="playbuflen", value=priming_stimulus.nsamples, procs=["RX81", "RX82"])
    for index, speaker in speakers.iterrows():  # set the speakers
        main.write(tag=f"chan{index}", value=speaker.channel, procs=speaker.analog_proc)
    input(f'Show {kind} priming to participant and press enter to start playing!')
    main.play(kind="ZbusB")
    main.wait_to_finish_playing()
    for index, speaker in speakers.iterrows():  # "unset" the speakers again
        main.write(tag=f"chan{index}", value=99, procs=speaker.analog_proc)


def block(speaker_seq, file_seq, kind='positive', noise_gain=-10):  # 'negative', or 'neutral'

    if kind not in ('positive', 'negative', 'neutral', 'noise'):
        raise ValueError('Unknown run type. Should be positive, negative, neutral, or noise.')
    folder = DIR / "stimuli" / kind  # the folder where the stimuli are in

    # when starting the block, send a 0 to each speaker
    for speaker in speaker_seq.conditions:
        main.write(tag="chan0", value=speaker.channel, procs=speaker.analog_proc)
        main.write(tag="stim", value=0, procs=speaker.analog_proc)

    for file, speaker in zip(file_seq, speaker_seq):
        print(f"trial number {speaker_seq.this_n} of {speaker_seq.n_trials}")
        if kind != "noise":  # send noise from 5 evenly spaced speakers
            stimulus = slab.Sound.read(folder/f"{file}.wav")  # read random wav
            stimulus = stimulus.resample(SAMPLERATE)
            noise = slab.Sound.whitenoise(duration=stimulus.nsamples, samplerate=48828)  # background noise
            noise.level += noise_gain
            main.write(tag="noise", value=noise.data.flatten(), procs=["RX81", "RX82"])
            noise_speakers = other_speakers(speaker_seq)
            for i, noise_speaker in enumerate(noise_speakers[::3]):
                main.write(tag=f"chan{i+1}", value=noise_speaker.channel, procs=noise_speaker.analog_proc)
        else:
            stimulus = slab.Sound.whitenoise(duration=NOISE_DUR, samplerate=48828)  # background noise
        main.write(tag="playbuflen", value=stimulus.nsamples, procs=speaker.analog_proc)
        main.write(tag="stim", value=stimulus.data.flatten(), procs=speaker.analog_proc)
        main.write(tag="chan0", value=speaker.channel, procs=speaker.analog_proc)
        #correct_pose = False
        #while not correct_pose:
        #    main.wait_for_button()
        #    correct_pose = main.check_pose(fix=(25, 0), var=10)
        main.play_and_wait_for_button()
        #azi, _ = main.get_headpose(convert=True, average=True, n=5)
        #speaker_seq.add_response(azi)

    return speaker_seq


def other_speakers(speaker_seq):
    """return all speakers that are not the target in the current trial"""
    this_speaker = speaker_seq.this_trial
    other_speakers = [condition for condition in speaker_seq.conditions
                      if not all(condition.dropna() == this_speaker.dropna())]
    return other_speakers
