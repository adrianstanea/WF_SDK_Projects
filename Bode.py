from typing import final
from WF_SDK import device
import sys
from ctypes import *
import time
import math
import matplotlib.pyplot as plt


class Bode():
    def __init__(self, ):
        """
            constructor function used to establish connection to device hardware controller
        """
        self.device_data = self.start_device()
        self.init_dwf()

    def start_device(self):
        # helper function
        device_data = device.open()
        device.check_error(device_data)
        return device_data

    def init_dwf(self):
        # helper function
        # get reference to execute dll functions of SDK from python scripts
        if sys.platform.startswith("win"):
            self.dwf = cdll.LoadLibrary("dwf.dll")
        elif sys.platform.startswith("darwin"):
            self.dwf = cdll.LoadLibrary(
                "/Library/Frameworks/dwf.framework/dwf")
        else:
            self.dwf = cdll.LoadLibrary("libdwf.so")

    def close(self):
        # helper function, extend if we use more hardware controllers from SDK
        device.close(self.device_data)

    def run_sampling(self, start=200, stop=2e6, steps=201, amplitude=1):
        """
            Sweep through frequency in order to collect samples of amplitude and phase
            that can be used make a bode plot

        Args:
            start (int, optional): starting sweep frequency. Defaults to 200.
            stop (_type_, optional): stop sweep frequency. Defaults to 2e6.
            steps (int, optional): number of sampling steps. Defaults to 201.
            amplitude (int, optional): sweeping signal amplitude. Defaults to 1 for easy conversion to dB

        Returns:
            tuple: the tuple contains 4 lists with sampled data; 
                    * each sampled frequency,
                    * amplitude in V measured at both channel of the scopes
                    * delay of channel 2 referenced to chanel 1
        """

        dwf = self.dwf
        hdwf = self.device_data.handle

        # this option will enable dynamic adjustment of analog out settings like: frequency, amplitude...
        dwf.FDwfDeviceAutoConfigureSet(hdwf, c_int(3))

        print("Frequency: "+str(start)+" Hz ... " +
              str(stop/1e3)+" kHz Steps: "+str(steps))

        dwf.FDwfAnalogImpedanceReset(hdwf)

        # electronic setup for measurement
        # 0 = W1-C1-DUT-C2-R-GND, 1 = W1-C1-R-C2-DUT-GND, 8 = AD IA adapter
        # use mode 0; for mode 1 just swap resistor with DUT
        dwf.FDwfAnalogImpedanceModeSet(hdwf, c_int(0))

        # set starting frequency in Hz
        dwf.FDwfAnalogImpedanceFrequencySet(
            hdwf, c_double(start))
        # 1V amplitude = 2V peak2peak signal
        dwf.FDwfAnalogImpedanceAmplitudeSet(hdwf, c_double(
            amplitude))
        dwf.FDwfAnalogImpedanceConfigure(hdwf, c_int(1))  # start
        time.sleep(2)

        # reserve memory
        reg_Hz = [0.0]*steps  # used as X axis for bode plot
        reg_gain_C1 = [0.0]*steps  # chanel 1 gain readings
        reg_gain_C2 = [0.0]*steps  # channel 2 gain readings
        # channel 2 phase difference with respect to channel 1 used as reference
        reg_phase_C2 = [0.0]*steps

        for i in range(steps):
            # exponential frequency steps formula
            hz = stop * pow(10.0, 1.0*(1.0*i/(steps-1)-1)
                            * math.log10(stop/start))
            reg_Hz[i] = hz

            # update sweeping frequency
            dwf.FDwfAnalogImpedanceFrequencySet(
                hdwf, c_double(hz))  # frequency in Hertz
            time.sleep(0.01)
            # ignore last capture since we changed the frequency
            dwf.FDwfAnalogImpedanceStatus(hdwf, None)

            status = c_byte()

            # wait until we get valid data acquisition (we need status value of 2)
            while True:
                if dwf.FDwfAnalogImpedanceStatus(hdwf, byref(status)) == 0:
                    quit()
                if status.value == 2:
                    break
            gain1 = c_double()
            gain2 = c_double()
            phase2 = c_double()
            # relative to FDwfAnalogImpedanceAmplitudeSet Amplitude/C1
            dwf.FDwfAnalogImpedanceStatusInput(hdwf, c_int(0), byref(gain1), 0)
            dwf.FDwfAnalogImpedanceStatusInput(hdwf, c_int(1), byref(
                gain2), byref(phase2))  # relative to Channel 1, C1/C#
            # rgGaC1[i] = 1.0/gain1.value
            # rgGaC2[i] = 1.0/gain2.value
            reg_phase_C2[i] = -phase2.value*180/math.pi
            # peak voltage value:
            reg_gain_C1[i] = amplitude/gain1.value
            reg_gain_C2[i] = amplitude/gain1.value/gain2.value

        dwf.FDwfAnalogImpedanceConfigure(hdwf, c_int(0))  # stop instrument

        return (reg_Hz, reg_gain_C1, reg_gain_C2, reg_phase_C2)

    def plot(self, reg_Hz, reg_gain_C1, reg_gain_C2, reg_phase_C2):
        """ 
            crete bode plot using sampled data

        Args:
            reg_Hz (list): sampling frequency values 
            reg_gain_C1 (list): gain on chanel 1 at each frequency
            reg_gain_C2 (list): gain on chanel 2 at each frequency
            reg_phase_C2 (list): phase on chanel 2 at each frequency
        """

        # convert from volts to dB scale
        reg_gain_C2 = [20*math.log10(x) for x in reg_gain_C2]
        reg_gain_C1 = [20*math.log10(x) for x in reg_gain_C1]

        # amplitude plot
        plt.subplot(211)
        # colors should correspond to cable used during sampling, plot both reference and measured amplitudes
        plt.plot(reg_Hz, reg_gain_C1, color='orange')
        plt.plot(reg_Hz, reg_gain_C2, color='blue')
        plt.xlabel(f"Frequency [Hz]")
        plt.ylabel(f"Amplitude [dB]")
        ax = plt.gca()
        ax.set_xscale('log')

        #  phase plot
        plt.subplot(212)
        plt.plot(reg_Hz, reg_phase_C2)
        plt.xlabel(f"Frequency [Hz]")
        plt.ylabel(f"Phase [°]")
        ax = plt.gca()
        ax.set_xscale('log')
        plt.show()


if __name__ == "__main__":
    BodeAnalyzer = Bode()

    try:
        (reg_Hz, reg_gain_C1, reg_gain_C2,
         reg_phase_C2) = BodeAnalyzer.run_sampling()
        BodeAnalyzer.plot(reg_Hz, reg_gain_C1, reg_gain_C2, reg_phase_C2)
    except KeyboardInterrupt:
        print("Exiting program ...")
    finally:
        print("Closing device controllers")
        BodeAnalyzer.close()
