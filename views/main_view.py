from neurosdk.sensor import Sensor, SensorCommand, SignalChannelsData
from kivy.uix.screenmanager import  Screen
import logging
from kivy.clock import Clock
from functools import partial
import numpy as np

logger = logging.getLogger("__main__.views.main")

class MainView(Screen):
    def __init__(self, sensor:Sensor, **kwargs):
        super().__init__(**kwargs)
        self.sensor = sensor
        self.refresh_time = 0.001
        self.is_set_to_signal = True
        self.mean_sig = {"O1": 0, "O2": 0, "T3":0, "T4":0}

        # No UI elements defined here, they will be in the KV file

    def on_enter(self, *args):
        self.graph_dict = {
            "O1": self.ids.o1_graph,
            "O2": self.ids.o2_graph,
            "T3": self.ids.t3_graph,
            "T4": self.ids.t4_graph
        }
        sensor_sampling_time = 1 / \
            float(self.sensor.sampling_frequency.name.split("Hz")[1])
        for graph in self.graph_dict.values():
            graph.sampling_time = sensor_sampling_time
        self.sensor.signalDataReceived = self.on_signal_received
        self.sensor.resistDataReceived = self.on_resistance_received
        self.sensor.exec_command(SensorCommand.StartResist)
        #Clock.schedule_once(self.toogle_signal_resistance, 30)

    def toogle_signal_resistance(self, dt):
        if self.is_set_to_signal:
            self.sensor.exec_command(SensorCommand.StopSignal)
            logger.info(f"Executed stop signal")
            self.sensor.exec_command(SensorCommand.StartResist)
            logger.info(f"Executed start resist")
        else:
            self.sensor.exec_command(SensorCommand.StopResist)
            logger.info(f"Executed stop resist")
            self.sensor.exec_command(SensorCommand.StartSignal)
            logger.info(f"Executed start signal")
            
        self.is_set_to_signal = not self.is_set_to_signal

    def on_signal_received(self, loc_sensor: Sensor, signal: list[SignalChannelsData]):
        for s in signal:
            Clock.schedule_once(
                partial(self.graph_dict["O1"].update_graph, s.O1-self.mean_sig["O1"]))
            Clock.schedule_once(
                partial(self.graph_dict["O2"].update_graph, s.O2-self.mean_sig["O2"]))
            Clock.schedule_once(
                partial(self.graph_dict["T3"].update_graph, s.T3-self.mean_sig["T3"]))
            Clock.schedule_once(
                partial(self.graph_dict["T4"].update_graph, s.T4-self.mean_sig["T4"]))
            
            self.mean_sig["O1"] = 0.8 * self.mean_sig["O1"] + 0.2 * s.O1
            self.mean_sig["O2"] = 0.8 * self.mean_sig["O2"] + 0.2 * s.O2
            self.mean_sig["T3"] = 0.8 * self.mean_sig["T3"] + 0.2 * s.T3
            self.mean_sig["T4"] = 0.8 * self.mean_sig["T4"] + 0.2 * s.T4

    def on_resistance_received(self, loc_sensor, resistance):
        resistance = np.array([resistance.O1,resistance.O2,resistance.T3,resistance.T4])
        logger.info(f"max resistance: {resistance.max()}")
        if not np.any(np.isinf(resistance)) and resistance.max() < 1800000:
            Clock.schedule_once(self.toogle_signal_resistance, 0)
        # Clock.schedule_once(partial(self.graph_dict["O1"].update_color, resistance.O1))
        # Clock.schedule_once(partial(self.graph_dict["O2"].update_color, resistance.O2))
        # Clock.schedule_once(partial(self.graph_dict["T3"].update_color, resistance.T3))
        # Clock.schedule_once(partial(self.graph_dict["T4"].update_color, resistance.T4))
