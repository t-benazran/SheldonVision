from PluginSheldonVision.PlotLayers.Constants import TOP, LEFT, WIDTH, HEIGHT
from PluginSheldonVision.Constants import Color, FontFamily

class Box:

    def __init__(self, box: dict = None, top: float = None, left: float = None, width: float = None, height: float = None):
        if all([param is None for param in [box, top, left, width, height]]):
            raise ValueError('No value supplied')
        if box:
            self.top = box[TOP]
            self.left = box[LEFT]
            self.width = box[WIDTH]
            self.height = box[HEIGHT]
        else:
            self.top = top
            self.left = left
            self.width = width
            self.height = height

    def to_dict(self):
        return {LEFT: self.left, HEIGHT: self.height, WIDTH: self.width, TOP: self.top}

    @property
    def right(self):
        return self.left + self.width

    @property
    def bottom(self):
        return self.top + self.height

class GUIRect():

    def __init__(self, left: float, top: float, right: float, bottom: float, color: Color, line_width: int, pressed: bool = False) -> None:
        self.left = left
        self.right = right
        self.top = top
        self.bottom = bottom

        self.color = color
        self.line_width = line_width
        self.pressed = pressed
        
class GUIText():

    def __init__(self, text_message: str, x: float, y: float, color: Color, font_size:int, align:str = 'center') -> None:
        # Todo - add font. Need to solve issue that PIL and plotly have different fonts classes (font: FontFamily = Font.Arial)
        self.text_message = text_message
        self.x = x
        self.y = y
        self.color = color
        self.font_size = font_size
        self.align = align