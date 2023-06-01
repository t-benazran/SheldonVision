import pandas as pd
from dash import html, dcc
import plotly.graph_objs as go
from PluginSheldonVision.PlotLayers.PlotLayerBase import PlotLayerBase
from PluginSheldonVision.MetaDataHandler import MetaDataHandler, MetaDataType
from PluginSheldonVision.Constants import KEYS, VALUES, Color
from PluginSheldonVision.PlotLayers.Elements import Box
from PluginSheldonVision.PlotLayers.Constants import MESSAGE, OBJECTS, SOURCE, BOUNDING_BOX

TEST_TEXT_LAYER_NAME = "TestTextLayer"
FACE_DETECTION = 'FACE_DETECTION'
BLUE_COLOR = Color.Blue


class TestTextLayer(PlotLayerBase):
    def layer_name(self):
        """
        :return: layer name
        """
        return TEST_TEXT_LAYER_NAME

    def add_layer_content(self, meta_data_type: MetaDataType, is_online: bool):
        """
        Method to add a layer to the frame, on this example we created a red rectangle around the face
        @rtype: void
        """
        box = self.get_layer_metadata_position(meta_data_type)
        if box:
            self.add_text('Test text to be printed on screen', BLUE_COLOR, is_online)

    def get_meta_data(self, meta_data_type: MetaDataType):
        """
        Get the data to display below the figure that represent the metadata values
        :param meta_data_type: metadata type - Primary or Secondary
        :return: Div with data to display
        """
        self.reset_meta_data_table()
        box = self.get_layer_metadata_position(meta_data_type)
        if box:
            data = box.to_dict()
            data_frame = pd.DataFrame.from_dict(data.items())
            data_frame.columns = [KEYS, VALUES]
            self.set_meta_data_table(data_frame)
        return self.__create_plot_metadata(self.get_component_id(meta_data_type), box)

    def __create_plot_metadata(self, component_id: str, box: Box):
        """
        Create metadata view with label and graph to locate below the figure.
        This is updating the general div which may contains any acceptable data allowed by dash
        :param component_id: name of component to create
        :param box: the metadata location
        :return: Div with label and graph
        """
        x1 = box.top if box else 0  # get the left top x coordinate
        x2 = box.left if box else 0  # get the left top y coordinate
        y1 = box.right if box else 0  # get the bottom right x coordinate
        y2 = box.bottom if box else 0  # get the bottom right y coordinate
        fig = go.Figure(data=[go.Scatter(x=[x1, x2], y=[y1, y2])])  # create figure graph with box coordinate - just an example of use
        div = html.Div(id=f"{component_id}Div", children=[
            html.Label("TestTextLayer Metadata"),
            dcc.Graph(figure=fig)
        ])
        return div

    def get_layer_metadata_position(self, meta_data_type: MetaDataType) -> Box | None:
        if self.verify_metadata():
            frame_metadata = self.frame_metadata.get(meta_data_type.value)
            if frame_metadata and len(frame_metadata) > 1 and len(frame_metadata[1][MESSAGE][OBJECTS]) > 0:
                for obj in frame_metadata[1][MESSAGE][OBJECTS]:
                    if obj[SOURCE] == FACE_DETECTION:
                        return Box(obj[BOUNDING_BOX])
        return None

    def handle_selected_box_by_click_event(self, box: Box, meta_data_type: MetaDataType):
        """
        Handling a box in case selected on the plot.
        :param box:
        :param meta_data_type:
        :return: plot with new data on it
        """
        self.add_text('Test text to be printed on screen', BLUE_COLOR, False)
        return self.figure_with_layers
