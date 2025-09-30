from kivy.uix.screenmanager import Screen
from kivy.clock import Clock
from neurosdk.scanner import Scanner
from neurosdk.sensor import Sensor
from neurosdk.cmn_types import SensorFamily
import logging

logger = logging.getLogger("__main__.views.waiting_for_connection")

class WaitingForConnectionView(Screen):
    def __init__(self, sensor: Sensor, **kwargs):
        super().__init__(**kwargs)
        # Initialize scanner here
        self.scanner = Scanner([SensorFamily.LEBrainBit])
        self.sensor = sensor

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
        if len(sensors) > 0:
            try:
                # Assuming we connect to the first found sensor
                self.sensor = scanner.create_sensor(sensors[0])
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

