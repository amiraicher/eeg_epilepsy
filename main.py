# main.py
# Import necessary Kivy modules
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget
from kivy.graphics import Color, Ellipse
from kivy.clock import Clock
from kivy.properties import StringProperty, ListProperty, NumericProperty
# Removed: from kivy.lang import Builder # No longer needed for auto-loading
from neurosdk.scanner import Scanner
from neurosdk.sensor import Sensor, SensorCommand, SignalChannelsData, ResistChannelsData
from neurosdk.cmn_types import SensorFamily
import numpy as np
import logging
from functools import partial

# Import MeshLinePlot if you plan to add data to the graph
from kivy_garden.graph import Graph, LinePlot

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("__main__")

# Global variable to hold the sensor instance
sensor: Sensor = None


class GraphWithTitle(BoxLayout):
    title = StringProperty('')
    graph_id = StringProperty('')  # New property to pass ID to the inner Graph

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        x = np.arange(0, 50, 1/40)
        self.line = LinePlot(color=[0.2, 0.7, 1, 1], line_width=1)
        self.line.points = [(x_, np.sin(2*np.pi*5*x_)) for x_ in x]
        self.current_vals = np.array(
            [[point[0], point[1]] for point in self.line.points])
        self.sampling_time = 1/40
        self.current_time = 0

    def on_kv_post(self, base_widget):
        self.ids.graph_obj.add_plot(self.line)
        return super().on_kv_post(base_widget)

    def update_graph(self, val, *args):
        self.line.points.pop(0)
        self.current_vals[:-1] = self.current_vals[1:]
        self.current_vals[-1] = np.array([self.current_time, val])
        self.current_time += self.sampling_time
        self.line.points.append((self.current_time, val))
        self.ids.graph_obj.xmin = float(self.line.points[0][0])
        self.ids.graph_obj.xmax = float(self.current_time)
        self.ids.graph_obj.ymin = float(self.current_vals[:, 1].min())
        self.ids.graph_obj.ymax = float(self.current_vals[:, 1].max())

    def update_color(self, val, *args):
        if np.isinf(val):
            val = 32000
        logger.info(f"Resistance: {val}")
        self.line.color = [np.exp(-val), 1-np.exp(-val), 1, 1]

# Define a custom widget for a single circle


class CircleWidget(Widget):
    # Default gray color (RGBA)
    circle_color = ListProperty([0.5, 0.5, 0.5, 1])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Bind the drawing function to size and position changes
        self.bind(size=self._update_canvas, pos=self._update_canvas,
                  circle_color=self._update_canvas)
        self._update_canvas()  # Initial draw

    def _update_canvas(self, *args):
        # Clear the widget's canvas
        self.canvas.clear()
        with self.canvas:
            # Set the color for the circle
            Color(*self.circle_color)
            # Draw an ellipse (circle) filling the widget's area
            # The size is adjusted slightly to add padding between circles
            # The minimum of width and height is used to ensure it's a circle
            diameter = min(self.width, self.height) * 0.8
            Ellipse(pos=(self.center_x - diameter / 2, self.center_y - diameter / 2),
                    size=(diameter, diameter))

# Define the custom spinning circles loader widget


class SpinningCirclesLoader(BoxLayout):
    active_circle_index = NumericProperty(0)
    animation_event = None
    default_color = [0.5, 0.5, 0.5, 1]  # Gray
    active_color = [0.1, 0.5, 0.8, 1]  # Blue (matching first screen label)

    # Constants for circle dimensions to calculate overall width
    NUM_CIRCLES = 5
    CIRCLE_WIDTH = 40
    SPACING = 10

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.spacing = self.SPACING  # Spacing between circles
        self.size_hint_y = None
        self.height = 50  # Fixed height for the loader

        # Set size_hint_x to None and calculate the explicit width for centering
        self.size_hint_x = None
        # Width = (number of circles * individual circle width) + (number of gaps * spacing)
        self.width = (self.NUM_CIRCLES * self.CIRCLE_WIDTH) + \
            ((self.NUM_CIRCLES - 1) * self.SPACING)

        # Center horizontally in the parent layout
        self.pos_hint = {'center_x': 0.5}

        # Create 5 CircleWidget instances and add them
        for _ in range(self.NUM_CIRCLES):
            # Fixed width for each circle
            circle = CircleWidget(size_hint_x=None, width=self.CIRCLE_WIDTH)
            self.add_widget(circle)
        self._set_initial_colors()

    def _set_initial_colors(self):
        # Set all circles to default gray color initially
        for i, circle in enumerate(self.children):
            # Kivy children list is reversed from how they are added, so reverse index
            reversed_index = len(self.children) - 1 - i
            circle.circle_color = self.default_color

    def start_animation(self):
        if self.animation_event is None:
            # Schedule the animation update to happen every 0.2 seconds
            self.animation_event = Clock.schedule_interval(
                self._animate_circles, 0.2)
            self.active_circle_index = 0  # Reset index when starting
            # Call once immediately to set the first blue circle
            self._animate_circles(0)

    def stop_animation(self):
        if self.animation_event:
            self.animation_event.cancel()
            self.animation_event = None
            # Reset all circles to default gray when stopping
            for circle in self.children:
                circle.circle_color = self.default_color

    def _animate_circles(self, dt):
        # Iterate through the children (circles) and update their colors
        # Kivy's children list is reversed from how they are added to the layout
        # So we need to access them in reverse order to match logical flow (left to right)
        num_circles = len(self.children)
        for i in range(num_circles):
            # Get widget from left to right
            circle_widget = self.children[num_circles - 1 - i]
            if i == self.active_circle_index:
                circle_widget.circle_color = self.active_color
            else:
                circle_widget.circle_color = self.default_color

        # Move to the next active circle, looping back to 0
        self.active_circle_index = (self.active_circle_index + 1) % num_circles


# Define the first screen of the application
class WaitingForConnectionView(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Initialize scanner here
        self.scanner = Scanner([SensorFamily.LEBrainBit])

    def on_enter(self):
        # Defer the execution of the setup logic to ensure KV IDs are ready
        Clock.schedule_once(self._setup_on_enter, 0)

    def _setup_on_enter(self, dt):
        # This method is called when the screen becomes active and IDs are ready
        self.ids.spinner.opacity = 1
        self.ids.spinner.start_animation()  # Start the spinning animation

        # Start scanning for BrainBit device
        self.scanner.sensorsChanged = self.on_sensor_found
        self.scanner.start()
        logger.info("Scanning for sensors...")

    def on_sensor_found(self, scanner: Scanner, sensors):
        global sensor
        if len(sensors) > 0:
            try:
                # Assuming we connect to the first found sensor
                sensor = scanner.create_sensor(sensors[0])
                logger.info(f"Sensor found and created: {sensors[0]}")
                # Schedule transition to the second screen after a short delay
                Clock.schedule_once(self.transition_to_second_screen, 1)
            except Exception as e:
                logger.error(f"Could not create sensor: {e}")
        else:
            logger.info("No sensors found yet...")

    def transition_to_second_screen(self, dt):
        # Stop animation and scanner before transitioning
        self.ids.spinner.stop_animation()
        self.scanner.stop()
        logger.info("Transitioning to second screen.")
        self.manager.current = 'second'

    def on_leave(self):
        # Stop scanner if leaving the screen before a sensor is found
        self.scanner.stop()
        logger.info("Scanner stopped on leaving WaitingForConnectionView.")


# Define the second screen of the application
class SecondScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
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
            float(sensor.sampling_frequency.name.split("Hz")[1])
        for graph in self.graph_dict.values():
            graph.sampling_time = sensor_sampling_time
        sensor.signalDataReceived = self.on_signal_received
        sensor.resistDataReceived = self.on_resistance_received
        sensor.exec_command(SensorCommand.StartResist)
        #Clock.schedule_once(self.toogle_signal_resistance, 30)

    def toogle_signal_resistance(self, dt):
        if self.is_set_to_signal:
            sensor.exec_command(SensorCommand.StopSignal)
            logger.info(f"Executed stop signal")
            sensor.exec_command(SensorCommand.StartResist)
            logger.info(f"Executed start resist")
        else:
            sensor.exec_command(SensorCommand.StopResist)
            logger.info(f"Executed stop resist")
            sensor.exec_command(SensorCommand.StartSignal)
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

# Main application class


class TwoScreenApp(App):
    def build(self):
        # Kivy will automatically look for 'twoscreen.kv' because the App class is TwoScreenApp

        sm = ScreenManager()
        # Add screens by their class names (UI is loaded from KV)
        sm.add_widget(WaitingForConnectionView(name='first'))
        sm.add_widget(SecondScreen(name='second'))

        sm.current = 'first'
        return sm


# Entry point to run the application
if __name__ == '__main__':
    TwoScreenApp().run()
