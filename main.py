from kivy.app import App
from kivy.uix.screenmanager import ScreenManager
from neurosdk.sensor import Sensor
import logging
from views import MainView, WaitingForConnectionView
from widgets import SpinningCirclesLoader, GraphWithTitle

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("__main__")

# Global variable to hold the sensor instance
sensor: Sensor = None


class EpilepsyMonitorApp(App):
    def build(self):
        # Kivy will automatically look for 'twoscreen.kv' because the App class is TwoScreenApp

        sm = ScreenManager()
        # Add screens by their class names (UI is loaded from KV)
        sm.add_widget(WaitingForConnectionView(sensor=sensor, name='first'))
        sm.add_widget(MainView(sensor=sensor, name='second'))

        sm.current = 'first'
        return sm


# Entry point to run the application
if __name__ == '__main__':
    EpilepsyMonitorApp().run()
