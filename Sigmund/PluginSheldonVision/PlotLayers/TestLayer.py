import pandas as pd
from PluginSheldonVision.PlotLayers.PlotLayerBase import PlotLayerBase
from PluginSheldonVision.MetaDataHandler import MetaDataHandler, MetaDataType
from SheldonCommon.ReusableComponents import create_data_div
from PluginSheldonVision.Constants import KEYS, VALUES, Color
from PluginSheldonVision.PlotLayers.Elements import Box
from PluginSheldonVision.PlotLayers.Constants import MESSAGE, OBJECTS, SOURCE, BOUNDING_BOX

TEST_LAYER_NAME = "TestLayer"
BODY_DETECTION = 'BODY_DETECTION'
ORANGE_COLOR = Color.Orange


class TestLayer(PlotLayerBase):

    def __init__(self, meta_data_handler: MetaDataHandler):
        super().__init__(meta_data_handler)
        self.current_width = 3

    def layer_name(self) -> str:
        return TEST_LAYER_NAME

    def add_layer_content(self, meta_data_type: MetaDataType, is_online: bool):
        """
        Method to add a layer to the frame, on this example we created a red rectangle around the face
        @rtype: void
        """
        box = self.get_layer_metadata_position(meta_data_type)
        if box:
            self.add_rectangular(is_online, box.left, box.top, box.right, box.bottom, ORANGE_COLOR, meta_data_type)

    def get_meta_data(self, meta_data_type: MetaDataType):
        self.reset_meta_data_table()
        box = self.get_layer_metadata_position(meta_data_type)
        if box:
            data = box.to_dict()
            data_frame = pd.DataFrame.from_dict(data.items())
            data_frame.columns = [KEYS, VALUES]
            self.set_meta_data_table(data_frame)
        return create_data_div(component_id=f"{self.get_component_id(meta_data_type)}cmp", data_frame=self.data_frame)

    def get_layer_metadata_position(self, meta_data_type: MetaDataType) -> Box | None:
        if self.verify_metadata():
            frame_metadata = self.frame_metadata[meta_data_type.value]
            if frame_metadata and len(frame_metadata) > 1 and len(frame_metadata[1][MESSAGE][OBJECTS]) > 0:
                for obj in frame_metadata[1][MESSAGE][OBJECTS]:
                    if obj[SOURCE] == BODY_DETECTION:
                        return Box(obj[BOUNDING_BOX])
        return None

    def handle_selected_box_by_click_event(self, box: Box, meta_data_type: MetaDataType):
        self.current_width = 6 if self.current_width == 3 else 3
        self.add_rectangular(False, box.left, box.top, box.right, box.bottom, ORANGE_COLOR, width=self.current_width, meta_data_type= meta_data_type)
        return self.figure_with_layers
