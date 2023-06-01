import datetime
import os
import logging
import time
from dash.html import Div
from matplotlib import colors
from plotly.graph_objects import Figure
from PIL import Image, ImageDraw, ImageFont
import pandas as pd
from PluginSheldonVision.MetaDataHandler import MetaDataHandler, MetaDataType
from PluginSheldonVision.Constants import KEYS, TENTH_SECOND, Color, FontFamily, Font, PRIMARY_GENERAL_DIV, SECONDARY_GENERAL_DIV, \
    PLOT_WIDTH, PLOT_HEIGHT, ONLINE_FONT_SIZE, HEADER, EMULATED_RESOLUTION, EMUMLATION_MATRIX
from PluginSheldonVision.PlotLayers.Elements import Box, GUIRect, GUIText
import numpy as np

DEFAULT_DATA = {"name": "No Data available for this frame number"}
PIL_PLOTLY_WIDTH_OFFSET = 2
RECTS = 'rects'
TEXT = 'text'
DEFAULT_LOG_PATH = "logs\\PlotLayerBase"


def init_logger_settings(logger: logging, log_file_path=DEFAULT_LOG_PATH):
    """
        Init logger to print log to specific log file and also to console
        @param log_file_path: Log file path
        @param logger: logging object from the calling class
    """
    if not os.path.exists(os.path.abspath(log_file_path)):
        os.makedirs(log_file_path)
    log_file_path = os.path.join(log_file_path, f"PlotLayerBase_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

    logger.basicConfig(filename=log_file_path,
                       filemode='a',
                       format='%(asctime)s,%(msecs)d|%(levelname)s| %(name)s: %(message)s',
                       datefmt='%Y-%d-%m %H:%M:%S')
    console = logging.StreamHandler()
    console_formatter = logging.Formatter("%(levelname)s:%(module)s:%(message)s")
    console.setLevel(logging.DEBUG)
    console.setFormatter(console_formatter)
    logger.getLogger('').addHandler(console)


class PlotLayerBase:
    def __init__(self, meta_data_handler: MetaDataHandler, original_image_height: int = 1080, original_image_width: int = 1920):
        self.frame_metadata = None
        self.whole_clip_metadata = {
            MetaDataType.PRIMARY.value: None,
            MetaDataType.SECONDARY.value: None
        }
        self.frame_number = None
        self.__active = True
        self.image_with_layers: Image.Image | None = None
        self.figure_with_layers: Figure | None = None
        self.meta_data_handler = meta_data_handler
        self.data_frame: bytes | None = None
        self.reset_meta_data_table()
        self.reset_GUI_elemets()
        self.data_frame.columns = [KEYS]
        self.original_image_height = original_image_height
        self.original_image_width = original_image_width
        self.frame_size_check = {
            MetaDataType.PRIMARY.value: True,
            MetaDataType.SECONDARY.value: True
        }
        init_logger_settings(logging)

    def layer_name(self) -> str:
        """
        :return: Layer name
        """
        raise NotImplementedError()

    def add_layer_content(self, meta_data_type: MetaDataType) -> None:
        """
        Adding layer to the image
        :param meta_data_type: relevant metadata type - Primary or Secondary
        """
        raise NotImplementedError()

    def get_meta_data(self, meta_data_type: MetaDataType) -> Div:
        """
        Get frame metadata as html.Div depends on how implemented in the layer to be shown below the image
        :param meta_data_type: relevant metadata - Primary or Secondary
        :return: html.Div as implemented in the layer
        """
        raise NotImplementedError()

    def handle_selected_box_by_click_event(self, box: Box, meta_data_type: MetaDataType) -> Figure:
        """
        Handle the behavior when clicking on the figure on Debug mode
        :param box: the relevant box to handle
        :param meta_data_type: relevant view - Primary or Secondary
        :return: figure with relevant update
        """
        raise NotImplementedError()

    def get_layer_metadata_position(self, meta_data_type: MetaDataType) -> Box | None:
        """
        Get the location of a specific layer
        :param meta_data_type: metadata type - Primary or Secondary
        :return: layer box location or None if no relevant data
        """
        raise NotImplementedError()

    def get_all_GUI_elements(self) -> dict:
        return self.all_GUI_elements

    def set_frame_data(self, frame_data: Figure | Image.Image, frame_number: int) -> None:
        """
        Set the Figure / Image data
        :param frame_data: frame Figure / Image data
        :param frame_number: frame numer
        """
        if issubclass(type(frame_data), Image.Image):
            self.image_with_layers = frame_data.copy()
        else:
            self.figure_with_layers = Figure(frame_data)
        self.frame_number = frame_number
        self.frame_metadata = self.meta_data_handler.get_data_by_frame_number(frame_number)
        #TODO: Find an indication that a new metadata file is loaded, so the resolution in it can be checked instead of this flag
        #TODO: The current flag does not support loading new metadata files after primary and secondary have been loaded once.
        for metadata_type in MetaDataType:
            if self.whole_clip_metadata[metadata_type.value] == None:
                self.whole_clip_metadata[metadata_type.value] = self.meta_data_handler.get_data_for_whole_clip(metadata_type)

            if self.frame_size_check[metadata_type.value]:
                self.original_image_width, self.original_image_height, updated = self.meta_data_handler.get_clip_resolution(self.original_image_width, self.original_image_height,metadata_type)
                self.frame_size_check[metadata_type.value] = not updated

    def draw_layer_GUI_elements(self, image: Image.Image | Figure , is_online_mode) -> Image.Image | Figure:
        for GUI_element in self.all_GUI_elements[RECTS]:
            image = self.draw_rectangular(image, GUI_element, is_online_mode)
        for GUI_element in self.all_GUI_elements[TEXT]:
            image = self.draw_text(image, GUI_element, is_online_mode)
        return image

    def add_layers_to_frame(self, is_online_mode: bool, meta_data_type: MetaDataType) -> Figure | Image.Image:
        """
        Add layer data on an image
        :param is_online_mode: Online or Debug mode
        :param meta_data_type: metadata for specific frame
        :return: figure or image with layer data on it depends on is_online_mode
        """

        if is_online_mode:
            image = self.image_with_layers
        else:
            image = self.figure_with_layers

        self.reset_GUI_elemets()
        self.add_layer_content(meta_data_type)
        image = self.draw_layer_GUI_elements(image, is_online_mode)

        if is_online_mode:
            self.image_with_layers = image
        else:
            self.figure_with_layers = image

        return image

    @staticmethod
    def create_rect_in_pil(image: Image.Image, x0: float, x1: float, y0: float, y1: float, color: Color,
                           width: int = 3 + PIL_PLOTLY_WIDTH_OFFSET) -> Image.Image:
        """
        Add rectangular to image in Online mode
        :param image: image content
        :param x0: top left corner x
        :param x1: top left corner y
        :param y0: bottom right corner x
        :param y1: bottom right corner y
        :param color: rectangular border color
        :param width: rectangular border thickness
        :return: image with rectangular
        """
        draw = ImageDraw.Draw(image)
        draw.rectangle([(x0, y0), (x1, y1)], outline=color, width=width)

        return image

    @staticmethod
    def create_text_in_pil(image: Image.Image, text_message: str, color: Color, font: Font = Font.Arial, font_size: int = ONLINE_FONT_SIZE,
                           x: int = 10, y: int = 10, align: str = 'center') -> Image.Image:
        """
        Add text to image in Online mode
        :param image: image content
        :param text_message: text to add to image
        :param color: text color
        :param font: text font
        :param font_size: text size
        :param x: text x coordinate
        :param y: text y coordinate
        :return: image with text
        """
        draw = ImageDraw.Draw(image)
        rgb_color = tuple([int(c * 256) for c in colors.to_rgb(color)])
        my_font = ImageFont.truetype(font, font_size)
        draw.text((x, y), str(text_message), font=my_font, fill=rgb_color)#, align=align)

        return image

    def active(self) -> bool:
        """
        Layer operation status
        :return: True if Active, False if Inactive
        """
        return self.__active

    def set_layer_state(self, is_active: bool) -> None:
        """
        Sets the layer operation status - Active Inactive
        :param is_active: status to set for the layer
        """
        self.__active = is_active

    @staticmethod
    def create_rect_in_plotly(fig: Figure, x0: float, x1: float, y0: float, y1: float, color: Color, width: int = 3) -> Figure:
        """
        Adding rectangular on Debug mode
        :param fig: figure content
        :param x0: top left corner x
        :param x1: top left corner y
        :param y0: bottom right corner x
        :param y1: bottom right corner y
        :param color: rectangular border color
        :param width: rectangular border thickness
        :return: figure with rectangular
        """
        try:
            fig.add_shape(type="rect", x0=x0, y0=y0, x1=x1, y1=y1, line=dict(color=color, width=width))
        finally:
            return fig

    @staticmethod
    def create_text_in_plotly(fig: Figure, text_message: str, color: Color, font: FontFamily = FontFamily.Arial, font_size: int = 30,
                              x: float = 0.1, y: float = 0.1, align='center') -> Figure:
        """
        Adding Text to image on Debug mode
        :param fig: figure content
        :param text_message: text to add to image
        :param color: text color
        :param font: text font
        :param font_size: text size
        :param x: text x coordinate
        :param y: text y coordinate
        :return: figure with text
        """
        font_dict = {'color': color, 'size': font_size, 'family': font}
        fig.add_annotation(text=str(text_message), xref="paper", yref="paper", x=x, y=y, showarrow=False, font=font_dict, align=align)
        return fig

    def add_rectangular(self, left: float, top: float, right: float, bottom: float, color: Color, meta_data_type: MetaDataType ,line_width: int = 3, pressed: bool = False) -> None:
        left, top, right, bottom, line_width = self.__rescale_position(left, top, right, bottom, line_width, False, meta_data_type) ## Remove the FALSE

        new_rect = GUIRect(left, top, right, bottom, color, line_width, pressed)
        self.all_GUI_elements[RECTS].append(new_rect)

    def draw_rectangular(self, image: Image.Image | Figure, rect: GUIRect, is_online: bool) -> Image.Image | Figure:
        """
        Drawing rectangular on image
        :param image: image content
        :param rect: rectangular to draw
        :param is_online: Online or Debug mode
        """
        if is_online:
            return self.create_rect_in_pil(image, rect.left, rect.right, rect.top, rect.bottom, rect.color, rect.line_width)
        else:
            return self.create_rect_in_plotly(self.figure_with_layers, rect.left, rect.right, rect.top, rect.bottom, rect.color, rect.line_width)

    def add_text(self, text_message: str, x:float, y: float, color:Color = Color.Black, font_size:int = ONLINE_FONT_SIZE, align = 'center') -> None:
        """
        Adding text to image
        :param text_message: text to add to image
        :param x: text x coordinate
        :param y: text y coordinate
        :param color: text color
        :param font_size: text size
        :param align: text align
        """
        font_size = int(PLOT_WIDTH / self.original_image_width * font_size) if self.original_image_width != PLOT_WIDTH else \
                            font_size

        new_text = GUIText(text_message, x, y, color, font_size, align)
        self.all_GUI_elements[TEXT].append(new_text)

    def draw_text(self, image: Image.Image | Figure, text: GUIText, is_online: bool) -> Image.Image | Figure:
        if is_online:
            # x, y = PLOT_WIDTH*x, PLOT_HEIGHT*(1-y)
            return self.create_text_in_pil(image, text.text_message, color=text.color, font_size=text.font_size, x=text.x, y=text.y, align=text.align)
        else:
            x, y = text.x/PLOT_WIDTH, 1- text.y/PLOT_HEIGHT
            return self.create_text_in_plotly(image, text.text_message, color=text.color, x=x, y=y, font_size=text.font_size, align=text.align)

    def scale_font_size(self, max_width, min_width, max_font_size, min_font_size, left, right):
        ratio = (max_font_size - min_font_size) / (max_width - min_width)
        width = right - left
        new_font_size = min(max_font_size, max(min_font_size, min_font_size + ratio * (width - min_width)))
        return new_font_size

    def set_meta_data_table(self, data_frame: pd.DataFrame) -> None:
        """
        Update frame metadata
        :param data_frame: frame metadata
        """
        self.data_frame = data_frame

    def reset_meta_data_table(self) -> None:
        """
        Clears frame metadata
        """
        self.data_frame = pd.DataFrame.from_dict(DEFAULT_DATA.values())
        self.data_frame.columns = [KEYS]

    def reset_GUI_elemets(self) -> None:
        self.all_GUI_elements = {}
        self.all_GUI_elements[RECTS] = []
        self.all_GUI_elements[TEXT] = []

    def verify_metadata(self) -> bool:
        """
        Verify that frame metadata already updated, If not, wait for updating with limited time.
        :return:
        True if metadat update, False if not
        """
        retries = 5
        while not self.frame_metadata and retries > 0:
            retries -= 1
            time.sleep(TENTH_SECOND)
        return self.frame_metadata is not None

    def get_frame_metadata_by_type(self, line_type:str, meta_data_type: MetaDataType) -> list | None:
        all_lines = []
        if self.verify_metadata():
            frame_metadata = self.frame_metadata.get(meta_data_type.value)

            if frame_metadata:
                all_lines = [f for f in frame_metadata if 'keys' in f.keys() and f['keys']['type'] == line_type]

        if len(all_lines)==0:
            return []
        if len(all_lines)>1:
            error_message = "**** Too many lines. Case not handeled yet ***"
            logging.error(error_message)
            # self.add_text(error_message, is_online, color = RED_COLOR, x=0.5, y=0.5 )
        all_lines = all_lines[0]

        return all_lines

    def get_whole_clip_metadata_by_type(self, line_type:str, meta_data_type: MetaDataType, field_name: str) -> list | None:
        rel_meta_data = self.whole_clip_metadata.get(meta_data_type.value)
        if not rel_meta_data:
            return []

        frames_number = list(rel_meta_data.keys())
        metadata_by_frame = [rel_meta_data[frame_num][0]['message'] for frame_num in frames_number \
                             if rel_meta_data[frame_num][0]['keys']['type'] == line_type]

        values_per_frame = [line[field_name] for line in metadata_by_frame]

        return frames_number, values_per_frame

    def get_component_id(self, meta_data_type: MetaDataType) -> str:
        """
        Get the relevant component id to update according to given metadata type
        :param meta_data_type: relevant metadata type - Primary or Secondary
        :return: Div component id
        """
        return PRIMARY_GENERAL_DIV if meta_data_type == MetaDataType.PRIMARY else SECONDARY_GENERAL_DIV

    def get_y_ratio(self, meta_data_type):
        emu_scaling = self.get_emulation_scaling(meta_data_type)[0,0] #Taking the scaling value from the first element in the affine transform matrix
        y_ratio = PLOT_HEIGHT / self.original_image_height * emu_scaling
        return y_ratio

    def get_x_ratio(self, meta_data_type):
        emu_scaling = self.get_emulation_scaling(meta_data_type)[1,1]
        x_ratio = PLOT_WIDTH / self.original_image_width * emu_scaling
        return x_ratio

    def get_emulation_scaling(self, meta_data_type):
        header = self.meta_data_handler.get_header(meta_data_type)
        if EMULATED_RESOLUTION in header[HEADER].keys():
            if header[HEADER][EMULATED_RESOLUTION]:
                return self.string2array(header[HEADER][EMUMLATION_MATRIX])
            else:
                return np.eye(3)
        else:
            return np.eye(3)

    @staticmethod
    def string2array(array_string):
        # remove starting and ending brackets and newline charactes
        array_string = array_string.replace('[','').replace(']','').replace('\n','')
        # make a list of floats
        array_data = [float(x) for x in array_string.split()]
        # reshape it back as numpy array
        array = np.array(array_data).reshape((3,3))
        return array

    def rescale_coordinate_2_screen(self, x, y, meta_data_type):
        x_new = x * self.get_x_ratio(meta_data_type)
        y_new = y * self.get_y_ratio(meta_data_type)
        return x_new, y_new

    def __rescale_position(self, left: float, top: float, right: float, bottom: float, line_width: int, is_online: bool, meta_data_type: MetaDataType):
        if self.original_image_width == 0 and self.original_image_height == 0:
            return left, top, right, bottom, line_width

        left = left * self.get_x_ratio(meta_data_type)
        top = top * self.get_y_ratio(meta_data_type)
        right = right * self.get_x_ratio(meta_data_type)
        bottom = bottom * self.get_y_ratio(meta_data_type)

        line_width = int(line_width * self.get_x_ratio()) + PIL_PLOTLY_WIDTH_OFFSET if is_online else line_width
        left, right, top, bottom = self.__validate_position_layouts(left, right, top, bottom)

        return left, top, right, bottom, line_width

    def __validate_position_layouts(self, left: float, right: float, top: float, bottom: float):
        """
        Validate position layouts
        :param left: position left
        :param right: position right
        :param top: position top
        :param bottom: position bottom
        :return: validated position - left, right, top, bottom
        """
        rescaled_left = 0 if left < 0 else PLOT_WIDTH if left > PLOT_WIDTH else left
        rescaled_right = 0 if right < 0 else PLOT_WIDTH if right > PLOT_WIDTH else right
        rescaled_top = 0 if top < 0 else PLOT_HEIGHT if top > PLOT_HEIGHT else top
        rescaled_bottom = 0 if bottom < 0 else PLOT_HEIGHT if bottom > PLOT_HEIGHT else bottom

        if rescaled_left != left or rescaled_right != right or rescaled_top != top or rescaled_bottom != bottom:
            logging.error(f"Layer layout error- rescaled position out of boundaries")

        return rescaled_left, rescaled_right, rescaled_top, rescaled_bottom
