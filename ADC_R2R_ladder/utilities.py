import matplotlib.pyplot as plt   # needed for plotting


def extract_bits(int_list, bit_position):
    extracted_bits = []
    for value in int_list:
        #  to extract bit at n-th position we first shift it to LSB position (index 0)
        #  then we extract it's value (either 0 or 1) with a bit mask: 0b1 using bitwise & operation
        extracted_bits.append((value >> bit_position) & 0b1)
    return extracted_bits


def plot_waveform(waveform_data):

    for (buffer, time, color, label) in waveform_data:
        plt.plot(time, buffer, color=color, label=label)

    plt.xlabel("time [ms]")
    plt.ylabel("voltage [V]")
    plt.grid()
    plt.legend()

    plt.show()
