from WF_SDK import wavegen, device, scope

from time import sleep
import matplotlib.pyplot as plt


class DiodeTracer:
    def __init__(self, voltage=5, totalSamples=101, resistor=100):
        """constructor function

        Args:
            voltage (int, optional): voltage value provided by V+ pin. Defaults to 5.
            totalSamples (int, optional): number of samples taken for the test interval.
                                        Defaults to 101.
            resistor (int, optional): used to calculate current through LED, both are connected in series.
                                    Defaults to 100.
        """
        self.voltage = voltage
        self.totalSamples = totalSamples
        self.resistor = resistor

        # calculate how much voltage increases based on total samples, round to 4 decimals
        self.step = round(voltage/totalSamples, 4)
        # array used to store values when reading
        self.sampledValues = []
        # reference used by device controllers
        self.device_data = self.start_device()

        # class constants
        self.DECIMAL_PRECISION = 6

    def start_device(self):
        device_data = device.open()
        device.check_error(device_data)
        return device_data

    def readMultiple(self, totalReadings=20):
        """When doing a measurement errors can occur, by calculating average value we obtain a 
        more precise value (less noise involved)
        !! Both LED and series resistor must be connected in series to have same current flowing through them.
        Use scope1 to read voltage drop across series limiting resistor
        Use scope2 to read voltage drop across LED
        Args:
            totalReadings (int, optional): how many times we do a reading. Defaults to 20.

        Returns:
            tuple: average result of measured voltage and current with 6 decimal precision
        """
        voltages = []
        currents = []

        for _ in range(totalReadings):
            measuredCurrent = round(scope.measure(
                self.device_data, 1) / self.resistor, self.DECIMAL_PRECISION)
            currents.append(measuredCurrent)

            measuredVoltage = round(scope.measure(
                self.device_data, channel=2), self.DECIMAL_PRECISION)
            voltages.append(measuredVoltage)

        avgVoltage = round(sum(voltages) / len(voltages),
                           self.DECIMAL_PRECISION)
        avgCurrent = round(sum(currents) / len(currents),
                           self.DECIMAL_PRECISION)

        return (avgVoltage, avgCurrent)

    def run(self, doAverage=False, totalRuns=20):
        # clear the values from previous readings
        self.sampledValues.clear()

        scope.open(self.device_data)

        for sample in range(self.totalSamples):
            testVoltage = round(sample * self.step, self.DECIMAL_PRECISION)
            # print("Measure with " + str(testVoltage) + " volts")

            CHANNEL = 1
            wavegen.generate(self.device_data, CHANNEL,
                             wavegen.function.dc, offset=testVoltage)

            #  at each step either do a single read and store or read multiple times and store average
            if doAverage == False:
                # NO AVERAGE
                measuredCurrent = round(scope.measure(
                    self.device_data, 1) / self.resistor, self.DECIMAL_PRECISION)
                measuredVoltage = round(scope.measure(
                    self.device_data, channel=2), 6)
                self.sampledValues.append((measuredVoltage, measuredCurrent))
            else:
                # AVERAGING
                self.sampledValues.append(
                    self.readMultiple(totalReadings=totalRuns))

        scope.close(self.device_data)
        wavegen.close(self.device_data)
        return self.sampledValues

    def close(self):
        # close connections to device controllers
        scope.close(self.device_data)
        wavegen.close(self.device_data)
        device.close(self.device_data)


def plot_curve(sampled_values):
    """Uses voltage and current to plot a LED characteristic

    Args:
        sampled_values (_type_: tuple): voltage, current
    """

    # extract voltage samples
    voltageSamples = [value[0] for value in sampled_values]
    # extract current samples; convert to mA
    currentSamples = [value[1] * 1e3 for value in sampled_values]

    #  make plot of voltage as a function of current
    plt.plot(voltageSamples, currentSamples)
    plt.xlabel("Voltage [V]")
    plt.ylabel("Current [mA]")
    plt.show()


if __name__ == '__main__':
    LEDTracer = DiodeTracer(voltage=4, totalSamples=200)

    try:
        while True:
            print("Doing tests ... ")
            sampled_values = LEDTracer.run(doAverage=True, totalRuns=30)
            plot_curve(sampled_values)
            sleep(2)
    except KeyboardInterrupt:
        print("Break from main loop")
    finally:
        print("Exiting program")
        LEDTracer.close()
