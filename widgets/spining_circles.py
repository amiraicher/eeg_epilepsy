from kivy.uix.widget import Widget
from kivy.graphics import Color, Ellipse
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock
from kivy.properties import StringProperty, ListProperty, NumericProperty


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
