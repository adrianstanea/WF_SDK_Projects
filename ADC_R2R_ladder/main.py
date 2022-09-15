from AD2_driver import AD2_driver

from utilities import extract_bits, plot_waveform

import CSV_Reader
from constants import *

from time import sleep

import matplotlib.pyplot as plt   # needed for plotting
import numpy


def assign_DIO_signals(AD2: AD2_driver, waveform_int_list, frequency):
    # generate a list for each DIO pin containing the extracted bit list at it's corresponding index from the original waveform_description_list
    for DIO_index in range(8):

        # print(f"Length: {frequency * len(waveform_int_list)}")
        extracted_bits = extract_bits(waveform_int_list, DIO_index)
        AD2.generate_custom_DIO_signal(
            frequency,
            extracted_bits,
            DIO_index)

        # debug
        print(f"DIO_index: {DIO_index}")
        print(extracted_bits)


def get_waveform_parameters(buffer):
    avg_value = sum(buffer) / len(buffer)
    print(f"Average value is: ${avg_value}")
    return (avg_value)


# def plot_data(wave_data):
#     for (buffer, time, color, label) in wave_data:

#         plt.plot(time, buffer, color=color, label=label)
#         # plt.plot(time, test)

#         plt.xlabel("time [ms]")
#         plt.ylabel("voltage [V]")
#         plt.grid()
#         plt.legend()
#         plt.show()


def generate_offset(AD2):
    sleep(0.5)
    buffer, time = AD2.scope_read(2, SAMPLE_RATE, 0.2, BUFFER_SIZE)
    average_voltage = (max(buffer) - min(buffer)) / 2

    print(f"Average voltage is: ${average_voltage}")
    AD2.DC_wave_generator(1, average_voltage/2)
    sleep(0.5)


if __name__ == "__main__":
    AD2 = AD2_driver(VOLTAGE)
    # AD2.DC_wave_generator(1, ADC_AVERAGE_VOLTAGE)
    sleep(0.5)

    WAVEFORM_INT_LIST = CSV_Reader.import_csv_data(WAVEFORM_FILE_PATH)

    assign_DIO_signals(AD2, WAVEFORM_INT_LIST,
                       FREQUENCY * len(WAVEFORM_INT_LIST))
    print(WAVEFORM_INT_LIST)

    try:
        # if DUAL_POLARITY == True:
        #     sleep(1)
        #     generate_offset(AD2)

        sleep(0.5)
        while True:
            print("Running main loop...")

            readings = []
            color = ["orange", "blue"]
            label = ["scope 1", "scope 2"]

            # TODO: to sync based on common trigger point

            for channel in range(1, 3):
                print(f"Reading from channel: ${channel}")
                buffer, time = AD2.scope_read(
                    channel, SAMPLE_RATE, 0.25, BUFFER_SIZE)
                readings.append(
                    (buffer, time, color[channel-1], label[channel - 1]))

            # buffer1, time1 = AD2.scope_read(1, SAMPLE_RATE, 0.5, BUFFER_SIZE)
            # buffer2, time2 = AD2.scope_read(2, SAMPLE_RATE, 0.5, BUFFER_SIZE)

            # get_waveform_parameters(buffer)

            # plot_waveform([(buffer2, time2)])
            plot_waveform(readings)

            # plot_waveform([(buffer1, time1), (buffer2, time2)])

            sleep(3)
    except KeyboardInterrupt:
        print("Exiting program...")
    finally:
        AD2.close_device()
