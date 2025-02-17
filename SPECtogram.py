import numpy
import scipy.io.wavfile
import matplotlib.pyplot as plt
#from scipy.fftpack import dct
from mfcc_bro import do_mfcc

def medianFilter(signal, searchDistance=2):
    minVal = numpy.min(signal)
    signal = numpy.add(signal, minVal)
    signalCopy = signal.copy()

    for i in range(searchDistance, signal.shape[0]-searchDistance):
        kernelExtract = []
        for kernelPart in range(i-searchDistance, i+searchDistance):
            kernelExtract.append(signal[kernelPart])

        signalCopy[i] = numpy.median(kernelExtract)

    return numpy.add(signalCopy, -minVal)


def gimmeDaSPECtogram(input, window_size_ms=30.0, stride_ms=10.0, pre_emphasis=0.97, NFFT=512, triangular_filters=40, magnitude_squared=False, name=None):
    #print(input)
    sample_rate, signal = scipy.io.wavfile.read(input)  # File assumed to be in the same directory
    #print(sample_rate)
    signal = signal[0:int(1.0 * sample_rate)]  # Keep the first 3.5 seconds
    paddedSignal = numpy.repeat(numpy.mean(signal[0:500]), 16000 - signal.shape[0])
    numpy.append(signal, paddedSignal)
    window_size_ms = window_size_ms/1000
    stride_ms = stride_ms/1000

    #ifitspadded = False


    emphasized_signal = numpy.append(signal[0], signal[1:] - pre_emphasis * signal[:-1])
    #emphasized_signal = signal
    if emphasized_signal.shape[0] > 16000:
        emphasized_signal = emphasized_signal[0:int(1.0 * sample_rate)]
    elif emphasized_signal.shape[0] < 16000:
        mean = numpy.mean(numpy.abs(emphasized_signal))
        while emphasized_signal.shape[0] < 16000:
            i = 0

            #print(mean)
            last_value = 0
            for value in emphasized_signal[0:(16000-emphasized_signal.shape[0])]:
                if i > 0 and numpy.abs(value) - numpy.abs(last_value) > 200:
                    break
                last_value = value
                i += 1

            #paddedSignal = numpy.repeat(numpy.mean(emphasized_signal[0:500]), 16000 - signal.shape[0])
            paddedSignal = emphasized_signal[0:i]
            emphasized_signal = numpy.append(emphasized_signal, paddedSignal)
            #print(emphasized_signal.shape)
        #while emphasized_signal.shape[0] < 16000:
        #    distanceToEnd = 16000-emphasized_signal.shape[0]
        #    emphasized_signal = emphasized_signal[:emphasized_signal,]
        #    #numpy.append(emphasized_signal, [0], 0)
        #    print(emphasized_signal.shape)
    window_size_ms, stride_ms = window_size_ms * sample_rate, stride_ms * sample_rate  # Convert from seconds to samples
    signal_length = len(emphasized_signal)
    window_size_ms = int(round(window_size_ms))
    stride_ms = int(round(stride_ms))
    num_frames = int(numpy.ceil(
        float(numpy.abs(signal_length - window_size_ms)) / stride_ms))  # Make sure that we have at least 1 frame

    #print(sample_rate)
    """ FIXED
    print(len(signal)) #16k ofc
    print(sample_rate) #16k ofc
    print(len(emphasized_signal)) #16k ofc
    print(frame_length) #480k, wth?
    print(frame_step) #160k 
    print(num_frames) #3 motherfucking frames bois, is it frames per window?
    """

    #medianFilteredSignal = medianFilter(emphasized_signal)


    pad_signal_length = num_frames * stride_ms + window_size_ms
    z = numpy.zeros((pad_signal_length - signal_length))
    pad_signal = numpy.append(emphasized_signal,
                              z)  # Pad Signal to make sure that all frames have equal number of samples without truncating any samples from the original signal

    indices = numpy.tile(numpy.arange(0, window_size_ms), (num_frames, 1)) + numpy.tile(
        numpy.arange(0, num_frames * stride_ms, stride_ms), (window_size_ms, 1)).T
    frames = pad_signal[indices.astype(numpy.int32, copy=False)] #cast the array to be of type int32.

    frames *= numpy.hamming(window_size_ms)
    # frames *= 0.54 - 0.46 * numpy.cos((2 * numpy.pi * n) / (frame_length - 1))  # Explicit Implementation **

    mag_frames = numpy.absolute(numpy.fft.rfft(frames, NFFT))  # Magnitude of the FFT
    #plt.plot(mag_frames)
    pow_frames = ((1.0 / NFFT) * ((mag_frames) ** 2))  # Power Spectrum
    #plt.plot(pow_frames)

    low_freq_mel = 0
    high_freq_mel = (2595 * numpy.log10(1 + (sample_rate / 4) / 700))  #Ask liming shi #Why is this shit divided by 2? huh? is it because it's half of 8k that they are using? do we need to divide it by 4 then? # Convert Hz to Mel
    mel_points = numpy.linspace(low_freq_mel, high_freq_mel, triangular_filters + 2)  # Equally spaced in Mel scale
    hz_points = (700 * (10 ** (mel_points / 2595) - 1))  # Convert Mel to Hz
    bin = numpy.floor((NFFT + 1) * hz_points / sample_rate)

    fbank = numpy.zeros((triangular_filters, int(numpy.floor(NFFT / 2 + 1))))
    for m in range(1, triangular_filters + 1):
        f_m_minus = int(bin[m - 1])  # left
        f_m = int(bin[m])  # center
        f_m_plus = int(bin[m + 1])  # right

        for k in range(f_m_minus, f_m):
            fbank[m - 1, k] = (k - bin[m - 1]) / (bin[m] - bin[m - 1])
        for k in range(f_m, f_m_plus):
            fbank[m - 1, k] = (bin[m + 1] - k) / (bin[m + 1] - bin[m])
    filter_banks = numpy.dot(pow_frames, fbank.T)
    filter_banks = numpy.where(filter_banks == 0, numpy.finfo(float).eps, filter_banks)  # Numerical Stability

    filter_banks = 20 * numpy.log10(filter_banks)  # dB




    """
    filter_banks -= (numpy.mean(filter_banks, axis=0) + 1e-8)
    plt.imshow(filter_banks.T, cmap=plt.cm.jet, aspect='auto')
    plt.xticks(numpy.arange(0, (filter_banks.T).shape[1],
                            int((filter_banks.T).shape[1] / 4)),
               ['0s', '0.25s', '0.5s', '0.75s', '1s'])
    ax = plt.gca()
    ax.invert_yaxis()
    plt.title('the spectrum image')
    plt.show()
    """


    """
    plt.subplot(312)
    filter_banks = do_mfcc(filter_banks, upper_frequency_limit=4000, lower_frequency_limit=0, dct_coefficient_count=12)
    # filter_banks -= (numpy.mean(filter_banks, axis=0) + 1e-8)
    plt.imshow(filter_banks.T, cmap=plt.cm.jet, aspect='auto')
    plt.xticks(numpy.arange(0, (filter_banks.T).shape[1],
                            int((filter_banks.T).shape[1] / 4)),
               ['0s', '0.25s', '0.5s', '0.75s', '1s'])
    plt.yticks(numpy.arange(1, (filter_banks.T).shape[0],
                            int((filter_banks.T).shape[0] / 4)),
               ['0', '3', '6', '9', '12'])
    ax = plt.gca()
    ax.invert_yaxis()
    plt.title('the mfcc image')
    plt.show()
    """

    filter_banks = do_mfcc(filter_banks, upper_frequency_limit=4000, lower_frequency_limit=0, dct_coefficient_count=12)

    """
    plt.subplot(312)
    filter_banks = do_mfcc(filter_banks, upper_frequency_limit=4000, lower_frequency_limit=0, dct_coefficient_count=12)
    print(filter_banks.shape)
    # filter_banks -= (numpy.mean(filter_banks, axis=0) + 1e-8)
    plt.imshow(filter_banks.T, cmap=plt.cm.jet, aspect='auto')
    plt.xticks(numpy.arange(0, (filter_banks.T).shape[1],
                            int((filter_banks.T).shape[1] / 4)),
               ['0s', '0.25s', '0.5s', '0.75s', '1s'])
    plt.yticks(numpy.arange(1, (filter_banks.T).shape[0],
                            int((filter_banks.T).shape[0] / 4)),
               ['0', '3', '6', '9', '12'])
    ax = plt.gca()
    ax.invert_yaxis()
    plt.show()
    """


    mfccs_graph = filter_banks.T

    return mfccs_graph

    #plt.imshow(filter_banks)

    #plt.imshow(do_mfcc(filter_banks, upper_frequency_limit=4000, lower_frequency_limit=0, dct_coefficient_count=12))

    #plt.show()

    #mfcc plot

    """
    
    plt.subplot(312)
    filter_banks = do_mfcc(filter_banks, upper_frequency_limit=4000, lower_frequency_limit=0, dct_coefficient_count=12)
    #filter_banks -= (numpy.mean(filter_banks, axis=0) + 1e-8)
    plt.imshow(filter_banks.T, cmap=plt.cm.jet, aspect='auto')
    plt.xticks(numpy.arange(0, (filter_banks.T).shape[1],
                         int((filter_banks.T).shape[1] / 4)),
               ['0s', '0.25s', '0.5s', '0.75s', '1s'])
    plt.yticks(numpy.arange(1, (filter_banks.T).shape[0],
                         int((filter_banks.T).shape[0]/4)),
               ['0', '3', '6', '9', '12'])
    ax = plt.gca()
    ax.invert_yaxis()
    plt.title('the mfcc image')

    #Spectrum
    """
    """
    filter_banks -= (numpy.mean(filter_banks, axis=0) + 1e-8)
    plt.imshow(filter_banks.T, cmap=plt.cm.jet, aspect='auto')
    plt.xticks(numpy.arange(0, (filter_banks.T).shape[1],
                            int((filter_banks.T).shape[1] / 4)),
               ['0s', '0.25s', '0.5s', '0.75s', '1s'])
    ax = plt.gca()
    ax.invert_yaxis()
    plt.title('the spectrum image')
    
    """

    plt.show()




#gimmeDaSPECtogram("samples/left.wav", window_size_ms=30.0, stride_ms=10.0, pre_emphasis=0.97)