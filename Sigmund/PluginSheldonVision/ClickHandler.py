import dash
import math
import PluginSheldonVision.Helpers as SheldonHelpers
from PluginSheldonVision.MetaDataHandler import MetaDataType
from PluginSheldonVision.PlotLayers.PlotLayerBase import PlotLayerBase, RECTS
from PluginSheldonVision.Constants import POINTS, X, Y
from PluginSheldonVision.PlotLayers.Elements import Box, GUIRect


class ClickHandler:

    def __init__(self, primary_plot_layer, secondary_plot_layer, get_graphs_div_display_status, create_offline_graph):
        self.primary_plot_layer = primary_plot_layer
        self.secondary_plot_layer = secondary_plot_layer
        self.get_graphs_div_display_status = get_graphs_div_display_status
        self.create_offline_graph = create_offline_graph

    def handle_figure_click(self, figure_click_data: dict, meta_data_type: MetaDataType, current_frame_number: int) -> list:
        x = figure_click_data[POINTS][0][X]
        y = figure_click_data[POINTS][0][Y]
        is_primary = meta_data_type == MetaDataType.PRIMARY
        plot_layer = self.primary_plot_layer if is_primary else self.secondary_plot_layer
        all_layers_on_figure = self.find_all_layers(plot_layer, meta_data_type)
        closest_rect, closest_layer = self.find_relevant_GUI_element(all_layers_on_figure, x, y)
        #print("Closest element: ", closest_rect.left if closest_rect else "NONE")

        if closest_layer:
            offline_graph = self.create_offline_graph(current_frame_number, meta_data_type, closest_rect, closest_layer) if is_primary else dash.no_update
            offline_graph_secondary = self.create_offline_graph(current_frame_number, meta_data_type, closest_rect, closest_layer) if not is_primary else dash.no_update
        else:
            offline_graph = dash.no_update
            offline_graph_secondary = dash.no_update

        main_ui_output_callbacks = SheldonHelpers.prepare_main_ui_output_callbacks(
            primary_graph_offline_figure=offline_graph,
            secondary_graph_offline_figure=offline_graph_secondary)

        main_ui_output_callbacks.extend(self.get_graphs_div_display_status())
        return main_ui_output_callbacks

    def find_relevant_GUI_element(self, all_layers_on_figure: dict[str, dict], x: int, y: int) -> tuple[GUIRect, str] | tuple[None, None]:
        min_dist = 9999
        closest_GUI_element = (None, None)

        for layer_name, GUI_elements_in_layer in all_layers_on_figure.items():
            all_GUI_rects = GUI_elements_in_layer[RECTS]
            for rect in all_GUI_rects:
                in_range, dist = self.calculate_distance_from_rect(rect, x, y)
                if in_range and dist < min_dist:
                    min_dist = dist
                    closest_GUI_element = (rect, layer_name)
        
        return closest_GUI_element

    def calculate_distance_from_rect(self, rect: GUIRect, x: int, y: int) -> tuple[bool, float]:
        PADDING = -10
        Dr = rect.right - x
        Dl = x - rect.left
        Db = rect.bottom - y
        Dt = y - rect.top

        in_range = (Dr > PADDING) and (Dl > PADDING) and (Db > PADDING) and (Dt > PADDING)
        min_dist = min(abs(Dr), abs(Dl), abs(Db), abs(Dt))

        return in_range, min_dist


    def find_relevant_box(self, all_boxes: dict[str, Box], x: int, y: int) -> tuple[dict, str] | tuple[None, None]:
        closest_box = {}
        for layer, box in all_boxes.items():
            if box:
                min_distance = self.calculate_min_distance_from_layer(box, x, y)
                if not closest_box:
                    closest_box[min_distance] = (box, layer)
                elif min_distance < list(closest_box.keys())[0]:
                    closest_box.clear()
                    closest_box[min_distance] = (box, layer)

        return list(closest_box.values())[0] if closest_box else (None, None)

    def calculate_min_distance_from_layer(self, box: Box, x: int, y: int) -> float:
        min_distance_from_top_line = self.calculate_distance_from_dot(x, y, box.left, box.top, box.right, None, None)
        min_distance_from_right_line = self.calculate_distance_from_dot(x, y, box.right, box.top, None, box.bottom, None)
        min_distance_from_left_line = self.calculate_distance_from_dot(x, y, box.left, box.top, None, box.bottom, None)
        min_distance_from_bottom_line = self.calculate_distance_from_dot(x, y, box.left, box.bottom, box.right, None, None)
        return min(min_distance_from_top_line, min_distance_from_right_line, min_distance_from_left_line, min_distance_from_bottom_line)

    def calculate_distance_from_dot(self, x: float, y: float, destination_x: float, destination_y: float, max_x: float = None,
                                    max_y: float = None, current_distance: float = None) -> float:
        distance = math.sqrt(((x - destination_x) ** 2) + ((y - destination_y) ** 2))
        if current_distance is not None and distance > current_distance:
            return current_distance
        if current_distance is None or distance < current_distance:
            current_distance = distance
            if max_x and max_x > destination_x:
                return self.calculate_distance_from_dot(x, y, destination_x + 1, destination_y, max_x, None, current_distance)
            elif max_y and max_y > destination_y:
                return self.calculate_distance_from_dot(x, y, destination_x, destination_y + 1, None, max_y, current_distance)
            else:
                return distance

    def find_all_layers(self, plot_layer: PlotLayerBase, meta_data_type: MetaDataType) -> dict[str, ]:
        layers_GUI_elements = {}
        for layer in plot_layer.keys():
            if plot_layer[layer].active():
                layer_name = plot_layer[layer].layer_name()
                layers_GUI_elements[layer_name] = plot_layer[layer].get_all_GUI_elements()
        return layers_GUI_elements
