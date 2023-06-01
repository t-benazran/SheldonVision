import pandas as pd
from PluginSheldonVision.PlotLayers.PlotLayerBase import PlotLayerBase, RECTS
from PluginSheldonVision.MetaDataHandler import MetaDataType
from SheldonCommon.ReusableComponents import create_updating_data_table_by_callback
from PluginSheldonVision.Constants import Color, ONLINE_FONT_SIZE, PLOT_WIDTH
from PluginSheldonVision.PlotLayers.Elements import Box, GUIRect
from PluginSheldonVision.PlotLayers.Constants import MESSAGE, BOUNDING_BOX
from dash import dcc, html
import plotly.graph_objects as go

GT_LOG_LAYER_NAME = "GTLogLayer"
FACE_DETECTION = 'Face BB'
BODY_DETECTION = 'Body BB'
RED_COLOR = Color.Red
CHOCOLATE_COLOR = Color.Chocolate
OBJECTS_TO_DETECT = {FACE_DETECTION: RED_COLOR, BODY_DETECTION: CHOCOLATE_COLOR}


class GTLogLayer(PlotLayerBase):
    def get_layer_metadata_position(self, meta_data_type: MetaDataType) -> Box | None:
        pass

    def layer_name(self):
        """
        Get layer name
        """
        return GT_LOG_LAYER_NAME

    def add_layer_content(self, meta_data_type: MetaDataType):
        """
        Method to add a layer to the frame, on this example we created a red rectangle around the face
        @rtype: void
        """
        self.show_gt_sequence_line(meta_data_type)
        for line_type, object_color in OBJECTS_TO_DETECT.items():
            self.show_objects(meta_data_type, line_type, object_color)

    def show_objects(self, meta_data_type: MetaDataType, line_type: str, color: Color = Color.Black):
        objects_lines = self.get_frame_metadata_by_type(line_type, meta_data_type)
        if len(objects_lines) == 0:
            return

        if MESSAGE not in objects_lines:
            return

        objects_list = objects_lines[MESSAGE].get("objects")

        for obj in objects_list:
            bb = Box(obj[BOUNDING_BOX])

            self.add_rectangular(bb.left, bb.top, bb.right, bb.bottom, color, meta_data_type)
            id = obj['Id']
            score = obj['confidence']
            left, top = self.rescale_coordinate_2_screen(bb.left, bb.top, meta_data_type)
            right, bottom = self.rescale_coordinate_2_screen(bb.right, bb.bottom, meta_data_type)

            size = self.scale_font_size(max_width=200, min_width=60, max_font_size=ONLINE_FONT_SIZE,
                                        min_font_size=0.5 * ONLINE_FONT_SIZE, left=left, right=right)

            self.add_text("ID: %d" % (id), color=Color.White, x=min(right + 10, PLOT_WIDTH - 20), y=max(top - 20, 0),
                          font_size=size, align='left')
            self.add_text("score: %d" % (score), color=Color.White, x=left, y=bottom, font_size=size)

    def show_gt_sequence_line(self, meta_data_type: MetaDataType):
        gt_sequence_lines = self.get_frame_metadata_by_type("sequence", meta_data_type)
        if len(gt_sequence_lines) == 0:
            return

        if MESSAGE not in gt_sequence_lines:
            self.add_text("No data in frame", color=RED_COLOR, x=0.05, y=0.95)
            return
        meta_data = gt_sequence_lines[MESSAGE]

        if "Approach_R0" in meta_data.keys():
            approach_r0_str = 'Approach_R0 = ' + meta_data['Approach_R0']
            approach_r1_str = 'Approach_R1 = ' + meta_data['Approach_R1']
            color = Color.Orange if meta_data['Approach_R0'] else Color.Green if meta_data['Approach_R1'] else Color.Red
            self.add_text(approach_r0_str, color=color, x=10, y=10)  # , 20, 0.05, 0.7)
            self.add_text(approach_r1_str, color=color, x=10, y=30)  # , 20, 0.05, 0.7)

        if "HumanPresence" in meta_data.keys():
            human_presence_str = 'HumanPresence = ' + meta_data['HumanPresence']
            self.add_text(human_presence_str, color=color, x=10, y=50)

        if "User_Status" in meta_data.keys():
            User_Status_str = 'User_Status = ' + meta_data['User_Status']
            self.add_text(User_Status_str, color=color, x=10, y=70)
        
        if "System_Context" in meta_data.keys():
            system_Context_str = 'System Context:  ' + meta_data['System_Context']
            system_context_color = Color.Blue if 'wake' in meta_data['System_Context'] else Color.Red
            self.add_text(system_Context_str, color = system_context_color, x=10, y=10 )
            self.add_text("Wake", color = Color.Blue if eval(meta_data['Is_Wake_event']) else Color.Black, x=10, y=30 )
            self.add_text("Lock", color = Color.Blue if eval(meta_data['Is_Lock_event']) else Color.Black, x=100, y=30 )
            self.add_text("Presence ROI", color = Color.Blue if eval(meta_data['Presence_ROI']) else Color.Black, x=200, y=30 )
            self.add_text("User_Status:  "+ meta_data['User_Status'], color = system_context_color,  x=10, y=50 )


    def get_meta_data(self, meta_data_type: MetaDataType):
        self.reset_meta_data_table()
        gt_sequence_lines = self.get_frame_metadata_by_type("sequence", meta_data_type)
        if len(gt_sequence_lines) == 0:
            return

        meta_data = gt_sequence_lines[MESSAGE]
        data_frame = pd.DataFrame.from_dict(meta_data.items())
        data_frame.columns = ['keys', 'values']
        data_table = create_updating_data_table_by_callback(
            component_id=f'{self.get_component_id(meta_data_type)}-component',
            data_frame=data_frame,
            sorted_column='keys',
            is_export=False)

        #frames_number, approach_r0_values = self.get_whole_clip_metadata_by_type("sequence", meta_data_type,
        #                                                                         "Approach_R0")
        #approach_r0_values = [int(x == 'True') for x in approach_r0_values]
        #_, approach_r1_values = self.get_whole_clip_metadata_by_type("sequence", meta_data_type, "Approach_R1")
        #approach_r1_values = [int(x == 'True') for x in approach_r1_values]
        fig = go.Figure()
        #fig.add_trace(go.Scatter(x=frames_number,
        #                         y=approach_r0_values,
        #                         name='R0',
        #                         line=dict(color='firebrick', width=4)))
        #fig.add_trace(go.Scatter(x=frames_number,
        #                         y=approach_r1_values,
        #                         name='R111',
        #                         line=dict(color='red', width=4)))
        #fig.add_trace(go.Scatter(x=[self.frame_number, self.frame_number],
        #                         y=[0, 1],
        #                         name='frame_num',
        #                         line=dict(color='black', width=4)))
   

        g = dcc.Graph(figure=fig)

        div = html.Div(id=f'{self.get_component_id(meta_data_type)}-componentDiv',
                       children=[html.H4("My metadata"),
                                 data_table,
                                 g,
                                 ])
        return div

    def handle_selected_box_by_click_event(self, clicked_rect: GUIRect, meta_data_type: MetaDataType):
        """
        Handling a box in case selected on the plot.
        :param clicked_rect: clicked rect
        :param meta_data_type:
        :return: plot with new data on it
        """
        for curr_rect in self.all_GUI_elements[RECTS]:
            if curr_rect == clicked_rect:
                curr_rect.color = Color.Blue
        self.figure_with_layers = self.draw_layer_GUI_elements(self.figure_with_layers, False)

        return self.figure_with_layers
