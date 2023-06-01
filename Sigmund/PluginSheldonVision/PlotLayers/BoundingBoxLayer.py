import pandas as pd
from dash import html

from PluginSheldonVision.PlotLayers.PlotLayerBase import PlotLayerBase, RECTS
from PluginSheldonVision.MetaDataHandler import MetaDataHandler, MetaDataType
from SheldonCommon.ReusableComponents import create_updating_data_table_by_callback
from PluginSheldonVision.Constants import KEYS, VALUES, Color, ONLINE_FONT_SIZE, PLOT_WIDTH
from PluginSheldonVision.PlotLayers.Elements import Box, GUIRect
from PluginSheldonVision.PlotLayers.Constants import MESSAGE, OBJECTS, SOURCE, BOUNDING_BOX

BOUNDING_BOX_LAYER_NAME = "BoundingBoxLayer"
FACE_DETECTION = 'FACE_DETECTION'
BODY_DETECTION = 'BODY_DETECTION'
OBJECTS_TO_DETECT = {FACE_DETECTION: Color.Red, BODY_DETECTION: Color.Chocolate}
RED_COLOR = Color.Red


class BoundingBoxLayer(PlotLayerBase):
    def layer_name(self):
        return BOUNDING_BOX_LAYER_NAME

    def add_layer_content(self, meta_data_type: MetaDataType):
        """
        Method to add a layer to the frame, on this example we created a red rectangle around the face
        @rtype: void
        """
        # if meta_data_type==MetaDataType.PRIMARY: ### TEMP
        #    a=1
        self.show_presence_line(meta_data_type)
        for object_name, object_color in OBJECTS_TO_DETECT.items():
            self.show_objects(meta_data_type, object_name, object_color)

    def show_objects(self, meta_data_type: MetaDataType, line_name: str, color: Color):
        objects_lines = self.get_frame_metadata_by_type("objects", meta_data_type)
        if len(objects_lines) == 0:
            return

        if MESSAGE not in objects_lines:
            return

        objects_list = objects_lines[MESSAGE].get("objects")
        for obj in objects_list:
            if obj[SOURCE] == line_name :
                bb = Box(obj[BOUNDING_BOX])
                self.add_rectangular(bb.left, bb.top, bb.right, bb.bottom, color, meta_data_type)
                Z = obj['ZDistanceInMerters']
                source = obj['Source']
                id = obj['Id']
                score = obj['Score']
                left, top = self.rescale_coordinate_2_screen(bb.left, bb.top, meta_data_type)
                right, bottom = self.rescale_coordinate_2_screen(bb.right, bb.bottom, meta_data_type)

                size = self.scale_font_size(max_width=200, min_width=60,
                                            max_font_size=ONLINE_FONT_SIZE, min_font_size=0.5 * ONLINE_FONT_SIZE,
                                            left=left, right=right)

                self.add_text("Z: %1.2f" % (Z), color=Color.White, x=left - 10, y=max(top - 20, 0), font_size=size, align='right')
                # self.add_text("%s"%(source), is_online, color = Color.White, x=left, y=top-20 )
                self.add_text("ID: %d" % (id), color=Color.White, x=min(right + 10, PLOT_WIDTH - 20), y=max(top - 20, 0), font_size=size,
                              align='left')
                self.add_text("score: %d" % (score), color=Color.White, x=left, y=bottom, font_size=size)

    def show_presence_line(self, meta_data_type: MetaDataType):

        presence_lines = self.get_frame_metadata_by_type("presence", meta_data_type)
        if len(presence_lines) == 0:
            return

        if MESSAGE not in presence_lines:
            self.add_text("No data in frame", color=RED_COLOR, x=0.05, y=0.95)
            return
        meta_data = presence_lines[MESSAGE]

        system_state_str = 'System State = ' + meta_data['System State']
        algo_state_str = 'Algo State = ' + meta_data['Algo State']
        screen_state_str = 'Screen State = ' + meta_data['Screen State']
        color = Color.Green if meta_data['Screen State'] == "ON" else Color.Red
        self.add_text(system_state_str, color=color, x=10, y=10)  # , 20, 0.05, 0.7)
        self.add_text(algo_state_str, color=color, x=10, y=30)  # , 20, 0.05, 0.7)
        self.add_text(screen_state_str, color=color, x=10, y=50)  # , 20, 0.05, 0.7)
        if "Activity State" in meta_data.keys():
            activity_state_str = 'Activity State = ' + meta_data['Activity State']
            self.add_text(activity_state_str, color=color, x=10, y=70)
            
    def get_meta_data(self, meta_data_type: MetaDataType):
        objects_lines = self.get_frame_metadata_by_type("objects", meta_data_type)
        if len(objects_lines) == 0 or MESSAGE not in objects_lines:
            return

        objects_list = objects_lines[MESSAGE].get("objects")
        obj_counter = 0
        general_divs = []
        for object_name in OBJECTS_TO_DETECT:
            for obj in objects_list:
                if obj[SOURCE] == object_name:
                    self.reset_meta_data_table()
                    bb = Box(obj[BOUNDING_BOX])
                    if bb:
                        data = bb.to_dict()
                        data_frame = pd.DataFrame.from_dict(data.items())
                        data_frame.columns = [KEYS, VALUES]
                        self.set_meta_data_table(data_frame)
                        obj_counter += 1
                        general_divs.append(html.Label(f'Box #{obj_counter}'))
                        general_divs.append(create_updating_data_table_by_callback(
                            component_id=f'{self.get_component_id(meta_data_type)}-component',
                            data_frame=self.data_frame, sorted_column=KEYS, is_export=False))
        return html.Div(general_divs)

    def get_metadata_by_type(self, line_type: str, meta_data_type: MetaDataType) -> list | None:
        all_lines = []
        if self.verify_metadata():
            frame_metadata = self.frame_metadata.get(meta_data_type.value)

            if frame_metadata:
                all_lines = [f for f in frame_metadata if 'keys' in f.keys() and f['keys']['type'] == line_type]

        if len(all_lines) == 0:
            return []
        if len(all_lines) > 1:
            error_message = "**** Too many presence lines. Case not handeled yet ***"
            print(error_message)
            # self.add_text(error_message, is_online, color = RED_COLOR, x=0.5, y=0.5 )
        all_lines = all_lines[0]

        return all_lines

    def get_layer_metadata_position(self, meta_data_type: MetaDataType) -> Box | None:
        if self.verify_metadata():
            frame_metadata = self.frame_metadata.get(meta_data_type.value)
            if frame_metadata and len(frame_metadata) > 1 and len(frame_metadata[1][MESSAGE][OBJECTS]) > 0:
                for obj in frame_metadata[1][MESSAGE][OBJECTS]:
                    if obj[SOURCE] == BODY_DETECTION:
                        return Box(obj[BOUNDING_BOX])
        return None

    def handle_selected_box_by_click_event(self, clicked_rect: GUIRect, meta_data_type: MetaDataType):
        """
        Handling a box in case selected on the plot.
        :param clicked_rect:
        :param meta_data_type:
        :return: plot with new data on it
        """
        for curr_rect in self.all_GUI_elements[RECTS]:
            if curr_rect == clicked_rect:
                curr_rect.color = Color.Blue
        self.figure_with_layers = self.draw_layer_GUI_elements(self.figure_with_layers, False)
        return self.figure_with_layers
