from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty
import numpy as np
from kivy_garden.graph import LinePlot
import logging

logger = logging.getLogger("__main__.widgets.graphs")

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
