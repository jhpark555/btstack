#!/usr/bin/env python
import numpy as np
import wave
import struct
import sys
from sbc import *
from sbc_encoder import *
from sbc_decoder import *

error = 0.99
max_error = -1

def sbc_compare_pcm(frame_count, actual_frame, expected_frame):
    global error, max_error

    M = mse(actual_frame.pcm, expected_frame.pcm)
    if M > max_error:
        max_error = M

    if M > error:
        print "pcm error (%d, %d ) " % (frame_count, M)
        return -1
    return 0 


def sbc_compare_headers(frame_count, actual_frame, expected_frame):
    if actual_frame.sampling_frequency != expected_frame.sampling_frequency:
        print "sampling_frequency wrong ", actual_frame.sampling_frequency
        return -1

    if actual_frame.nr_blocks != expected_frame.nr_blocks:
        print "nr_blocks wrong ", actual_frame.nr_blocks
        return -1

    if actual_frame.channel_mode != expected_frame.channel_mode:
        print "channel_mode wrong ", actual_frame.channel_mode
        return -1

    if actual_frame.nr_channels != expected_frame.nr_channels:
        print "nr_channels wrong ", actual_frame.nr_channels
        return -1

    if actual_frame.allocation_method != expected_frame.allocation_method:
        print "allocation_method wrong ", actual_frame.allocation_method
        return -1

    if actual_frame.nr_subbands != expected_frame.nr_subbands:
        print "nr_subbands wrong ", actual_frame.nr_subbands
        return -1

    if actual_frame.bitpool != expected_frame.bitpool:
        print "bitpool wrong (E: %d, D: %d)" % (actual_frame.bitpool, expected_frame.bitpool)
        return -1
    
    return 0


def get_actual_frame(fin):
    actual_frame = SBCFrame()
    sbc_unpack_frame(fin, actual_frame)
    sbc_reconstruct_subband_samples(actual_frame)
    sbc_synthesis(actual_frame)
    return actual_frame

def get_expected_frame(fin_expected, nr_blocks, nr_subbands, nr_channels, sampling_frequency, bitpool, allocation_method):
    expected_frame = SBCFrame(nr_blocks, nr_subbands, nr_channels, sampling_frequency, bitpool, allocation_method)
    fetch_samples_for_next_sbc_frame(fin_expected, expected_frame)
    return expected_frame

usage = '''
Usage:      ./sbc_decoder_test.py decoder_input.sbc decoder_expected_output.wav
Example:    ./sbc_decoder_test.py fanfare-4sb.sbc fanfare-4sb-decoded.wav 
'''

if (len(sys.argv) < 3):
    print(usage)
    sys.exit(1)
try:
    decoder_input_sbc = sys.argv[1]
    decoder_expected_wav = sys.argv[2]
    
    if not decoder_input_sbc.endswith('.sbc'):
        print(usage)
        sys.exit(1)

    if not decoder_expected_wav.endswith('.wav'):
        print(usage)
        sys.exit(1)

    fin_expected = wave.open(decoder_expected_wav, 'rb')
    nr_channels, sampwidth, sampling_frequency, nr_audio_frames, comptype, compname =  fin_expected.getparams()
    
    # print nr_channels, sampwidth, sampling_frequency, nr_audio_frames, comptype, compname
    
    with open(decoder_input_sbc, 'rb') as fin:
        try:
            subband_frame_count = 0
            while True:
                if subband_frame_count % 200 == 0:
                    print "== Frame %d ==" % (subband_frame_count)
                
                actual_frame = get_actual_frame(fin)
                
                expected_frame = get_expected_frame(fin_expected, actual_frame.nr_blocks, 
                                                actual_frame.nr_subbands, nr_channels, 
                                                actual_frame.bitpool, sampling_frequency, 
                                                actual_frame.allocation_method)
                
            
                err = sbc_compare_headers(subband_frame_count, actual_frame, expected_frame)
                if err < 0:
                    exit(1)

                err = sbc_compare_pcm(subband_frame_count, actual_frame, expected_frame)
                if err < 0:
                    exit(1)

                if subband_frame_count == 0:
                    print actual_frame
                    
                subband_frame_count += 1
                
        except TypeError:
            fin_expected.close()
            fin.close()
            print "DONE, max MSE PCM error %d", max_error
            exit(0) 

except IOError as e:
    print(usage)
    sys.exit(1)




