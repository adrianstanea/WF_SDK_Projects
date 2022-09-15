from pickle import TRUE
import wave
from WF_SDK import device, supplies, pattern, scope, wavegen       # import instruments

from time import sleep

# from utilities import extract_bits


class AD2_driver:
    def __init__(self, VCC):
        self.device_data = self.start_device()
        self.VCC = VCC
        self.supply = self.start_sources()

    def start_device(self):
        device_data = device.open()
        device.check_error(device_data)
        return device_data

    def start_sources(self):
        supply_config_settings = self.config_sources()
        # apply configurations
        supplies.switch(self.device_data, supply_config_settings)
        return supply_config_settings

    def config_sources(self):
        supply = supplies.data()
        supply.master_state = True
        supply.positive_state = True
        supply.negative_state = True
        supply.positive_voltage = abs(self.VCC)
        supply.negative_voltage = -abs(self.VCC)
        return supply

    def generate_custom_DIO_signal(self, frequency, waveform_int_list, DIO_index):
        pattern.enable(self.device_data, DIO_index)
        pattern.generate(self.device_data, channel=DIO_index,
                         function=pattern.function.custom,
                         frequency=frequency,
                         data=waveform_int_list)

    def DC_wave_generator(self, channel, offset):
        wavegen.generate(self.device_data, channel,
                         wavegen.function.dc, offset)

    def scope_read(self, channel, sample_rate, trigger_level, buffer_size):
        scope.open(self.device_data, sampling_frequency=sample_rate,
                   amplitude_range=10, buffer_size=buffer_size)
        sleep(0.1)
        scope.trigger(self.device_data, enable=True,
                      source=scope.trigger_source.analog, channel=channel, level=trigger_level)

        buffer, time = scope.record(self.device_data, channel=channel)
        time = [moment * 1e3 for moment in time]

        scope.close(self.device_data)
        return (buffer, time)

        # call function to end connection when main program finishes execution

    def close_device(self):
        self.close_sources()
        pattern.close(self.device_data)
        device.close(self.device_data)

    def close_sources(self):
        self.supply.master_state = False  # disable switch
        supplies.switch(self.device_data, self.supply)  # update changes
        supplies.close(self.device_data)
