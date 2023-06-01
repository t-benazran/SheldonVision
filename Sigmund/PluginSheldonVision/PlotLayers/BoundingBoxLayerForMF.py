import pandas as pd
from PluginSheldonVision.PlotLayers.PlotLayerBase import PlotLayerBase, RECTS
from PluginSheldonVision.MetaDataHandler import MetaDataHandler, MetaDataType
from SheldonCommon.ReusableComponents import create_updating_data_table_by_callback
from PluginSheldonVision.Constants import KEYS, VALUES, Color, ONLINE_FONT_SIZE, PLOT_WIDTH
from PluginSheldonVision.PlotLayers.Elements import Box, GUIRect
from PluginSheldonVision.PlotLayers.Constants import MESSAGE, OBJECTS, SOURCE, BOUNDING_BOX

BOUNDING_BOX_LAYER_FOR_MF_NAME = "BoundingBoxLayerForMF"
FACE_DETECTION = 'FACE_DETECTION'
BODY_DETECTION = 'BODY_DETECTION'
RED_COLOR = Color.Red


class BoundingBoxLayerForMF(PlotLayerBase):
    def __init__(self, meta_data_handler: MetaDataHandler):
        super().__init__(meta_data_handler)

    def layer_name(self):
        return BOUNDING_BOX_LAYER_FOR_MF_NAME

    def add_layer_content(self, meta_data_type: MetaDataType):
        """
        Method to add a layer to the frame, on this example we created a red rectangle around the face
        @rtype: void
        """
        #if meta_data_type==MetaDataType.PRIMARY: ### TEMP
        #    a=1
        #self.show_presence_line(meta_data_type)
        self.show_objects_mf(meta_data_type)

    def scale_font_size(self, max_width, min_width, max_font_size, min_font_size, left, right):
        ratio = (max_font_size - min_font_size)/(max_width-min_width)
        width = right-left
        new_font_size = min(max_font_size, max(min_font_size,min_font_size+ ratio* (width-min_width)))
        return new_font_size

    def show_objects_mf(self, meta_data_type: MetaDataType):
        objects_lines = self.get_metadata_by_type("multiframe_objects", meta_data_type)
        if len(objects_lines)==0:
            #frame_metadata = self.frame_metadata.get(meta_data_type.value)
            #objects_lines = frame_metadata[0]
            objects_lines = self.get_metadata_by_type("MultiFrameOutput", meta_data_type)

        if MESSAGE not in objects_lines:
            return
        
        objects_list = objects_lines[MESSAGE].get("objects")

        for obj in objects_list:
            bb = Box(obj['Object']['BoundingBox'])
            ObjectType = obj['ObjectType']
            if ObjectType == 'OBJECT_TRACK_AND_DETECTION':
                ObjectColor = Color.Green
            elif ObjectType == 'OBJECT_NO_DETECTION':
                ObjectColor = Color.Red
            elif  ObjectType == 'OBJECT_NO_TRACKING':
                ObjectColor = Color.Blue
            elif ObjectType == 'NEW_OBJECT':
                ObjectColor = Color.Gray
            elif ObjectType == 'NO_OBJECT_WAITING':
                ObjectColor = Color.White

            self.add_rectangular(bb.left, bb.top, bb.right, bb.bottom, ObjectColor, meta_data_type)
            
            ObjectID = obj['ObjectID']
            ObjectDetectorScore = obj['DetectorScore']
            ObjectTrackerScore = obj['TrackerScore']

            left, top = self.rescale_coordinate_2_screen(bb.left, bb.top, meta_data_type)
            right, bottom = self.rescale_coordinate_2_screen(bb.right, bb.bottom, meta_data_type)
            size = self.scale_font_size(max_width = 200, min_width = 60,
                                       max_font_size = ONLINE_FONT_SIZE, min_font_size = 0.5*ONLINE_FONT_SIZE,
                                       left = left, right = right)
            
            self.add_text("ID: %d"%(ObjectID), color = ObjectColor, x=left-10, y=max(top-20,0), font_size=size+10, align = 'left')
            #self.add_text("Detector score: %1.2f"%(ObjectDetectorScore), color = Color.White, x=min(right+10,PLOT_WIDTH-20) , y=max(top-40,0), font_size=size,align = 'right')
            #self.add_text("Tracker score: %1.2f"%(ObjectTrackerScore), color = Color.White, x=min(right+10,PLOT_WIDTH-20), y=max(top-40,0), font_size=size,align = 'right')


            
    
    def show_objects(self, meta_data_type: MetaDataType):
        objects_lines = self.get_metadata_by_type("objects", meta_data_type)
        if len(objects_lines)==0:
            return

        if MESSAGE not in objects_lines:
            return
        
        objects_list = objects_lines[MESSAGE].get("objects")

        for obj in objects_list:
            if obj[SOURCE] == BODY_DETECTION:
                bb = Box(obj[BOUNDING_BOX])
                self.add_rectangular(bb.left, bb.top, bb.right, bb.bottom, RED_COLOR, meta_data_type)
                Z = obj['ZDistanceInMerters']
                source = obj['Source']
                id = obj['Id']
                score = obj['Score']
                left, top = self.rescale_coordinate_2_screen(bb.left, bb.top, meta_data_type)
                right, bottom = self.rescale_coordinate_2_screen(bb.right, bb.bottom, meta_data_type)

                size = self.scale_font_size(max_width = 200, min_width = 60,
                                       max_font_size = ONLINE_FONT_SIZE, min_font_size = 0.5*ONLINE_FONT_SIZE,
                                       left = left, right = right)

                self.add_text("Z: %1.2f"%(Z), color = Color.White, x=left-10, y=max(top-20,0), font_size=size, align = 'right')
                # self.add_text("%s"%(source), is_online, color = Color.White, x=left, y=top-20 )
                self.add_text("ID: %d"%(id), color = Color.White, x=min(right+10,PLOT_WIDTH-20) , y=max(top-20,0), font_size=size,align = 'left')
                self.add_text("score: %d"%(score), color = Color.White, x=left, y=bottom, font_size=size )


    def show_presence_line(self, meta_data_type: MetaDataType):

        presence_lines = self.get_metadata_by_type("presence", meta_data_type)
        if len(presence_lines)==0:
            return

        if MESSAGE not in presence_lines:
            self.add_text("No data in frame", color = RED_COLOR, x=0.05, y=0.95 )
            return
        meta_data = presence_lines[MESSAGE]

        system_state_str = 'System State = ' + meta_data['System State']
        algo_state_str = 'Algo State = ' + meta_data['Algo State']
        screen_state_str = 'Screen State = ' + meta_data['Screen State']
        color = Color.Green if meta_data['Screen State']=="ON" else Color.Red
        self.add_text(system_state_str, color = color, x=10, y=10 )#, 20, 0.05, 0.7)
        self.add_text(algo_state_str, color = color, x=10, y=30 )#, 20, 0.05, 0.7)
        self.add_text(screen_state_str, color = color, x=10, y=50 )#, 20, 0.05, 0.7)

    def get_meta_data(self, meta_data_type: MetaDataType):
        self.reset_meta_data_table()
        box = self.get_layer_metadata_position(meta_data_type)
        if box:
            data = box.to_dict()
            data_frame = pd.DataFrame.from_dict(data.items())
            data_frame.columns = [KEYS, VALUES]
            self.set_meta_data_table(data_frame)
        return create_updating_data_table_by_callback(component_id=f'{self.get_component_id(meta_data_type)}-component',
                                                      data_frame=self.data_frame, sorted_column=KEYS, is_export=False)

    def get_metadata_by_type(self, line_type:str, meta_data_type: MetaDataType) -> list | None:
        all_lines = []
        if self.verify_metadata():
            frame_metadata = self.frame_metadata.get(meta_data_type.value)
            
            if frame_metadata:
                all_lines = [f for f in frame_metadata if 'keys' in f.keys() and 'type' in f['keys'] and f['keys']['type'] == line_type]
                #all_lines = [f for f in frame_metadata if 'keys' in f.keys() and f['keys']['type'] == line_type]

        if len(all_lines)==0:
            return []
        if len(all_lines)>1:
            error_message = "**** Too many presence lines. Case not handeled yet ***"
            print (error_message)
            # self.add_text(error_message, is_online, color = RED_COLOR, x=0.5, y=0.5 )
        all_lines = all_lines[0]
            
        return all_lines

    def get_layer_metadata_position(self, meta_data_type: MetaDataType) -> Box | None:
        if self.verify_metadata():
            frame_metadata = self.frame_metadata.get(meta_data_type.value)
            if frame_metadata and len(frame_metadata) > 1 and len(frame_metadata[2][MESSAGE][OBJECTS]) > 0:
                for obj in frame_metadata[2][MESSAGE][OBJECTS]:
                    #if obj[SOURCE] == BODY_DETECTION:
                        #return Box(obj[BOUNDING_BOX])
                    if obj['Object']['Source'] == BODY_DETECTION:
                        return Box(obj['Object']['BoundingBox'])
        return None        

    def handle_selected_box_by_click_event(self, clicked_rect: GUIRect, meta_data_type: MetaDataType):
        """
        Handling a box in case selected on the plot.
        :param box:
        :param meta_data_type:
        :return: plot with new data on it
        """
        for curr_rect in self.all_GUI_elements[RECTS]:
            if curr_rect == clicked_rect:
                curr_rect.color = Color.Blue
        # self.add_layer_content(meta_data_type)
        self.draw_layer_GUI_elements(False)

        # self.add_rectangular(False, box.left, box.top, box.right, box.bottom, Color.Green)
        return self.plotly_frame_with_layers
