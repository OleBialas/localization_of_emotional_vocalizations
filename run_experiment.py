import sys
sys.path.append("D:/Projects/localization_of_emotional_vocalizations")
sys.path.append("D:/Projects/freefield")
import os
import slab
from freefield import main
from experiment import DIR, priming, block

# calibrate the camera
main.initialize_setup(setup="arc", default_mode="cam_calibration", zbus=True, connection="GB", camera_type="flir")
calibration_targets = main.get_speaker_list([9, 16, 23])
main.calibrate_camera_no_visual(calibration_targets, n_reps=1, n_images=5)

# initialize the setup for the experiment
proc_list = [["RX81", "RX8", DIR/"rcx"/"play_buffer_from_channel.rcx"],
             ["RX82", "RX8", DIR/"rcx"/"play_buffer_from_channel.rcx"],
             ["RP2", "RP2",  DIR/"rcx"/"button_response.rcx"]]
main.PROCESSORS.initialize(proc_list=proc_list, zbus=True, connection="GB")


# configuring number of blocks and trials:
n_repeat_conditions = 2
n_repeat_files = 2
n_repeat_speakers = 4
speakers = main.get_speaker_list(list(range(9, 24)))  # speakers used in the experiment
calibration_targets = main.get_speaker_list([9, 16, 23])
priming_speakers = speakers.iloc[::3, :]  # use every third speaker for priming
priming_speakers = priming_speakers.reset_index()
speakers = [speakers.loc[i] for i in speakers.index]

# make a folder for the subject:
subject = "subject0"
try:
    os.makedirs(DIR/"data"/subject)
except FileExistsError:
    print(f"folder {DIR/'data'/subject} already exists")

# generate and save the trial sequences:
conditions = slab.Trialsequence(conditions=["positive", "negative", "neutral"],
                                n_reps=n_repeat_conditions, kind='non_repeating')

conditions.save_pickle(DIR/"data"/subject/"conditions.pickle")
n_files = 31  # number of .wav files that contain the stimuli (per condition)
for i in range(conditions.n_trials+1):  # make trial lists for single blocks, +1 for initial noise block
    file_seq = slab.Trialsequence(conditions=n_files, n_reps=n_repeat_files, kind='non_repeating')
    speaker_seq = slab.Trialsequence(conditions=speakers, n_reps=n_repeat_speakers, kind='non_repeating')
    file_seq.save_pickle(DIR/"data"/subject/f"file_seq{i}.pickle")
    speaker_seq.save_pickle(DIR/"data"/subject/f"speaker_seq{i}.pickle")

# run a "noise" block:
file_seq = slab.Trialsequence(str(DIR/"data"/subject/"file_seq0.pickle"))
speaker_seq = slab.Trialsequence(str(DIR/"data"/subject/"speaker_seq0.pickle"))
speaker_seq = block(kind="noise", speaker_seq=speaker_seq, file_seq=file_seq)  # run the block
speaker_seq.save_pickle(DIR/"data"/subject/f"speaker_seq0.pickle")


# run the blocks:
for condition in conditions:
    # load the sequences
    file_seq = slab.Trialsequence(str(DIR/"data"/subject/f"file_seq{conditions.this_n+1}.pickle"))
    speaker_seq = slab.Trialsequence(str(DIR/"data"/subject/f"speaker_seq{conditions.this_n+1}.pickle"))
    priming(priming_speakers, condition)  # run the priming
    speaker_seq = block(kind=condition, speaker_seq=speaker_seq, file_seq=file_seq)  # run the block
    speaker_seq.save_pickle(DIR/"data"/subject/f"speaker_seq{conditions.this_n+1}.pickle")
