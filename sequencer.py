#!/usr/bin/env python3
# andrii kuts

import pyaudio
import wave
import sys
import numpy as np

DURATION = 0.17
FRAMERATE = 44100
LENGTH = 28

VOLUME = 0.3
PRE_GAIN = 1.2

A_FREQ = 440
TRANSPOSE = -6

ATACK = 0.05
SUSTAIN = 1-ATACK
UNISON_NUM = 7
UNISON_DET = 40
UNISON_PAN = 0.8

SOFT_GAIN = 1.2

notes = [0, 4, 2, 1, 3, 2, 1, 2, 0, 2, 1, 3, 2, 4, 2, 3]
chords = [[3, 7, 10, 15, 17], [3, 7, 10, 14, 15], [-4, 3, 8, 12, 17], [-4, 3, 7, 12, 14]]

if len(sys.argv) < 2:
    print("\nplease type in a file name to write\n")
    sys.exit(-1)


def get_note_from_A4(n):
	n += TRANSPOSE
	ptch = A_FREQ * (2.0 ** (n/12.0))
	return ptch

note_names = ["A", "Bb", "B", "C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab"]

def get_note_name(n):
	n += TRANSPOSE
	n %= 12
	return note_names[n]

def cents_to_ratio(cnt):
	return (2.0 ** (cnt/1200.0))

def square(t):
	t = t-int(t)
	if t <= 0.5:
		return 1.0
	else:
		return -1.0

def saw(t):
	t = t-int(t)
	return 1-t

def triang(t):
	t = t-int(t)
	return (np.abs((t*-2)+1)*2)-1

def sinus(t):
	return np.sin(t*2*np.pi)

def soft_clip(t, gn):
	t *= gn
	if t <= -1:
		return -2.0/3
	elif t >= 1:
		return 2.0/3
	else:
		return t-(t**3)/3

def play_tone(t, ptch, wav):
	val = float(t)*float(ptch)/float(FRAMERATE)
	if wav == 0:
		return sinus(val)
	elif wav == 1:
		return triang(val)
	elif wav == 2:
		return square(val)
	else:
		return saw(val)

def play_voice(t, ptch, wav, vol, pan):
	amp = play_tone(t, ptch, wav)
	ans = [0.0, 0.0]
	if pan <= 0:
		ans[0] += vol*amp
		ans[1] += vol*amp*(1+pan)
	else:
		ans[1] += vol*amp
		ans[0] += vol*amp*(1-pan)
	return ans

leng = int(FRAMERATE*DURATION)

def play_note(t, ptch):
	global leng
	ans = [0.0, 0.0]
	for i in range(UNISON_NUM):
		pos = float(i+1)/(UNISON_NUM+1) - 1.0/2.0
		pos *= 2
		det = cents_to_ratio(pos*UNISON_DET)
		pan = pos*UNISON_PAN
		amp = play_voice(t, ptch*det, 1, 1, pan)
		ans[0] += amp[0]
		ans[1] += amp[1]
	sub = play_voice(t, ptch/2.0, 0, 0.5, 0)
	ans[0] += sub[0]
	ans[1] += sub[1]
	bass = play_voice(t, ptch/4.0, 0, 0.8, 2)
	ans[0] += bass[0]
	ans[1] += bass[1]
	ans[0] = soft_clip(ans[0]*PRE_GAIN*envelope(t/float(leng)),SOFT_GAIN)
	ans[1] = soft_clip(ans[1]*PRE_GAIN*envelope(t/float(leng)),SOFT_GAIN)
	ans[0] *= VOLUME
	ans[1] *= VOLUME
	return ans

def envelope(t):
	if t < ATACK:
		return t/ATACK
	elif t == ATACK:
		return 1.0
	else:
		return 1.0-(t-ATACK)/SUSTAIN

def distortion(t, amp):
	t = (1-t*amp)
	return 1-(t*t)

chord_num = 0
idx = 0
note_time = 0
FREQ = get_note_from_A4(notes[0])

frames = []

def generate_next_chunk(size):
    global chord_num
    global idx
    global note_time
    global FREQ
    audio_frames = np.empty(size*2, dtype=np.float32)
    for i in range(size):
        if note_time == leng:
            note_time = 0;
            print(get_note_name(chords[chord_num][notes[idx]]), end = ' ')
            idx += 1
            if idx == len(notes):
                idx = 0
                chord_num += 1
                print('\n------------------------------------------\n', end = '')
                if chord_num == len(chords):
                    chord_num = 0
            FREQ = get_note_from_A4(chords[chord_num][notes[idx]])
        amp = play_note(note_time, FREQ)
        audio_frames[i*2] = amp[0]
        audio_frames[i*2+1] = amp[1]
        note_time += 1
    audio_frames = (audio_frames).astype(np.float32)
    return audio_frames

frames = generate_next_chunk(FRAMERATE * LENGTH)

byt_frames = (np.array(frames) * (2**15-1)).astype(np.short)
wf = wave.open(sys.argv[1], 'wb')
wf.setnchannels(2)
wf.setsampwidth(2)
wf.setframerate(FRAMERATE)
wf.writeframes(byt_frames)
wf.close()
