import ctypes
from WF_SDK import wavegen, device, scope

from time import sleep
import matplotlib.pyplot as plt


class TransistorTracer:
    def __init__(self, Rb=1e3, Rc=100, Vc=5, totalSamples=201, Vb_list=[0.4, 0.8, 1]):
        """constructor function, setup uses a transistor having connected a resistor from base to supply
        another from collector to supply, emitter is connected to gnd

        Args:
            Vc (int, optional): control voltage. Defaults to 5.
            totalSamples (int, optional): number of samples taken for the test interval.
                                          Defaults to 201.
            Rb (float): resistor connected to base, used to convert measured voltage to current.
                        Defaults to 1e3.
            Rc (float): resistor connected to collector, used to convert measured voltage to current.
                        Defaults to 100.
            Vb (list, optional): discrete desired test values to be applied to base of transistor  
        """
        self.Vc = Vc
        self.totalSamples = totalSamples
        self.Rb = Rb
        self.Rc = Rc
        self.Vb_list = Vb_list

        self.step = round(Vc/totalSamples, 4)

        #  reference needed after starting device for each hardware controller
        self.device_data = self.start_device()

    def start_device(self):
        device_data = device.open()
        device.check_error(device_data)
        return device_data

    def readMultiple(self, totalReadings=20):
        """When doing a measurement errors can occur, by calculating average value we obtain a 
        more precise value (less noise involved)

        Args:
            totalReadings (int, optional): how many times we do a reading. Defaults to 20.

        Returns:
            tuple: average result of measured voltage and current with 6 decimal precision
        """

        voltages = []
        currents = []
        for i in range(1, totalReadings):
            Ic = round(scope.measure(
                self.device_data, 1) / self.Rc, 6)
            currents.append(Ic)

            Vce = round(scope.measure(
                self.device_data, channel=2), 6)
            voltages.append(Vce)

        avgVoltage = round(sum(voltages) / len(voltages), 6)
        avgCurrent = round(sum(currents) / len(currents), 6)

        return (avgVoltage, avgCurrent)

    def run(self, doAverage=False, totalRuns=20):
        """_summary_

        Args:
            doAverage (bool, optional): measure multiple times for same sample and average value. Defaults to False.
            totalRuns (int, optional): number of runs when doing average. Defaults to 20.

        Returns:
            list: the list contains nested lists, each one corresponding to a particular value of the base voltage
        """
        sampledValues = []

        scope.open(self.device_data)

        for applied_base_voltage in self.Vb_list:
            print(f"Base voltage: {applied_base_voltage}")
            wavegen.generate(self.device_data, 1,
                             wavegen.function.dc, offset=applied_base_voltage)
            current_reading = []
            for sample in range(self.totalSamples):
                test_voltage = round(sample * self.step, 4)

                wavegen.generate(self.device_data, 2,
                                 wavegen.function.dc, offset=test_voltage)

                if doAverage == False:
                    # NO AVERAGE
                    Ic = round(scope.measure(
                        self.device_data, 1) / self.Rc, 6)
                    Vce = round(scope.measure(
                        self.device_data, channel=2), 6)
                    current_reading.append(
                        (Vce, Ic))
                else:
                    # AVERAGING
                    current_reading.append(
                        self.readMultiple(totalReadings=totalRuns))

            sampledValues.append(current_reading)
            wavegen.generate(self.device_data, 1,
                             wavegen.function.dc, offset=0)
            sleep(0.5)

        scope.close(self.device_data)
        wavegen.close(self.device_data)
        return sampledValues

    def close(self):
        # close connections to device controllers
        scope.close(self.device_data)
        wavegen.close(self.device_data)
        device.close(self.device_data)


def plot_curve(sampled_values):
    # sampled values is a list that contains nested lists, for each one of them we extract an plot sampled values
    for values in sampled_values:
        voltageSamples = [value[0] for value in values]
        currentSamples = [value[1] * 1e3 for value in values]  # convert to mA
        plt.plot(voltageSamples, currentSamples)

    plt.xlabel("Vce [V]")
    plt.ylabel("Ic [mA]")
    plt.show()


if __name__ == '__main__':
    transistor_tracer = TransistorTracer(
        Vc=4, totalSamples=301, Vb_list=[0.8, 1.2, 1.6, 2])

    try:
        while True:
            print("Doing tests ... ")
            sampled_values = transistor_tracer.run(
                doAverage=True, totalRuns=100)
            plot_curve(sampled_values)
            sleep(2)
    except KeyboardInterrupt:
        print("Break from main loop")
    finally:
        print("Exiting program")
        transistor_tracer.close()
