import base64
import io
import logging
import time
import sys
import os
import PIL
import pandas as pd
from enum import Enum
import plotly.express as px
from PIL import Image
import plotly.graph_objects as go
import threading
from dash import html, dcc, ctx
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import tkinter as tk
from tkinter import filedialog
from typing import Tuple, Dict
import dash_mantine_components as dmc

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import PluginSheldonVision.Helpers as sheldon_helpers
from PluginSheldonVision.Exceptions import FrameRangeNotValid
import PluginSheldonVision.Constants as SheldonVisionConstants
from PluginSheldonVision.PlotLayers.BoundingBoxLayer import BoundingBoxLayer, BOUNDING_BOX_LAYER_NAME
from PluginSheldonVision.PlotLayers.GTLogLayer import GTLogLayer, GT_LOG_LAYER_NAME

from PluginSheldonVision.PlotLayers.BoundingBoxLayerForMF import BoundingBoxLayerForMF, BOUNDING_BOX_LAYER_FOR_MF_NAME
from PluginSheldonVision.PlotLayers.TestTextLayer import TestTextLayer, TEST_TEXT_LAYER_NAME
from PluginSheldonVision.PlotLayers.TestLayer import TestLayer, TEST_LAYER_NAME
from PluginSheldonVision.PlotLayers.Elements import GUIRect
from PluginSheldonVision.MetaDataHandler import MetaDataHandler, MetaDataType, is_checked_modify_value, IS_CHECKED_ID, COLUMN_ID, ROW, \
    VIDEO_LOCATION
from SheldonCommon.Constants import RECORDING_INFO_CARD_ID, BACK_BUTTON_ID, FORWARD_BUTTON_ID, PLAY_BUTTON_ID, CYCLE_RANGE_SLIDER_ID, \
    MAIN_HTML_DIV_ELEMENT_ID, FRAME_INPUT_ID, PROP_ID, INVALID_RECORDING_INFO_MESSAGE, EVENTS_TIMEOUT_SECONDS, PRIMARY_GRAPH_DROPDOWN_ID, \
    SECONDARY_GRAPH_DROPDOWN_ID, EMPTY_CALLBACK_ID, ID
from SheldonCommon.SheldonBase import *
from SheldonCommon import ReusableComponents as rc
from SheldonCommon.ReusableComponents import BOOTSTRAP_ICONS
from PluginSheldonVision.ConfigurationHandler import ConfigurationHandler
from SigmundProtobufPy.CloseType_pb2 import SigmundCloseTypeProto
from PluginSheldonVision.ClickHandler import ClickHandler
from PluginSheldonVision.MailHandler import MailHandler
from PluginSheldonVision.NotificationsHandler import Notification

setting_file_name = os.path.abspath(os.path.join(__file__, '..', 'settings.json'))
settings = ConfigurationHandler(setting_file_name,perform_validation=False)

global app
app = None


def set_app_instance(server):
    global app
    if app is None:
        app = dash.Dash(__name__,
                        external_stylesheets=[dbc.themes.BOOTSTRAP, rc.MATERIAlIZE_CSS, BOOTSTRAP_ICONS],
                        suppress_callback_exceptions=False, server=server, update_title=None)
        app.title = SheldonVisionConstants.SHELDON_VISION_UI_TITLE
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)


def run_server():
    app.run_server(debug=False)


class AutoRunStatus(Enum):
    UNAVAILABLE = 0
    WAITING = 1
    LOADING = 2


class MainSheldonVisionUI:
    def __init__(self, send_get_current_frame_method, get_current_frame_method, clear_frames_queue_method, send_stop_message_method,
                 send_new_load_request_method, get_current_frame_number_method, send_set_frame_message_method,
                 send_previous_message_method, send_next_frame_message_method, send_pause_message_method, send_play_message_method,
                 get_recording_information_method, get_frames_range_method, log_method, validate_path, get_fps, set_fps,
                 close_network, send_upload_file_to_blob_method, send_download_file_from_bolb_method, verify_blob_path,
                 get_files_list_on_blob, files_list_on_blob, verify_local_path, server, configurations, storage_account_name,
                 container_name):
        set_app_instance(server)
        self.close_network = close_network
        self.log_method = log_method
        self.get_frames_range_callback = get_frames_range_method
        self.get_recording_information_callback = get_recording_information_method
        self.send_play_message_method_callback = send_play_message_method
        self.send_pause_message_method_callback = send_pause_message_method
        self.send_previous_message_method_callback = send_previous_message_method
        self.send_next_frame_message_method_callback = send_next_frame_message_method
        self.send_set_frame_message_method_callback = send_set_frame_message_method
        self.get_current_frame_number_method_callback = get_current_frame_number_method
        self.send_new_load_request_method_callback = send_new_load_request_method
        self.send_stop_message_method_callback = send_stop_message_method
        self.clear_frames_queue_method_callback = clear_frames_queue_method
        self.get_current_frame_method_callback = get_current_frame_method
        self.send_get_current_frame_method_callback = send_get_current_frame_method
        self.validate_path_callback = validate_path
        self.get_fps_callback = get_fps
        self.set_fps_callback = set_fps
        self.upload_file_to_blob_callback = send_upload_file_to_blob_method
        self.download_file_from_blob_callback = send_download_file_from_bolb_method
        self.get_files_list_on_blob = get_files_list_on_blob
        self.files_list_on_blob = files_list_on_blob
        self.verify_blob_path = verify_blob_path
        self.verify_local_path = verify_local_path
        self.storage_account_name = storage_account_name
        self.container_name = container_name
        self.reload_ui_event = threading.Event()
        self.main_div_children = None
        self.player_frames = 0
        self.is_playing = False
        self.is_ready_to_load_metadata = False
        self.is_decimated = False
        self.speed = 1
        self.frames_range = [0, 0]
        self.notifications: Notification = Notification()
        self.configurations = ConfigurationHandler(configuration_file_path=configurations, notifications=self.notifications)
        self.meta_data_handler = MetaDataHandler(verify_blob_path, get_files_list_on_blob, files_list_on_blob, verify_local_path,
                                                 self.download_file_from_blob, notifications=self.notifications)
        self.are_player_buttons_disabled = True
        self.__root_tk = None
        self.fig: Dict[MetaDataType, Image] = {MetaDataType.PRIMARY: None, MetaDataType.SECONDARY: None}
        self.debug_data_frame = None
        self.last_figure_layout = None
        self.previous_video_file_name = None
        self.on_loading = True
        self.primary_plot_layer = self.__initialize_plot_layers_handlers(MetaDataType.PRIMARY)
        self.secondary_plot_layer = self.__initialize_plot_layers_handlers(MetaDataType.SECONDARY)
        self.autorun_from_mail = {}
        self.waiting_autorun_main_ui = AutoRunStatus.UNAVAILABLE
        self.waiting_autorun_metadata_primary = AutoRunStatus.UNAVAILABLE
        self.waiting_autorun_metadata_secondary = AutoRunStatus.UNAVAILABLE
        self.loading_hidden = True
        self.__page_refresh = False
        self.current_frame_number = 0
        self.__play_decimation_thread = None
        self.base_path_video = ConfigurationHandler(os.path.abspath(os.path.join(__file__, '..', 'settings.json')),
                                                    perform_validation=False).get_item('BASE_PATH_VIDEO', 'General')
        self.jump_path_http = None
        self.waiting_jump_loading = AutoRunStatus.UNAVAILABLE
        self.is_on_dragging = False

        self.alternative_base_path_video = settings.get_item('BASE_PATH_VIDEO', 'General') #TODO: Take that from config file
        
    def __initialize_plot_layers_handlers(self, meta_data_type: MetaDataType):
        """
        Return the plot handler per layer
        :rtype: dic
        """
        layers = self.configurations.get_item(item_name=SheldonVisionConstants.CONFIG_LAYERS_LIST, section=str(meta_data_type.value))
        if layers:
            layers_dict = {layer: globals()[layer](self.meta_data_handler) for layer in layers}
            return layers_dict
        else:
            # default when no config file at all or no argument in config file
            return {
                BOUNDING_BOX_LAYER_NAME: BoundingBoxLayer(self.meta_data_handler)
                # Add new handler for new layer here
            }

    def reload_application(self):
        self.reload_ui_event.set()

    def start_ui(self):
        """
        Start the UI
        @return:
        """

        # self.__validate_basic_data_to_load_ui()
        self.__create_app()

    def __on_interval_kill_application(self, n):
        if self.on_display_refresh.wait(EVENTS_TIMEOUT_SECONDS):
            self.on_display_refresh = threading.Event()
            set_app_instance()
            shutdown()
        return dash.no_update

    def __get_graphs_div_display_status(self):
        """
        Return the display status of the graphs div
        @return:
        """
        slider_disabled = self.previous_video_file_name is None
        input_disabled = self.previous_video_file_name is None or self.is_playing
        return [not self.is_playing, self.is_playing, not self.is_playing, self.is_playing, input_disabled, slider_disabled]

    def __update_main_ui(self,
                         fast_back_button_n_clicks, pause_button_n_clicks, primary_graph_dropdown_value, secondary_graph_dropdown_value,
                         browse_button_n_clicks, back_button_n_clicks, next_button_n_clicks, slider_click, interval_tick,
                         frame_input_value, active_debug_table_cell, primary_figure_click, secondary_figure_click,
                         primary_relayout_data, secondary_relayout_data, slider_fps_value, fps_input, autorun_hidden,
                         metadata_file_path_primary, metadata_file_path_secondary, decimation_n_clicks, speed_slider, speed_input,
                         drop_down_video_local, drop_down_video_blob, video_modal_ok, video_modal_cancel,
						 local_file_not_found_submit_n_click, local_file_not_found_cancel_n_click, frames_slider_value, debug_data_table,
                         primary_general_div, secondary_general_div, slider_fps_style, slider_speed_style,
                         video_modal_input):
        """
                Main update method for the UI.
                Parameters:
                -----------
                    fast_back_button_n_clicks : Number of clicks on the fast back button.
                    pause_button_n_clicks : Number of clicks on the pause button.
                    primary_graph_dropdown_value : Value of the primary graph dropdown.
                    secondary_graph_dropdown_value : Value of the secondary graph dropdown.
                    browse_button_n_clicks : Number of clicks on the browse button.
                    back_button_n_clicks : Number of clicks on the back button.
                    next_button_n_clicks : Number of clicks on the next button.
                    slider_click : Number of clicks on the slider.
                    interval_tick : The number of ticks in an interval of the slider.
                    frame_input_value : Value of current frame.
                    active_debug_table_cell : The specific cell a user chosen.
                    uri_input_value : The URI inserted.
                    primary_figure_click: click location on primary figure
                    secondary_figure_click: click location on secondary figure
                    primary_relayout_data : The primary relayout data.
                    secondary_relayout_data : The secondary relayout data.
                    frames_slider_value : Frame slider value.
                    debug_data_table : The debug data info in a table.
                Returns:
                --------
                    main_ui_output_callbacks : A series of callbacks modified following an event.
                """
        triggered_callback = []
        for index in range(0, len(dash.callback_context.triggered)):
            triggered_callback.append(dash.callback_context.triggered[index][PROP_ID])

        # Initial load of the application
        if any(EMPTY_CALLBACK_ID == s for s in triggered_callback):
            # Stop the player when GUI is loaded
            self.send_stop_message_method_callback()
            return self.__on_page_loading()

        # handle figures zoom level
        if any(SheldonVisionConstants.RELAYOUT_DATA_EVENT in s for s in triggered_callback):
            caller_view = [view for view in triggered_callback if SheldonVisionConstants.RELAYOUT_DATA_EVENT in view]
            relevant_view = MetaDataType.PRIMARY if MetaDataType.PRIMARY.value in caller_view[0] else MetaDataType.SECONDARY
            if self.__page_refresh:
                self.__page_refresh = False
                return self.__on_page_refresh()
            video_path = self.configurations.get_item(SheldonVisionConstants.CONFIG_VIDEO_FILE_PATH)
            if self.on_loading and video_path:
                self.on_loading = False
                return self.__on_video_browser_button_click(file_name=video_path, is_from_dialog=False)
            elif self.on_loading:
                self.on_loading = False
                return self.__on_page_loading()
            elif self.fig[relevant_view] is not None:
                success, ret = self.__handle_figures_zoom_level(triggered_callback, primary_relayout_data, secondary_relayout_data)
                if success:
                    return ret
                else:
                    return self.__on_page_refresh()
            else:
                return self.__on_page_refresh()

        if any(SheldonVisionConstants.FPS_INPUT_ID in s for s in triggered_callback):
            logging.info(f"On {SheldonVisionConstants.FPS_INPUT_ID} value changed selected fps: {fps_input}\n")
            return self.__on_fps_change(fps_input)

        if any(SheldonVisionConstants.FPS_SLIDER_ID in s for s in triggered_callback):
            logging.info(f"On {SheldonVisionConstants.FPS_SLIDER_ID} value changed selected fps: {slider_fps_value}\n")
            return self.__on_fps_change(slider_fps_value)

        if any(SheldonVisionConstants.DECIMATION_BUTTON_ID in s for s in triggered_callback):
            logging.info(f"On {SheldonVisionConstants.DECIMATION_BUTTON_ID} button clicked\n")
            return self.__on_decimation_button_clicked(slider_fps_style, slider_speed_style)

        if any(SheldonVisionConstants.DECIMATION_SPEED_SLIDER_ID in s for s in triggered_callback):
            logging.info(f"On {SheldonVisionConstants.DECIMATION_SPEED_SLIDER_ID} value changed selected speed: {speed_slider}\n")
            return self.__on_speed_change(speed_slider)

        if any(SheldonVisionConstants.DECIMATION_SPEED_INPUT_ID in s for s in triggered_callback):
            logging.info(f"On {SheldonVisionConstants.DECIMATION_BUTTON_ID}  value changed selected speed: {speed_input}\n")
            float_speed_input = float(speed_input)
            values = SheldonVisionConstants.DECIMATION_SPEED_VALUES
            speed_value = values.index(float_speed_input) if float_speed_input in values else speed_slider
            return self.__on_speed_change(speed_value)

        file_not_found_submit = any(
            f"{SheldonVisionConstants.LOCAL_FILE_NOT_FOUND_ID}.{SheldonVisionConstants.SUBMIT_N_CLICKS}"
            in s for s in triggered_callback)
        file_not_found_cancel = any(
            f"{SheldonVisionConstants.LOCAL_FILE_NOT_FOUND_ID}.{SheldonVisionConstants.CANCEL_N_CLICKS}"
            in s for s in triggered_callback)

        if file_not_found_cancel:
            main_ui_output_callbacks = sheldon_helpers.prepare_main_ui_output_callbacks()
            main_ui_output_callbacks.extend(self.__get_graphs_div_display_status())
            return main_ui_output_callbacks

        # handle on click on debug table cell
        if file_not_found_submit or \
                (any(f"{SheldonVisionConstants.DEBUG_EDITABLE_TABLE}.{SheldonVisionConstants.ACTIVE_CELL_ID}"
                     in s for s in
                     triggered_callback) and not file_not_found_cancel) and active_debug_table_cell is not None:
            if active_debug_table_cell[COLUMN_ID] == IS_CHECKED_ID:
                main_ui_output_callbacks = sheldon_helpers.prepare_main_ui_output_callbacks()
                main_ui_output_callbacks.extend(self.__get_graphs_div_display_status())
                return main_ui_output_callbacks
            return self.__load_new_debug_recording(active_debug_table_cell, debug_data_table)

        # On slider value changed update the frames slider value
        if any(CYCLE_RANGE_SLIDER_ID in s for s in triggered_callback):
            logging.info(f"On {CYCLE_RANGE_SLIDER_ID} value changed selected frame:{frames_slider_value}\n")
            self.current_frame_number = frames_slider_value
            self.is_on_dragging = False
            return self.__create_offline_graph_for_frame(frames_slider_value)

        # handle input dialog for frame number
        if any(FRAME_INPUT_ID in s for s in triggered_callback):
            logging.info(f"On {FRAME_INPUT_ID} value change selected frame:{frame_input_value}\n")
            self.current_frame_number = int(frame_input_value)
            return self.__create_offline_graph_for_frame(int(frame_input_value))

        # Update layers by dropdown selection
        if any(PRIMARY_GRAPH_DROPDOWN_ID in s for s in triggered_callback) or any(
                SECONDARY_GRAPH_DROPDOWN_ID in s for s in triggered_callback):
            logging.info(f"On {PRIMARY_GRAPH_DROPDOWN_ID} or {SECONDARY_GRAPH_DROPDOWN_ID} \n")

            return self.__on_dropdown_selection_change(primary_graph_dropdown_value, secondary_graph_dropdown_value,
                                                       frames_slider_value)
        # handle on click on pause button click
        if any(SheldonVisionConstants.PAUSE_BUTTON_ID in s for s in triggered_callback):
            logging.info(f"On Pause, current slider frame number{frames_slider_value} \n")
            return self.__on_pause_button_click()

        # Update slider and input value using interval
        if any(SheldonVisionConstants.SLIDER_INTERVAL_ID in s for s in triggered_callback):
            return self.__on_slider_interval_tick(pause_button_n_clicks, frames_slider_value)

        if any(SheldonVisionConstants.FAST_BACK_BUTTON_ID in s for s in triggered_callback):
            logging.info(f"On {SheldonVisionConstants.FAST_BACK_BUTTON_ID}\n")
            self.current_frame_number = 0
            return self.__create_offline_graph_for_frame(0)

        if any(SheldonVisionConstants.BROWSE_BUTTON_ID in s for s in triggered_callback):
            if any(SheldonVisionConstants.DROP_DOWN_VIDEO_BLOB in s for s in triggered_callback):
                main_ui_output_callbacks = sheldon_helpers.prepare_main_ui_output_callbacks(video_modal_is_open=True)
                main_ui_output_callbacks.extend(self.__get_graphs_div_display_status())
                return main_ui_output_callbacks
            logging.info(f"On {SheldonVisionConstants.BROWSE_BUTTON_ID}\n")
            return self.__on_video_browser_button_click()

        if any(SheldonVisionConstants.INPUT_VIDEO_MODAL_OK in s for s in triggered_callback):
            logging.info(f"On {SheldonVisionConstants.INPUT_METADATA_MODAL_OK}\n")
            main_ui_output_callbacks = self.__on_video_browser_button_click(file_name=video_modal_input, is_from_dialog=False)
            sheldon_helpers.modify_main_ui_output_callbacks(main_ui_output_callbacks, video_modal_is_open=False)
            return main_ui_output_callbacks

        if any(SheldonVisionConstants.INPUT_VIDEO_MODAL_CANCEL in s for s in triggered_callback):
            main_ui_output_callbacks = sheldon_helpers.prepare_main_ui_output_callbacks(video_modal_is_open=False)
            main_ui_output_callbacks.extend(self.__get_graphs_div_display_status())
            return main_ui_output_callbacks

        if any(SheldonVisionConstants.LOADING_FROM_MAIL_LABEL_ID in s for s in triggered_callback):
            if self.waiting_autorun_main_ui == AutoRunStatus.WAITING:
                self.waiting_autorun_main_ui = AutoRunStatus.LOADING
                return self.__on_autorun()
            else:
                main_ui_output_callbacks = sheldon_helpers.prepare_main_ui_output_callbacks()
                main_ui_output_callbacks.extend(self.__get_graphs_div_display_status())
                return main_ui_output_callbacks

        if any(SheldonVisionConstants.PAUSE_BUTTON_ID not in s for s in triggered_callback) and self.is_playing:
            self.send_set_frame_message_method_callback(frames_slider_value)

        # Load first metadata for frame (Offline Graph) after metadata file is loaded
        if not self.is_playing:
            frame_number = self.get_current_frame_number_method_callback()
            if any(SheldonVisionConstants.METADATA_SECONDARY_LOADED_FILES_LIST_ID in s for s in triggered_callback) and \
                    frame_number is not None:
                self.current_frame_number = frame_number
                return self.__create_offline_graph_for_frame(frame_number, MetaDataType.SECONDARY)
            if any(SheldonVisionConstants.METADATA_LOADED_FILES_LIST_ID in s for s in triggered_callback) and \
                    frame_number is not None:
                self.current_frame_number = frame_number
                return self.__create_offline_graph_for_frame(frame_number, MetaDataType.PRIMARY)

        if self.current_frame_number > 0 and any(BACK_BUTTON_ID in s for s in triggered_callback):
            if self.is_decimated:
                self.current_frame_number = self.meta_data_handler.get_decimation_value(self.current_frame_number, is_next_frame=False)
            elif self.current_frame_number - SheldonVisionConstants.MAX_NUM_FRAMES_SELECTED > self.frames_range[0]:
                self.current_frame_number = self.current_frame_number - SheldonVisionConstants.MAX_NUM_FRAMES_SELECTED

        elif self.current_frame_number >= 0 and any(FORWARD_BUTTON_ID in s for s in triggered_callback):
            if self.is_decimated:
                self.current_frame_number = self.meta_data_handler.get_decimation_value(self.current_frame_number, is_next_frame=True)
            elif self.current_frame_number + SheldonVisionConstants.MAX_NUM_FRAMES_SELECTED < self.frames_range[1]:
                self.current_frame_number = self.current_frame_number + SheldonVisionConstants.MAX_NUM_FRAMES_SELECTED

        if any(SheldonVisionConstants.CLICK_DATA_EVENT in s for s in triggered_callback):
            current_frame_number = self.get_current_frame_number_method_callback()
            is_primary = ctx.triggered_id == SheldonVisionConstants.PRIMARY_GRAPH_OFFLINE_FIGURE_ID
            figure_click_data = primary_figure_click if is_primary else secondary_figure_click
            meta_data_type = MetaDataType.PRIMARY if is_primary else MetaDataType.SECONDARY
            click_handler = ClickHandler(self.primary_plot_layer, self.secondary_plot_layer, self.__get_graphs_div_display_status, self.create_offline_graph)
            return click_handler.handle_figure_click(figure_click_data, meta_data_type, current_frame_number)

        logging.info(f"On {BACK_BUTTON_ID} or {FORWARD_BUTTON_ID}\n")
        return self.__create_offline_graph_for_frame(self.current_frame_number)

    def __on_page_loading(self):
        conf_div = html.Div(SheldonVisionConstants.NO_SETTINGS_FILE_SELECTED, style=SheldonVisionConstants.INDICATION_TEXT_STYLE) if \
            not self.configurations.is_ok else html.Div(self.configurations.configuration_file_path)

        main_ui_output_callbacks = sheldon_helpers.prepare_main_ui_output_callbacks(
            video_files_list_label=html.Div(SheldonVisionConstants.NO_FILES_SELECTED,
                                            style=SheldonVisionConstants.HIGHLIGHT_TEXT_STYLE),
            settings_file=conf_div
        )
        main_ui_output_callbacks.extend(self.__get_graphs_div_display_status())
        return main_ui_output_callbacks

    def __on_page_refresh(self):
        """
        Handling page refresh (F5)
        :return:
        """
        self.__page_refresh = True
        time.sleep(0.1)  # short sleep for frame_number to update after refresh
        frame_number = self.get_current_frame_number_method_callback()
        offline_graph = self.create_offline_graph(frame_number, MetaDataType.PRIMARY)
        offline_graph_secondary = self.create_offline_graph(frame_number, MetaDataType.SECONDARY)
        primary_metadata_general = self.create_meta_data_general(MetaDataType.PRIMARY)
        secondary_metadata_general = self.create_meta_data_general(MetaDataType.SECONDARY)

        conf_div = html.Div(SheldonVisionConstants.NO_SETTINGS_FILE_SELECTED, style=SheldonVisionConstants.INDICATION_TEXT_STYLE) if \
            not self.configurations.is_ok else html.Div(self.configurations.configuration_file_path)

        video_div = html.Div(self.previous_video_file_name) if self.previous_video_file_name else \
            html.Div(SheldonVisionConstants.NO_FILES_SELECTED, style=SheldonVisionConstants.HIGHLIGHT_TEXT_STYLE)

        range_marks = self.__get_range_marks_by_clip_name()
        marks = self.__set_marks(range_marks)

        self.fps = self.configurations.get_item(SheldonVisionConstants.CONFIG_FPS)
        if not self.fps:
            self.fps = self.get_fps_callback()

        main_ui_output_callbacks = sheldon_helpers.prepare_main_ui_output_callbacks(
            slider_value=int(frame_number) if frame_number else dash.no_update,
            frame_input_number_value=frame_number if frame_number else dash.no_update,
            primary_graph_offline_figure=offline_graph,
            secondary_graph_offline_figure=offline_graph_secondary,
            primary_metadata_general=primary_metadata_general,
            secondary_metadata_general=secondary_metadata_general,
            video_files_list_label=video_div,
            settings_file=conf_div,
            slider_min_value=self.frames_range[0],
            slider_max_value=self.frames_range[1],
            slider_fps_value=self.fps,
            fps_input_value=self.fps,
            slider_marks_value=marks
        )
        main_ui_output_callbacks.extend(self.__get_graphs_div_display_status())
        return main_ui_output_callbacks

    def __set_main_div_children(self):
        """
        Set the children of the main div
        @return:
        """
        recording_info = self.get_recording_information_callback()
        controls = self.__create_controls(self.frames_range, recording_info)
        self.main_div_children = \
            [
                dcc.ConfirmDialog(
                    id=SheldonVisionConstants.LOCAL_FILE_NOT_FOUND_ID,
                    displayed=False,
                    message="Local Metadata file not found, do you want to try downloading from blob?",
                ),
                dcc.ConfirmDialog(
                    id=SheldonVisionConstants.ERROR_MESSAGE,
                    message='',
                ),
                dcc.ConfirmDialog(
                    id=SheldonVisionConstants.ERROR_MESSAGE_EMAIL,
                    message='',
                ),
                rc.input_modal(component_id=SheldonVisionConstants.INPUT_METADATA_MODAL, title="Metadata from Blob", label_text="Metadata Path:"),
                rc.input_modal(component_id=SheldonVisionConstants.INPUT_VIDEO_MODAL, title="Video from Blob", label_text="Video Path:"),
                html.Div(id="notifications-container"),
                html.Div(rc.Interval(component_id=SheldonVisionConstants.SLIDER_INTERVAL_ID, interval=100)),
                html.Div(rc.Interval(component_id=SheldonVisionConstants.AUTORUN_FROM_MAIL_INTERVAL_ID, interval=5000, disabled=False)),
                html.Div(rc.Interval(component_id=SheldonVisionConstants.JUMP_LOAD_INTERVAL_ID, interval=5000, disabled=False)),
                html.Div(rc.Interval(component_id=SheldonVisionConstants.ALERTS_INTERVAL_ID, interval=1000, disabled=False)),
                # Navigation Bar View
                self.__create_nav_bar(),
                rc.Row([
                    rc.Col(
                        rc.Card(rc.CardContent(rc.Row([
                            rc.Col(controls[SheldonVisionConstants.ButtonsIndex.FAST_BACK_BUTTON_INDEX.value], width=0,
                                   style=SheldonVisionConstants.BUTTONS_COLUMN_STYLE),  # Fast Back Button
                            rc.Col(controls[SheldonVisionConstants.ButtonsIndex.BACK_BUTTON_INDEX.value], width=0,
                                   style=SheldonVisionConstants.BUTTONS_COLUMN_STYLE),  # Back Button
                            rc.Col(controls[SheldonVisionConstants.ButtonsIndex.PLAY_BUTTON_INDEX.value], width=0,
                                   style=SheldonVisionConstants.BUTTONS_COLUMN_STYLE),  # Play Button
                            rc.Col(controls[SheldonVisionConstants.ButtonsIndex.PAUSE_BUTTON_INDEX.value], width=0,
                                   style=SheldonVisionConstants.BUTTONS_COLUMN_STYLE),  # Pause Button
                            rc.Col(controls[SheldonVisionConstants.ButtonsIndex.NEXT_BUTTON_INDEX.value], width=1,
                                   style=SheldonVisionConstants.BUTTONS_COLUMN_STYLE),  # Next Button
                            rc.Col(controls[SheldonVisionConstants.ButtonsIndex.VIDEO_BROWSER_BUTTON_INDEX.value],
                                   width=0,
                                   style=SheldonVisionConstants.BUTTONS_COLUMN_STYLE),  # Video Browser
                            rc.Col(controls[SheldonVisionConstants.ButtonsIndex.METADATA_PRIMARY_BROWSER_BUTTON_INDEX.value],
                                   width=0,
                                   style=SheldonVisionConstants.BUTTONS_COLUMN_STYLE),  # MetaData Browser
                            rc.Col(controls[SheldonVisionConstants.ButtonsIndex.METADATA_SECONDARY_BROWSER_BUTTON_INDEX.value],
                                   width=0,
                                   style=SheldonVisionConstants.BUTTONS_COLUMN_STYLE),  # MetaData Secondary Browser
                            rc.Col(controls[
                                       SheldonVisionConstants.ButtonsIndex.MULTIPLE_RECORDING_BROWSER_BUTTON_INDEX.value],
                                   width=0,
                                   style=SheldonVisionConstants.BUTTONS_COLUMN_STYLE),  # Uri Input
                            rc.Col(controls[
                                       SheldonVisionConstants.ButtonsIndex.SEND_MAIL_BUTTON_INDEX.value],
                                   width=0,
                                   style=SheldonVisionConstants.BUTTONS_COLUMN_STYLE),
                            rc.Col(controls[
                                        SheldonVisionConstants.ButtonsIndex.DECIMATION_BUTTON_INDEX.value],
                                   width=0,
                                   style=SheldonVisionConstants.BUTTONS_COLUMN_STYLE),  # Decimation button
                            rc.Col(controls[
                                       SheldonVisionConstants.ButtonsIndex.CLOSE_NETWORK_BUTTON_INDEX.value],
                                   width=0,
                                   style=SheldonVisionConstants.CLOSE_APPLICATION_COLUMN_STYLE),
                            rc.Col(html.Label("Loading from mail", id=SheldonVisionConstants.LOADING_FROM_MAIL_LABEL_ID, hidden=True,
                                              style={'background-color': 'DarkGreen', 'color': 'white', 'margin': '10px'}), width=0),
                            rc.Col(html.Label("Loading jump", id=SheldonVisionConstants.JUMP_LOADING_LABEL_ID, hidden=True,
                                              style={'background-color': 'DarkGreen', 'color': 'white', 'margin': '10px'}), width=0),
                            # Frame Slider
                            rc.Col(controls[SheldonVisionConstants.ButtonsIndex.SLIDER_INDEX.value], width=9),
                            rc.Col([
                                # FPS Slider
                                rc.Col(controls[SheldonVisionConstants.ButtonsIndex.SLIDER_FPS_INDEX.value], width=10),
                                # Decimation Slider
                                rc.Col(controls[SheldonVisionConstants.ButtonsIndex.DECIMATION_SPEED_SLIDER_INDEX.value], width=10)],
                                width=3
                            ),
                            # Loaded Video Files
                            rc.Col([html.Label("Loaded Video:", style=SheldonVisionConstants.FONT_SIZE_20PX),
                                    html.Div(id=SheldonVisionConstants.VIDEO_LOADED_FILES_LIST_ID)], width=4),
                            # Loaded MetaData Files
                            rc.Col([html.Label("Loaded MetaData Primary:", style=SheldonVisionConstants.FONT_SIZE_20PX),
                                    html.Div(id=SheldonVisionConstants.METADATA_LOADED_FILES_LIST_ID)], width=4),
                            # Loaded MetaData Files Secondary
                            rc.Col([html.Label("Loaded MetaData Secondary:", style=SheldonVisionConstants.FONT_SIZE_20PX),
                                    html.Div(id=SheldonVisionConstants.METADATA_SECONDARY_LOADED_FILES_LIST_ID)], width=4)
                        ], style=SheldonVisionConstants.MARGIN_0_STYLE,
                        )), style=SheldonVisionConstants.MARGIN_0_STYLE),
                        width=12,
                    ),
                ], style=SheldonVisionConstants.MARGIN_0_STYLE),
                rc.Row([
                    # Primary Frame View
                    rc.Col([html.H5("Primary Frame View"), self.__create_frame_view(
                        SheldonVisionConstants.PRIMARY_GRAPH_ID,
                        PRIMARY_GRAPH_DROPDOWN_ID, "/video_feed_primary")],
                           width=6),
                    # Secondary Frame View
                    rc.Col([html.H5("Secondary Frame View"), self.__create_frame_view(
                        SheldonVisionConstants.SECONDARY_GRAPH_ID,
                        SECONDARY_GRAPH_DROPDOWN_ID, "/video_feed_secondary", MetaDataType.SECONDARY)],
                           width=6),
                ], style=SheldonVisionConstants.MARGIN_0_STYLE),
                rc.Row([
                    # MetaData Primary Frame View
                    rc.Col(self.__create_general_meta_data_view(SheldonVisionConstants.PRIMARY_GENERAL_DIV), width=6),
                    # MetaDataSecondary Frame View
                    rc.Col(self.__create_general_meta_data_view(SheldonVisionConstants.SECONDARY_GENERAL_DIV), width=6),
                ]),

                rc.Row([rc.Col([rc.Card(
                    [
                        rc.custom_button_with_icon(
                            component_id=SheldonVisionConstants.RECORDINGS_DEBUG_EXPORT_BUTTON_ID,
                            label="Export",
                            button_class_name=SheldonVisionConstants.BUTTON_CLASS_NAME, is_disabled=False,
                            button_style=SheldonVisionConstants.BUTTONS_STYLE),
                        html.Label(
                            "No jump file selected, Select jump(*.json) by browser button",
                            style=SheldonVisionConstants.FONT_SIZE_20PX,
                            id=SheldonVisionConstants.RECORDINGS_DEBUG_DATA_LABEL_ID,
                            hidden=False),
                        rc.create_updating_editable_data_table_by_callback(
                            component_id=SheldonVisionConstants.RECORDINGS_DEBUG_DATA_TABLE_ID,
                            data_frame=pd.DataFrame(),
                            buttons_class=SheldonVisionConstants.BUTTON_CLASS_NAME,
                            buttons_style=SheldonVisionConstants.BUTTONS_STYLE,
                            input_style=SheldonVisionConstants.WIDTH_100_STYLE,
                            is_export=False, sorted_column='Video Location', is_hidden=True)
                    ]),
                ],
                    width=12)]),
            ]

    def __create_app(self):
        self.__set_main_div_children()
        app.layout = dmc.MantineProvider(
            dmc.NotificationsProvider([
                html.Div(
                    id=MAIN_HTML_DIV_ELEMENT_ID,
                    style={"--slider_active": "teal"},
                    children=self.main_div_children
                )],
                limit=5,
                containerWidth=600))
        self.__create_callbacks()

    @staticmethod
    def __create_nav_bar():
        """
        Create the navigation bar on top of the page
        @return:
        """
        return html.Nav(
            html.Div(
                className="nav-wrapper teal",
                children=[
                    rc.Row([
                        rc.Col([
                            html.A(
                                "Sheldon Vision Plugin",
                                className="brand-logo",
                                style={"padding-left": "20px"}, )], width=3),
                        rc.Col([html.Label("Settings File:", style=SheldonVisionConstants.FONT_SIZE_15PX_WHITE)], width=0),
                        rc.Col([html.Div(id=SheldonVisionConstants.SETTINGS_LOADED_LABEL_ID)], width=3),
                        rc.Col([html.Label("Jump File:", style=SheldonVisionConstants.FONT_SIZE_15PX_WHITE)], width=0),
                        rc.Col([html.Div(id=SheldonVisionConstants.JUMP_FILE_ID)], width=4)])]
            ))

    def __create_controls(self, cycles_range, recording_info):
        """
        Create the controls components for the page
        @param cycles_range: for init the slider
        @param recording_info: for init the
        @return: list of controls used in the init if the page
        """
        if recording_info == INVALID_RECORDING_INFO_MESSAGE:
            db_info_card_content = rc.CardContent(id=RECORDING_INFO_CARD_ID,
                                                  children=[
                                                      rc.CardTitle("Video Information"),
                                                      html.Label("Invalid Video information.")
                                                  ])
        else:
            db_info_card_content = rc.CardContent(id=RECORDING_INFO_CARD_ID, children=[rc.CardTitle("Video General "
                                                                                                    "Information")])
        return [
            rc.custom_button_with_icon(component_id=BACK_BUTTON_ID,
                                       icon_class_name=SheldonVisionConstants.BACK_BUTTON_ICON_CLASS_NAME,
                                       button_class_name=SheldonVisionConstants.BUTTON_CLASS_NAME, is_disabled=True,
                                       icon_style=SheldonVisionConstants.BUTTONS_FONT_STYLE_PLAYER,
                                       button_style=SheldonVisionConstants.BUTTONS_STYLE,
                                       access_key=SheldonVisionConstants.BACK_BUTTON,
                                       title=SheldonVisionConstants.BACK_BUTTON_SHORTCUT),
            rc.custom_button_with_icon(component_id=PLAY_BUTTON_ID,
                                       icon_class_name=SheldonVisionConstants.PLAY_BUTTON_ICON_CLASS_NAME,
                                       button_class_name=SheldonVisionConstants.BUTTON_CLASS_NAME,
                                       is_disabled=self.previous_video_file_name is None,
                                       icon_style=SheldonVisionConstants.BUTTONS_FONT_STYLE_PLAYER,
                                       button_style=SheldonVisionConstants.BUTTONS_STYLE,
                                       access_key=SheldonVisionConstants.PLAY_BUTTON,
                                       title=SheldonVisionConstants.PLAY_BUTTON_SHORTCUT),
            rc.custom_button_with_icon(component_id=FORWARD_BUTTON_ID,
                                       icon_class_name=SheldonVisionConstants.FORWARD_BUTTON_ICON_CLASS_NAME,
                                       button_class_name=SheldonVisionConstants.BUTTON_CLASS_NAME, is_disabled=True,
                                       icon_style=SheldonVisionConstants.BUTTONS_FONT_STYLE_PLAYER,
                                       button_style=SheldonVisionConstants.BUTTONS_STYLE,
                                       access_key=SheldonVisionConstants.FORWARD_BUTTON,
                                       title=SheldonVisionConstants.FORWARD_BUTTON_SHORTCUT),
            rc.slider(input_range_id=FRAME_INPUT_ID, component_id=CYCLE_RANGE_SLIDER_ID,
                      min_slider_range=cycles_range[0], max_slider_range=cycles_range[1], label="Selected Frame:", is_range_slider=False,
                      input_disabled=True, slider_disabled=True),
            db_info_card_content,
            rc.custom_button_with_icon(component_id=SheldonVisionConstants.PAUSE_BUTTON_ID,
                                       icon_class_name=SheldonVisionConstants.PAUSE_BUTTON_ICON_CLASS_NAME,
                                       button_class_name=SheldonVisionConstants.BUTTON_CLASS_NAME,
                                       is_disabled=self.are_player_buttons_disabled,
                                       icon_style=SheldonVisionConstants.BUTTONS_FONT_STYLE_PLAYER,
                                       button_style=SheldonVisionConstants.BUTTONS_STYLE,
                                       access_key=SheldonVisionConstants.PAUSE_BUTTON,
                                       title=SheldonVisionConstants.PAUSE_BUTTON_SHORTCUT),
            rc.custom_button_with_icon_drop_down(component_id=SheldonVisionConstants.BROWSE_BUTTON_ID,
                                                 icon_class_name=SheldonVisionConstants.SEARCH_BUTTON_ICON_CLASS_NAME,
                                                 button_class_name=SheldonVisionConstants.BUTTON_CLASS_NAME,
                                                 icon_style=SheldonVisionConstants.BUTTONS_FONT_STYLE,
                                                 button_style=SheldonVisionConstants.BROWSE_BUTTONS_STYLE,
                                                 access_key=SheldonVisionConstants.VIDEO_BROWSE_BUTTON,
                                                 title=SheldonVisionConstants.VIDEO_BROWSE_BUTTON_SHORTCUT,
                                                 label="Video",
                                                 values=["Local File", "Blob"],
                                                 drop_down_style=SheldonVisionConstants.DROP_DOWN_BUTTONS_STYLE),
            rc.custom_button_with_icon_drop_down(component_id=SheldonVisionConstants.BROWSE_METADATA_BUTTON_ID,
                                                 icon_class_name=SheldonVisionConstants.SEARCH_BUTTON_ICON_CLASS_NAME,
                                                 button_class_name=SheldonVisionConstants.BUTTON_CLASS_NAME,
                                                 icon_style=SheldonVisionConstants.BUTTONS_FONT_STYLE,
                                                 button_style=SheldonVisionConstants.BROWSE_BUTTONS_STYLE,
                                                 access_key=SheldonVisionConstants.META_DATA_PRIMARY_BROWSE_BUTTON,
                                                 title=SheldonVisionConstants.META_DATA_PRIMARY_BROWSE_BUTTON_SHORTCUT,
                                                 label="MetaData Primary",
                                                 values=["Local File", "Blob"],
                                                 drop_down_style=SheldonVisionConstants.DROP_DOWN_BUTTONS_STYLE),
            rc.custom_button_with_icon_drop_down(component_id=SheldonVisionConstants.BROWSE_METADATA_SECONDARY_BUTTON_ID,
                                                 icon_class_name=SheldonVisionConstants.SEARCH_BUTTON_ICON_CLASS_NAME,
                                                 button_class_name=SheldonVisionConstants.BUTTON_CLASS_NAME,
                                                 icon_style=SheldonVisionConstants.BUTTONS_FONT_STYLE,
                                                 button_style=SheldonVisionConstants.BROWSE_BUTTONS_STYLE,
                                                 access_key=SheldonVisionConstants.META_DATA_SECONDARY_BROWSE_BUTTON,
                                                 title=SheldonVisionConstants.META_DATA_SECONDARY_BROWSE_BUTTON_SHORTCUT,
                                                 label="MetaData Secondary",
                                                 values=["Local File", "Blob"],
                                                 drop_down_style=SheldonVisionConstants.DROP_DOWN_BUTTONS_STYLE),
            rc.custom_button_with_icon_drop_down(component_id=SheldonVisionConstants.BROWSE_RECORDINGS_DEBUG_DATA_BUTTON_ID,
                                                 icon_class_name=SheldonVisionConstants.SEARCH_BUTTON_ICON_CLASS_NAME,
                                                 button_class_name=SheldonVisionConstants.BUTTON_CLASS_NAME,
                                                 icon_style=SheldonVisionConstants.BUTTONS_FONT_STYLE,
                                                 button_style=SheldonVisionConstants.BROWSE_BUTTONS_STYLE,
                                                 access_key=SheldonVisionConstants.DEBUG_RECORDINGS_BROWSE_BUTTON,
                                                 title=SheldonVisionConstants.DEBUG_RECORDINGS_BROWSE_BUTTON_SHORTCUT,
                                                 label="Jump File",
                                                 values=["Local File", "Blob"],
                                                 drop_down_style=SheldonVisionConstants.DROP_DOWN_BUTTONS_STYLE),
            rc.custom_button_with_icon(component_id=SheldonVisionConstants.FAST_BACK_BUTTON_ID,
                                       icon_class_name=SheldonVisionConstants.FAST_FORWARD_BUTTON_ICON_CLASS_NAME,
                                       button_class_name=SheldonVisionConstants.BUTTON_CLASS_NAME, is_disabled=True,
                                       icon_style=SheldonVisionConstants.BUTTONS_FONT_STYLE_PLAYER,
                                       button_style=SheldonVisionConstants.BUTTONS_STYLE,
                                       access_key=SheldonVisionConstants.FAST_FORWARD_BUTTON,
                                       title=SheldonVisionConstants.FAST_FORWARD_BUTTON_SHORTCUT),
            rc.slider(input_range_id=SheldonVisionConstants.FPS_INPUT_ID, component_id=SheldonVisionConstants.FPS_SLIDER_ID,
                      min_slider_range=SheldonVisionConstants.FPS_RANGE[0], max_slider_range=SheldonVisionConstants.FPS_RANGE[1],
                      label="FPS:", is_range_slider=False, placeholder=SheldonVisionConstants.FPS_RANGE[0]),
            rc.custom_button_with_icon(component_id=SheldonVisionConstants.CLOSE_NETWORK_ID,
                                       icon_class_name=SheldonVisionConstants.CLOSE_APPLICATION_ICON_CLASS_NAME,
                                       button_class_name=SheldonVisionConstants.BUTTON_CLASS_NAME,
                                       icon_style=SheldonVisionConstants.BUTTONS_FONT_STYLE,
                                       button_style=SheldonVisionConstants.CLOSE_NETWORK_BUTTON_STYLE,
                                       access_key=SheldonVisionConstants.CLOSE_NETWORK_BUTTON,
                                       title=SheldonVisionConstants.CLOSE_NETWORK_SHORTCUT,
                                       label="Close"),
            rc.custom_button_with_icon(component_id=SheldonVisionConstants.SEND_MAIL_BUTTON_ID,
                                       icon_class_name=SheldonVisionConstants.SEND_MAIL_ICON_CLASS_NAME,
                                       button_class_name=SheldonVisionConstants.BUTTON_CLASS_NAME,
                                       icon_style=SheldonVisionConstants.BUTTONS_FONT_STYLE,
                                       button_style=SheldonVisionConstants.BROWSE_BUTTONS_STYLE,
                                       access_key=SheldonVisionConstants.SEND_MAIL_BUTTON,
                                       title=SheldonVisionConstants.SEND_MAIL_SHORTCUT,
                                       label="Send Mail"),
            rc.slider(input_range_id=SheldonVisionConstants.DECIMATION_SPEED_INPUT_ID,
                      component_id=SheldonVisionConstants.DECIMATION_SPEED_SLIDER_ID,
                      range=SheldonVisionConstants.DECIMATION_SPEED_VALUES, value=1, label="Speed:", is_range_slider=False,
                      is_predefined_slider=True, placeholder=1, max_slider_range=0, min_slider_range=0, hidden=True, step=1, included=False,
                      is_linear=False, show_tooltip=False),
            rc.custom_button_with_icon(component_id=SheldonVisionConstants.DECIMATION_BUTTON_ID,
                                       icon_class_name=SheldonVisionConstants.DECIMATION_ICON_CLASS_NAME,
                                       button_class_name=SheldonVisionConstants.BUTTON_CLASS_NAME,
                                       icon_style=SheldonVisionConstants.BUTTONS_FONT_STYLE,
                                       button_style=SheldonVisionConstants.DECIMATION_BUTTONS_STYLE,
                                       access_key=SheldonVisionConstants.DECIMATION_BUTTON,
                                       title=SheldonVisionConstants.DECIMATION_BUTTON_SHORTCUT,
                                       label="Decimation"),
        ]

    def __create_frame_view(self, component_id, drop_down_component_id, feed_source, meta_data_type: MetaDataType = MetaDataType.PRIMARY):
        """
        Create the frame view component for the page
        @param component_id:
        @param drop_down_component_id:
        @return:
        """
        plot_layer = self.primary_plot_layer if meta_data_type == MetaDataType.PRIMARY else self.secondary_plot_layer
        return rc.Card(
            rc.CardContent(
                [
                    dcc.Dropdown(id=drop_down_component_id,
                                 options=list(plot_layer.keys()),
                                 value=list(plot_layer.keys()),
                                 multi=True
                                 ),

                    self.__create_online_graph(f"{component_id}{SheldonVisionConstants.ONLINE_ID}", feed_source),
                    self.__create_offline_graph_div(f"{component_id}{SheldonVisionConstants.OFFLINE_ID}"),
                    html.Br(),
                ]
                , style={'margin': '0px', 'height': '600px'}), style={'margin': '2px'}
        )

    def __validate_basic_data_to_load_ui(self):
        if self.frames_range is None:
            raise FrameRangeNotValid()

    def __create_callbacks(self):
        """
        Create the callbacks for the page
        @return:
        """
        app.clientside_callback(
            """
            function(main_send, is_disabled) {            
                if (is_disabled == false){
                    document.body.style.zoom=0.5;   
                    setTimeout(function() {
                       document.body.style.zoom=1;
                        }, 1000);                                  
                    }                    
                else {
                    document.body.style.zoom=1;                
                    }
                return false;
            }
            """,
            Output(SheldonVisionConstants.SEND_MAIL_BUTTON_ID, 'disabled'),
            Input(SheldonVisionConstants.SEND_MAIL_BUTTON_ID, 'n_clicks'),
            State(SheldonVisionConstants.SEND_MAIL_BUTTON_ID, 'disabled'),
            prevent_initial_call=True
        )

        app.callback(output=[Output(CYCLE_RANGE_SLIDER_ID, 'value'),
                             Output(FRAME_INPUT_ID, 'value'),
                             Output(CYCLE_RANGE_SLIDER_ID, 'min'),
                             Output(CYCLE_RANGE_SLIDER_ID, 'max'),
                             Output(SheldonVisionConstants.VIDEO_LOADED_FILES_LIST_ID, "children"),
                             Output(SheldonVisionConstants.SETTINGS_LOADED_LABEL_ID, "children"),
                             Output(CYCLE_RANGE_SLIDER_ID, 'marks'),
                             Output(SheldonVisionConstants.FPS_SLIDER_ID, 'value'),
                             Output(SheldonVisionConstants.FPS_INPUT_ID, 'value'),
                             Output(SheldonVisionConstants.PRIMARY_GENERAL_DIV, 'children'),
                             Output(SheldonVisionConstants.SECONDARY_GENERAL_DIV, 'children'),
                             Output(SheldonVisionConstants.PRIMARY_GRAPH_OFFLINE_FIGURE_ID, 'figure'),
                             Output(SheldonVisionConstants.SECONDARY_GRAPH_OFFLINE_FIGURE_ID, 'figure'),
                             Output(SheldonVisionConstants.DECIMATION_BUTTON_ID, 'style'),
                             Output(SheldonVisionConstants.FULL_FPS_SLIDER_ID, 'style'),
                             Output(SheldonVisionConstants.FULL_SPEED_SLIDER_ID, 'style'),
                             Output(SheldonVisionConstants.DECIMATION_SPEED_SLIDER_ID, 'value'),
                             Output(SheldonVisionConstants.DECIMATION_SPEED_INPUT_ID, 'value'),
                             Output(SheldonVisionConstants.INPUT_VIDEO_MODAL, 'is_open'),
                             Output(SheldonVisionConstants.PRIMARY_GRAPH_ONLINE_DIV_ID, 'hidden'),
                             Output(SheldonVisionConstants.PRIMARY_GRAPH_OFFLINE_DIV_ID, 'hidden'),
                             Output(SheldonVisionConstants.SECONDARY_GRAPH_ONLINE_DIV_ID, 'hidden'),
                             Output(SheldonVisionConstants.SECONDARY_GRAPH_OFFLINE_DIV_ID, 'hidden'),
                             Output(FRAME_INPUT_ID, 'disabled'),
                             Output(CYCLE_RANGE_SLIDER_ID, 'disabled')
                             ],
                     inputs=[
                         Input(SheldonVisionConstants.FAST_BACK_BUTTON_ID, 'n_clicks'),
                         Input(SheldonVisionConstants.PAUSE_BUTTON_ID, 'n_clicks'),
                         Input(PRIMARY_GRAPH_DROPDOWN_ID, "value"),
                         Input(SECONDARY_GRAPH_DROPDOWN_ID, "value"),
                         Input(SheldonVisionConstants.BROWSE_BUTTON_ID, "n_clicks"),
                         Input(BACK_BUTTON_ID, 'n_clicks'),
                         Input(FORWARD_BUTTON_ID, 'n_clicks'),
                         Input(CYCLE_RANGE_SLIDER_ID, 'value'),
                         Input(SheldonVisionConstants.SLIDER_INTERVAL_ID, 'n_intervals'),
                         Input(FRAME_INPUT_ID, 'value'),
                         Input(SheldonVisionConstants.DEBUG_EDITABLE_TABLE, "active_cell"),
                         Input(SheldonVisionConstants.PRIMARY_GRAPH_OFFLINE_FIGURE_ID, 'clickData'),
                         Input(SheldonVisionConstants.SECONDARY_GRAPH_OFFLINE_FIGURE_ID, 'clickData'),
                         Input(SheldonVisionConstants.PRIMARY_GRAPH_OFFLINE_FIGURE_ID, 'relayoutData'),
                         Input(SheldonVisionConstants.SECONDARY_GRAPH_OFFLINE_FIGURE_ID, 'relayoutData'),
                         Input(SheldonVisionConstants.FPS_SLIDER_ID, 'value'),
                         Input(SheldonVisionConstants.FPS_INPUT_ID, 'value'),
                         Input(SheldonVisionConstants.LOADING_FROM_MAIL_LABEL_ID, 'hidden'),
                         Input(SheldonVisionConstants.METADATA_LOADED_FILES_LIST_ID, "children"),
                         Input(SheldonVisionConstants.METADATA_SECONDARY_LOADED_FILES_LIST_ID, "children"),
                         Input(SheldonVisionConstants.DECIMATION_BUTTON_ID, 'n_clicks'),
                         Input(SheldonVisionConstants.DECIMATION_SPEED_SLIDER_ID, 'value'),
                         Input(SheldonVisionConstants.DECIMATION_SPEED_INPUT_ID, 'value'),
                         Input(SheldonVisionConstants.LOCAL_FILE_NOT_FOUND_ID, 'submit_n_clicks'),
                         Input(SheldonVisionConstants.LOCAL_FILE_NOT_FOUND_ID, 'cancel_n_clicks'),
                         Input(SheldonVisionConstants.DROP_DOWN_VIDEO_LOCAL, 'n_clicks'),
                         Input(SheldonVisionConstants.DROP_DOWN_VIDEO_BLOB, 'n_clicks'),
                         Input(SheldonVisionConstants.INPUT_VIDEO_MODAL_OK, 'n_clicks'),
                         Input(SheldonVisionConstants.INPUT_VIDEO_MODAL_CANCEL, 'n_clicks'),
                     ],
                     state=[State(CYCLE_RANGE_SLIDER_ID, 'value'),
                            State(SheldonVisionConstants.DEBUG_EDITABLE_TABLE, 'derived_viewport_data'),
                            State(SheldonVisionConstants.PRIMARY_GENERAL_DIV, 'children'),
                            State(SheldonVisionConstants.SECONDARY_GENERAL_DIV, 'children'),
                            State(SheldonVisionConstants.FULL_FPS_SLIDER_ID, 'style'),
                            State(SheldonVisionConstants.FULL_SPEED_SLIDER_ID, 'style'),
                            State(SheldonVisionConstants.INPUT_VIDEO_MODAL_INPUT, 'value')
                            ])(
            self.__update_main_ui)
        app.callback(output=[Output(SheldonVisionConstants.PAUSE_BUTTON_ID, 'n_clicks'),
                             Output(PLAY_BUTTON_ID, 'n_clicks'),
                             Output(PLAY_BUTTON_ID, 'disabled'),
                             Output(SheldonVisionConstants.PAUSE_BUTTON_ID, 'disabled'),
                             Output(SheldonVisionConstants.SLIDER_INTERVAL_ID, 'disabled'),
                             Output(FORWARD_BUTTON_ID, 'disabled'),
                             Output(BACK_BUTTON_ID, 'disabled'),
                             Output(SheldonVisionConstants.FAST_BACK_BUTTON_ID, 'disabled')
                             ],
                     inputs=[Input(PLAY_BUTTON_ID, 'n_clicks'),
                             Input(SheldonVisionConstants.PAUSE_BUTTON_ID, 'n_clicks'),
                             Input(SheldonVisionConstants.VIDEO_LOADED_FILES_LIST_ID, "children"),
                             ],
                     state=[State(CYCLE_RANGE_SLIDER_ID, 'value')])(
            self.on_play_button)

        app.callback(output=[
            Output(SheldonVisionConstants.METADATA_LOADED_FILES_LIST_ID, "children"),
            Output(SheldonVisionConstants.METADATA_SECONDARY_LOADED_FILES_LIST_ID, "children"),
            Output(SheldonVisionConstants.LOCAL_FILE_NOT_FOUND_ID, "displayed"),
        ],
            inputs=[
                Input(SheldonVisionConstants.BROWSE_METADATA_BUTTON_ID, "n_clicks"),
                Input(SheldonVisionConstants.DEBUG_EDITABLE_TABLE, "active_cell"),
                Input(SheldonVisionConstants.LOADING_FROM_MAIL_LABEL_ID, 'hidden'),
                Input(SheldonVisionConstants.DROP_DOWN_PRIMARY_LOCAL, 'n_clicks'),
                Input(SheldonVisionConstants.INPUT_METADATA_MODAL_OK, 'n_clicks'),
                Input(SheldonVisionConstants.BROWSE_METADATA_SECONDARY_BUTTON_ID, "n_clicks"),
                Input(SheldonVisionConstants.DROP_DOWN_SECONDARY_LOCAL, 'n_clicks'),
                Input(SheldonVisionConstants.LOCAL_FILE_NOT_FOUND_ID, 'submit_n_clicks'),
                Input(SheldonVisionConstants.LOCAL_FILE_NOT_FOUND_ID, 'cancel_n_clicks')
            ],
            state=[State(SheldonVisionConstants.DEBUG_EDITABLE_TABLE, 'derived_viewport_data'),
                   State(SheldonVisionConstants.INPUT_METADATA_MODAL_INPUT, 'value'),
                   State(SheldonVisionConstants.INPUT_METADATA_MODAL_TYPE, 'title')])(
            self.__load_metadata_from_file)

        app.callback(output=[
            Output(SheldonVisionConstants.RECORDINGS_DEBUG_DATA_LABEL_ID, "hidden"),
            Output(SheldonVisionConstants.RECORDINGS_DEBUG_DATA_TABLE_DIV_ID, 'hidden'),
            Output(SheldonVisionConstants.DEBUG_EDITABLE_TABLE, 'data'),
            Output(SheldonVisionConstants.DEBUG_EDITABLE_TABLE, 'columns'),
            Output(SheldonVisionConstants.ERROR_MESSAGE, 'displayed'),
            Output(SheldonVisionConstants.ERROR_MESSAGE, 'message'),
            Output(SheldonVisionConstants.JUMP_FILE_ID, 'children')
        ],
            inputs=[
                Input(SheldonVisionConstants.BROWSE_RECORDINGS_DEBUG_DATA_BUTTON_ID, "n_clicks"),
                Input(SheldonVisionConstants.DEBUG_EDITABLE_TABLE, "active_cell"),
                Input(SheldonVisionConstants.DEBUG_ADD_ROW_BUTTON, 'n_clicks'),
                Input(SheldonVisionConstants.DEBUG_ADD_COLUMN_BUTTON, 'n_clicks'),
                Input(SheldonVisionConstants.DROP_DOWN_JUMP_LOCAL, 'n_clicks'),
                Input(SheldonVisionConstants.JUMP_LOADING_LABEL_ID, 'hidden'),
                Input(SheldonVisionConstants.INPUT_METADATA_MODAL_OK, 'n_clicks'),
            ], state=[State(SheldonVisionConstants.DEBUG_EDITABLE_TABLE, 'derived_viewport_data'),
                      State(SheldonVisionConstants.DEBUG_EDITABLE_TABLE, 'columns'),
                      State(SheldonVisionConstants.DEBUG_EDITABLE_TABLE, 'data'),
                      State(SheldonVisionConstants.DEBUG_COLUMN_NAME_INPUT, 'value'),
                      State(SheldonVisionConstants.INPUT_METADATA_MODAL_INPUT, 'value'),
                      State(SheldonVisionConstants.INPUT_METADATA_MODAL_TYPE, 'title')])(
            self.load_recordings_debug_data_from_file)

        app.callback(output=[
            Output(SheldonVisionConstants.RECORDINGS_DEBUG_EXPORT_BUTTON_ID, "children"),
        ],
            inputs=[
                Input(SheldonVisionConstants.RECORDINGS_DEBUG_EXPORT_BUTTON_ID, "n_clicks"),
            ], state=[State(SheldonVisionConstants.DEBUG_EDITABLE_TABLE, 'derived_virtual_data')])(
            self.export_recordings_debug_data_to_file)

        app.callback(output=[Output(SheldonVisionConstants.CLOSE_NETWORK_ID, "children"), ],
                     inputs=Input(SheldonVisionConstants.CLOSE_NETWORK_ID, "n_clicks"))(self.__on_close_network_click)

        app.callback(output=[
                        Output(SheldonVisionConstants.ERROR_MESSAGE_EMAIL, 'displayed'),
                        Output(SheldonVisionConstants.ERROR_MESSAGE_EMAIL, 'message')],
                     inputs=Input(SheldonVisionConstants.SEND_MAIL_BUTTON_ID, "n_clicks"),
                     state=[
                         State(SheldonVisionConstants.VIDEO_LOADED_FILES_LIST_ID, "children"),
                         State(SheldonVisionConstants.METADATA_LOADED_FILES_LIST_ID, "children"),
                         State(SheldonVisionConstants.METADATA_SECONDARY_LOADED_FILES_LIST_ID, "children"),
                         State(FRAME_INPUT_ID, "value")])(self.send_mail_with_outlook)

        app.callback(output=Output(SheldonVisionConstants.LOADING_FROM_MAIL_LABEL_ID, 'hidden'),
                     inputs=Input(SheldonVisionConstants.AUTORUN_FROM_MAIL_INTERVAL_ID, 'n_intervals'))(self.__on_autorun_interval)

        app.callback(output=[Output(SheldonVisionConstants.INPUT_METADATA_MODAL, 'is_open'),
                             Output(SheldonVisionConstants.INPUT_METADATA_MODAL_TYPE, 'title'),
                             Output(SheldonVisionConstants.INPUT_METADATA_MODAL_INPUT, 'value'),
                             Output(SheldonVisionConstants.INPUT_METADATA_MODAL_HEADER, 'children'),
                             Output(SheldonVisionConstants.INPUT_METADATA_MODAL_LABEL, 'children')],
                     inputs=[Input(SheldonVisionConstants.DROP_DOWN_PRIMARY_BLOB, 'n_clicks'),
                             Input(SheldonVisionConstants.DROP_DOWN_SECONDARY_BLOB, 'n_clicks'),
                             Input(SheldonVisionConstants.DROP_DOWN_JUMP_BLOB, 'n_clicks'),
                             Input(SheldonVisionConstants.INPUT_METADATA_MODAL_OK, 'n_clicks'),
                             Input(SheldonVisionConstants.INPUT_METADATA_MODAL_CANCEL, 'n_clicks')])(self.__handle_metadata_drop_down)

        app.callback(output=Output("notifications-container", "children"),
                     inputs=Input(SheldonVisionConstants.ALERTS_INTERVAL_ID, 'n_intervals'),
                     prevent_initial_call=True)(self.__on_alerts_interval)

        app.callback(inputs=Input(CYCLE_RANGE_SLIDER_ID, 'drag_value'),
                     output=Output(CYCLE_RANGE_SLIDER_ID, 'hidden'))(self.__on_frame_drag_event)
                    
        app.callback(output=Output(SheldonVisionConstants.JUMP_LOADING_LABEL_ID, 'hidden'),
                     inputs=Input(SheldonVisionConstants.JUMP_LOAD_INTERVAL_ID, 'n_intervals'),
                     state=State(SheldonVisionConstants.JUMP_LOADING_LABEL_ID, 'hidden'))(self.__on_jump_load_interval)
                     
    def __on_jump_load_interval(self, jump_load_interval, label_status):
        if self.waiting_jump_loading == AutoRunStatus.WAITING or self.waiting_jump_loading == AutoRunStatus.LOADING:
            return False
        elif not label_status:
            return True
        else:
            return dash.no_update

    def __on_frame_drag_event(self, drag_value):
        current_frame = self.get_current_frame_number_method_callback()
        self.is_on_dragging = not (current_frame - 5 <= drag_value <= current_frame + 5) if current_frame else False
        return False

    def __on_alerts_interval(self, alert_interval):
        notification, notification_id = self.notifications.get_notification()
        if not notification:
            return dash.no_update

        return rc.create_notification(component_id_number=notification_id, title=notification.title, message=notification.body,
                                      time_to_display=notification.notification_type['autoClose'],
                                      base_color=notification.notification_type['color'], style=notification.notification_type['style'],
                                      icon=notification.notification_type['icon'])

    def __handle_metadata_drop_down(self, primary_blob, secondary_blob, jump_blob, input_ok, input_cancel):
        triggered_callback = dash.callback_context.triggered[0][PROP_ID]
        if SheldonVisionConstants.DROP_DOWN_PRIMARY_BLOB in triggered_callback:
            return sheldon_helpers.prepare_browse_blob_output_callback(modal_is_open=True,
                                                                       modal_type=MetaDataType.PRIMARY.name,
                                                                       modal_input='',
                                                                       modal_title=dbc.ModalHeader('Metadata from Blob'),
                                                                       modal_label="Metadata Path:")

        if SheldonVisionConstants.DROP_DOWN_SECONDARY_BLOB in triggered_callback:
            return sheldon_helpers.prepare_browse_blob_output_callback(modal_is_open=True,
                                                                       modal_type=MetaDataType.SECONDARY.name,
                                                                       modal_input='',
                                                                       modal_title=dbc.ModalHeader('Metadata from Blob'),
                                                                       modal_label="Metadata Path:")

        if SheldonVisionConstants.DROP_DOWN_JUMP_BLOB in triggered_callback:
            return sheldon_helpers.prepare_browse_blob_output_callback(modal_is_open=True,
                                                                       modal_type='Jump',
                                                                       modal_input='',
                                                                       modal_title=dbc.ModalHeader('Jump from Blob'),
                                                                       modal_label="Jump Path:")

        return sheldon_helpers.prepare_browse_blob_output_callback(modal_is_open=False,
                                                                   modal_type='')

    def __on_autorun_interval(self, autorun_interval):
        statuses = [self.waiting_autorun_main_ui, self.waiting_autorun_metadata_primary, self.waiting_autorun_metadata_secondary]
        if [x for x in statuses if x == AutoRunStatus.WAITING or x == AutoRunStatus.LOADING]:
            if self.loading_hidden:
                self.loading_hidden = False
            return False
        else:
            if not self.loading_hidden:
                self.loading_hidden = True
                return True
        return dash.no_update

    def __validate_path(self, item: html.Div):
        item_path = item['props']['children'] if item else ''
        return item_path if \
            item_path and item_path not in [SheldonVisionConstants.NO_FILES_SELECTED, SheldonVisionConstants.NO_FILES_SELECTED_JSON] else ''

    def __extract_children(self, video, metadata_primary, metadata_secondary) -> Tuple[str, str, str, str]:
        video_path = self.__validate_path(video)
        metadata_primary_path = self.__validate_path(metadata_primary)
        metadata_secondary_path = self.__validate_path(metadata_secondary)
        errors = []
        if not video_path:
            errors.append('Video is missing')
        if not metadata_primary_path and not metadata_secondary_path:
            errors.append('No metadata files')
        error_message = f'Errors detected: {", ".join(errors)}' if errors else ''
        return video_path, metadata_primary_path, metadata_secondary_path, error_message

    def send_mail_with_outlook(self, send_mail_n_click: int, video, metadata_primary, metadata_secondary, frame_number) -> Tuple[bool, str]:
        triggered_callback = dash.callback_context.triggered[0][PROP_ID]
        if triggered_callback == EMPTY_CALLBACK_ID:
            return False, ''
        time.sleep(0.5)  # waits for zoom to be completed
        MailHandler.get_screenshot()
        video_path, primary_metadata, secondary_metadata, fields_error = self.__extract_children(video, metadata_primary, metadata_secondary)
        if fields_error:
            self.notifications.notify_error(title='Send Mail', body=f'Send mail failed - {fields_error}')
            return True, fields_error
        mail_error = MailHandler.send_with_outlook(self.upload_file_to_blob_callback, video_path, primary_metadata, secondary_metadata, frame_number)
        if mail_error:
            self.notifications.notify_error(title='Send Mail', body=f'Send mail failed - {mail_error}')
            return True, mail_error
        return False, ''

    def on_play_button(self, play_button_n_clicks, pause_button_n_clicks, video_file_path, frame_id):
        pause_n_click = dash.no_update
        triggered_callback = dash.callback_context.triggered[0][PROP_ID]
        if EMPTY_CALLBACK_ID == triggered_callback and self.previous_video_file_name:

            return sheldon_helpers.prepare_player_output_callbacks(pause_button_n_clicks=pause_n_click,
                                                                   play_button_n_clicks=play_button_n_clicks,
                                                                   play_button_is_disabled=self.is_playing,
                                                                   pause_button_is_disabled=not self.is_playing,
                                                                   slider_interval_is_disabled=not self.is_playing,
                                                                   forward_button_is_disabled=self.is_playing,
                                                                   back_button_is_disabled=self.is_playing,
                                                                   fast_forward_button_is_disabled=self.is_playing)

        if EMPTY_CALLBACK_ID == triggered_callback and not self.previous_video_file_name:
            return sheldon_helpers.prepare_player_output_callbacks(pause_button_n_clicks=pause_n_click,
                                                                   play_button_n_clicks=play_button_n_clicks,
                                                                   play_button_is_disabled=True,
                                                                   pause_button_is_disabled=True,
                                                                   slider_interval_is_disabled=True,
                                                                   forward_button_is_disabled=True,
                                                                   back_button_is_disabled=True,
                                                                   fast_forward_button_is_disabled=True)

        if play_button_n_clicks is None:
            if video_file_path and \
                    SheldonVisionConstants.NO_FILES_SELECTED not in video_file_path.get('props').get('children'):
                return sheldon_helpers.prepare_player_output_callbacks(play_button_is_disabled=False,
                                                                       pause_button_is_disabled=True,
                                                                       slider_interval_is_disabled=True,
                                                                       forward_button_is_disabled=False,
                                                                       back_button_is_disabled=False,
                                                                       fast_forward_button_is_disabled=False)
            else:
                return sheldon_helpers.prepare_player_output_callbacks()

        if f"{PLAY_BUTTON_ID}.n_clicks" in triggered_callback and not self.is_playing:
            self.is_playing = True
            if self.is_decimated:
                self.__play_decimation_thread = threading.Thread(target=self.__play_decimation, args=(frame_id,)).start()
            else:
                self.send_play_message_method_callback()
        elif f"{SheldonVisionConstants.PAUSE_BUTTON_ID}.n_clicks" in triggered_callback:
            self.send_pause_message_method_callback()
            self.is_playing = False
            pause_n_click = None
            self.__set_auto_range(True)
        return sheldon_helpers.prepare_player_output_callbacks(pause_button_n_clicks=pause_n_click,
                                                               play_button_n_clicks=play_button_n_clicks,
                                                               play_button_is_disabled=self.is_playing,
                                                               pause_button_is_disabled=not self.is_playing,
                                                               slider_interval_is_disabled=not self.is_playing,
                                                               forward_button_is_disabled=self.is_playing,
                                                               back_button_is_disabled=self.is_playing,
                                                               fast_forward_button_is_disabled=self.is_playing)

    def __play_decimation(self, current_frame):
        def calc_delay(prev_frame, next_frame):
            return (1 / self.speed) * (next_frame - prev_frame) / SheldonVisionConstants.DEFAULT_FPS

        prev_frame_id = self.meta_data_handler.get_decimation_value(current_frame, is_next_frame=False)
        frame_id = self.meta_data_handler.get_decimation_value(current_frame, is_next_frame=True)
        self.clear_frames_queue_method_callback(True)
        while self.is_playing:
            self.send_set_frame_message_method_callback(frame_id - 1)
            self.send_get_current_frame_method_callback()
            if frame_id == prev_frame_id:
                self.is_playing = False
            prev_frame_id = frame_id
            frame_id = self.meta_data_handler.get_decimation_value(frame_id, is_next_frame=True)
            time.sleep(calc_delay(prev_frame_id, frame_id))
        self.current_frame_number = frame_id

    @staticmethod
    def __create_meta_data_view(component_id):
        return rc.Card(
            rc.CardContent(
                [
                    rc.create_updating_data_table_by_callback(component_id=component_id, data_frame=pd.DataFrame(),
                                                              sorted_column=SheldonVisionConstants.KEYS, is_export=False, is_hidden=True)
                ]
            ), style={'margin': '2px'}
        )

    @staticmethod
    def __create_general_meta_data_view(component_id):
        return rc.Card(
            rc.CardContent(
                [
                    rc.create_general_div_by_callback(component_id=component_id, data=html.Div())
                ]
            ), style={'margin': '2px'}
        )

    def __select_file_from_dialog_box(self, file_types, is_save_as_dialog=False):
        file_name = []
        # open-file dialog
        if self.__root_tk is None:
            self.__root_tk = tk.Tk()
            self.__root_tk.withdraw()
            self.__root_tk.call('wm', 'attributes', '.', '-topmost', True)
            file_name = tk.filedialog.askopenfilename(
                title='Select a file...',
                filetypes=file_types,
            ) if not is_save_as_dialog else tk.filedialog.asksaveasfilename(
                title='Select a file...',
                filetypes=file_types,
            )
            self.__root_tk.destroy()
            self.__root_tk = None

            if is_save_as_dialog:
                file_name = sheldon_helpers.add_file_suffix(file_name, SheldonVisionConstants.JSON_SUFFIX)

        return file_name

    @staticmethod
    def __create_offline_graph_div(component_id):
        return html.Div(id=f"{component_id}{SheldonVisionConstants.GRAPH_DIV_ID}", hidden=True,
                        children=dcc.Graph(
                            id=component_id,
                            config={'scrollZoom': True}, figure={
                                'layout': go.Layout(
                                    xaxis={
                                        'showgrid': False,
                                        'visible': False,
                                    },
                                    yaxis={
                                        'showgrid': False,
                                        'visible': False,
                                    }
                                )},
                        )
                        )

    @staticmethod
    def __create_online_graph(component_id, src):
        return html.Div(id=f"{component_id}{SheldonVisionConstants.GRAPH_DIV_ID}", hidden=False,
                        children=html.Img(id=component_id, src=src, width=SheldonVisionConstants.PLOT_WIDTH,
                                          height=SheldonVisionConstants.PLOT_HEIGHT))

    def create_online_graph(self, frame, current_frame_number: int, meta_data_type: MetaDataType = MetaDataType.PRIMARY):
        try:
            frame_with_layers = Image.open(io.BytesIO(frame))
            plot_player = self.primary_plot_layer if meta_data_type == MetaDataType.PRIMARY else self.secondary_plot_layer
            for layer in plot_player.keys():
                if plot_player[layer].active():
                    plot_player[layer].set_frame_data(frame_with_layers, current_frame_number)
                    frame_with_layers = plot_player[layer].add_layers_to_frame(True, meta_data_type)

            buffer = io.BytesIO()
            frame_with_layers.save(buffer, format='JPEG')
            return buffer.getvalue()
        except PIL.UnidentifiedImageError:
            self.log_method(logging.WARN, "Failed to create online graph due to invalid frame data")
            self.log_method(logging.WARN, f"Frame number: {current_frame_number} | frame: {frame} | meta_data_type: {meta_data_type.value}")
            return bytes()

    def create_meta_data_general(self, meta_data_type: MetaDataType = MetaDataType.PRIMARY):
        layers_metadata = []
        if self.previous_video_file_name:
            plot_player = self.primary_plot_layer if meta_data_type == MetaDataType.PRIMARY else self.secondary_plot_layer
            for layer in plot_player.keys():
                if plot_player[layer].active():
                    layer_name = plot_player[layer].layer_name()
                    plot_title = html.Div(id=f"{meta_data_type.value}-{layer_name}-title",
                                          children=layer_name,
                                          style={"margin-top": "15px", "font-weight": "bold", "font-size": "120%"})
                    layer_data_with_name = html.Div(id=f"{meta_data_type.value}-{layer_name}",
                                                    children=[plot_title, plot_player[layer].get_meta_data(meta_data_type)])
                    layers_metadata.append(layer_data_with_name)

        return layers_metadata

    def create_offline_graph(self, current_frame_number, meta_data_type: MetaDataType = MetaDataType.PRIMARY,
                             click_event_rect: GUIRect = None, closest_layer_name: str = None):
        if not self.previous_video_file_name:
            return dash.no_update
        frame_to_set = current_frame_number - 1 if current_frame_number is not None and current_frame_number > 0 else 0
        if frame_to_set + 1 != self.get_current_frame_number_method_callback():
            self.__set_frame_number(frame_to_set)
        frame_data = self.get_current_frame_method_callback()
        frame_number = self.get_current_frame_number_method_callback()
        if frame_data:
            logging.info(f"going to create offline fig current_frame_number on queue:{frame_number}"
                         f", frame data length:{len(frame_data)}\n")
            image = Image.open(io.BytesIO(frame_data))
            if self.fig[meta_data_type] is None:
                self.fig[meta_data_type] = px.imshow(image, width=SheldonVisionConstants.PLOT_WIDTH, height=SheldonVisionConstants.PLOT_HEIGHT)
                self.fig[meta_data_type].update_xaxes(showticklabels=False).update_yaxes(showticklabels=False)
                self.fig[meta_data_type].update_layout(width=SheldonVisionConstants.PLOT_WIDTH, height=SheldonVisionConstants.PLOT_HEIGHT,
                                                       margin=dict(l=0, r=0, b=0, t=0))
            else:
                data = io.BytesIO()
                image.save(data, "JPEG")
                data64 = base64.b64encode(data.getvalue())
                self.fig[meta_data_type].data[0]['source'] = u'data:image/png;base64,' + data64.decode('utf-8')
                self.fig[meta_data_type].update_layout(width=SheldonVisionConstants.PLOT_WIDTH, height=SheldonVisionConstants.PLOT_HEIGHT,
                                                       margin=dict(l=0, r=0, b=10, t=0))

            self.fig[meta_data_type].layout['shapes'] = []
            self.fig[meta_data_type].layout['annotations'] = []

            plot_layer = self.primary_plot_layer if meta_data_type == MetaDataType.PRIMARY else self.secondary_plot_layer
            for layer in plot_layer.keys():
                if plot_layer[layer].active():
                    plot_layer[layer].set_frame_data(self.fig[meta_data_type], current_frame_number)
                    if plot_layer[layer].layer_name() == closest_layer_name and click_event_rect:
                        self.fig[meta_data_type] = plot_layer[layer].handle_selected_box_by_click_event(click_event_rect, meta_data_type)
                    else:
                        self.fig[meta_data_type] = plot_layer[layer].add_layers_to_frame(False, meta_data_type)

            return go.Figure(self.fig[meta_data_type])

    def __update_graph_dropdown_values(self, primary_graph_dropdown_value, secondary_graph_dropdown_value):
        for key in self.primary_plot_layer.keys():
            if key not in primary_graph_dropdown_value:
                self.primary_plot_layer[key].set_layer_state(False)
            else:
                self.primary_plot_layer[key].set_layer_state(True)

        for key in self.secondary_plot_layer.keys():
            if key not in secondary_graph_dropdown_value:
                self.secondary_plot_layer[key].set_layer_state(False)
            else:
                self.secondary_plot_layer[key].set_layer_state(True)

    def __load_metadata_from_file(self, browse_primary_button_n_clicks, debug_active_cell, autorun_hidden,
                                  local_menu_primary_n_clicks, div_hidden, browse_secondary_button_n_clicks,
                                  local_menu_secondary_n_clicks, local_file_not_found_submit_n_clicks, local_file_not_found_cancel_n_clicks,
                                  debug_data_table, input_modal_value, input_modal_type):
        triggered_callback = dash.callback_context.triggered[0][PROP_ID]
        metadata_values_by_type_dict = {MetaDataType.PRIMARY: dash.no_update, MetaDataType.SECONDARY: dash.no_update}
        no_file_loaded = html.Div(SheldonVisionConstants.NO_FILES_SELECTED_JSON,
                                  style=SheldonVisionConstants.HIGHLIGHT_TEXT_STYLE)

        if triggered_callback == EMPTY_CALLBACK_ID and self.meta_data_handler.is_metadata_file_loaded:
            caller_name = ctx.outputs_list[0][ID]
            relevant_metadata = MetaDataType.PRIMARY if caller_name == SheldonVisionConstants.METADATA_LOADED_FILES_LIST_ID else \
                MetaDataType.SECONDARY
            metadata_values_by_type_dict[relevant_metadata] = self.meta_data_handler.get_metadata_filename(relevant_metadata.value)
            return self.__prepare_load_metadata_from_file_output_callbacks(
                metadata_values_by_type_dict[MetaDataType.PRIMARY],
                metadata_values_by_type_dict[MetaDataType.SECONDARY],
                False)
        elif triggered_callback == EMPTY_CALLBACK_ID:
            metadata_values_by_type_dict[MetaDataType.PRIMARY] = no_file_loaded
            metadata_values_by_type_dict[MetaDataType.SECONDARY] = no_file_loaded
            return self.__prepare_load_metadata_from_file_output_callbacks(
                metadata_values_by_type_dict[MetaDataType.PRIMARY],
                metadata_values_by_type_dict[MetaDataType.SECONDARY],
                False)

        if SheldonVisionConstants.LOADING_FROM_MAIL_LABEL_ID in triggered_callback:
            if self.waiting_autorun_metadata_primary == AutoRunStatus.WAITING or self.waiting_autorun_metadata_secondary == AutoRunStatus.WAITING:
                caller_name = ctx.outputs_list[0][ID]
                if caller_name == SheldonVisionConstants.METADATA_LOADED_FILES_LIST_ID:
                    self.waiting_autorun_metadata_primary = AutoRunStatus.UNAVAILABLE
                else:
                    self.waiting_autorun_metadata_secondary = AutoRunStatus.UNAVAILABLE
                if caller_name == SheldonVisionConstants.METADATA_LOADED_FILES_LIST_ID:
                    metadata_values_by_type_dict[MetaDataType.PRIMARY] = self.autorun_from_mail[
                        'primary_metadata_path_blob']
                else:
                    metadata_values_by_type_dict[MetaDataType.SECONDARY] = self.autorun_from_mail[
                        'secondary_metadata_path_blob']
                return self.__prepare_load_metadata_from_file_output_callbacks(
                    metadata_values_by_type_dict[MetaDataType.PRIMARY],
                    metadata_values_by_type_dict[MetaDataType.SECONDARY],
                    False)
            else:
                return self.__prepare_load_metadata_from_file_output_callbacks()

        if SheldonVisionConstants.DROP_DOWN_PRIMARY_LOCAL in triggered_callback or \
                SheldonVisionConstants.DROP_DOWN_SECONDARY_LOCAL in triggered_callback:
            metadata_type = MetaDataType.SECONDARY if \
                SheldonVisionConstants.DROP_DOWN_SECONDARY_LOCAL in triggered_callback else MetaDataType.PRIMARY
            file_name = self.__select_file_from_dialog_box(SheldonVisionConstants.JSON_FILES_TYPE)

            if len(file_name) == 0 and self.meta_data_handler.get_metadata_filename(metadata_type.value):
                return self.__prepare_load_metadata_from_file_output_callbacks()
            elif len(file_name) == 0 and self.meta_data_handler.get_metadata_filename(metadata_type.value) is None:
                if metadata_type == MetaDataType.PRIMARY:
                    metadata_values_by_type_dict[MetaDataType.PRIMARY] = no_file_loaded
                else:
                    metadata_values_by_type_dict[MetaDataType.SECONDARY] = no_file_loaded
                return [metadata_values_by_type_dict[MetaDataType.PRIMARY],
                        metadata_values_by_type_dict[MetaDataType.SECONDARY],
                        False]
            else:
                self.meta_data_handler.load_metadata_from_file(file_name, metadata_type)
                metadata_values_by_type_dict[metadata_type] = file_name
                return self.__prepare_load_metadata_from_file_output_callbacks(
                    metadata_values_by_type_dict[MetaDataType.PRIMARY],
                    metadata_values_by_type_dict[MetaDataType.SECONDARY],
                    False)

        if SheldonVisionConstants.INPUT_METADATA_MODAL_OK in triggered_callback and input_modal_value and \
                (input_modal_type == MetaDataType.PRIMARY.name or input_modal_type == MetaDataType.SECONDARY.name):
            relevant_metadata = MetaDataType.PRIMARY if input_modal_type == MetaDataType.PRIMARY.name else \
                MetaDataType.SECONDARY
            caller_name = ctx.outputs_list[0][ID]
            is_primary = (
                        relevant_metadata == MetaDataType.PRIMARY and caller_name == SheldonVisionConstants.METADATA_LOADED_FILES_LIST_ID)
            is_secondary = (relevant_metadata == MetaDataType.SECONDARY and
                            caller_name == SheldonVisionConstants.METADATA_SECONDARY_LOADED_FILES_LIST_ID)
            if is_primary or is_secondary:
                metadata_values_by_type_dict[relevant_metadata] = self.meta_data_handler.load_metadata_file(
                    input_modal_value, relevant_metadata)
                if metadata_values_by_type_dict[relevant_metadata]:
                    return self.__prepare_load_metadata_from_file_output_callbacks(
                        metadata_values_by_type_dict[MetaDataType.PRIMARY],
                        metadata_values_by_type_dict[MetaDataType.SECONDARY],
                        False)
            return self.__prepare_load_metadata_from_file_output_callbacks()
        elif SheldonVisionConstants.INPUT_METADATA_MODAL_OK in triggered_callback:
            return self.__prepare_load_metadata_from_file_output_callbacks()

        if (browse_primary_button_n_clicks is None or browse_secondary_button_n_clicks is None) and debug_active_cell is None:
            component_id = ctx.args_grouping[0][ID]
            metadata_type = MetaDataType.PRIMARY if component_id == SheldonVisionConstants.BROWSE_METADATA_BUTTON_ID else \
                MetaDataType.SECONDARY
            metadata_values_by_type_dict[metadata_type] = self.__handle_metadata_loading_from_config(metadata_type)
            return [metadata_values_by_type_dict[MetaDataType.PRIMARY],
                    metadata_values_by_type_dict[MetaDataType.SECONDARY],
                    False]

        if SheldonVisionConstants.BROWSE_METADATA_BUTTON_ID in triggered_callback:
            metadata_type = MetaDataType.SECONDARY if \
                SheldonVisionConstants.BROWSE_METADATA_SECONDARY_BUTTON_ID in triggered_callback else MetaDataType.PRIMARY
            file_name = self.__select_file_from_dialog_box(SheldonVisionConstants.JSON_FILES_TYPE)

            if len(file_name) == 0 and self.meta_data_handler.get_metadata_filename(metadata_type.value):
                return self.__prepare_load_metadata_from_file_output_callbacks()
            elif len(file_name) == 0 and self.meta_data_handler.get_metadata_filename(metadata_type.value) is None:
                if metadata_type == MetaDataType.PRIMARY:
                    metadata_values_by_type_dict[MetaDataType.PRIMARY] = no_file_loaded
                else:
                    metadata_values_by_type_dict[MetaDataType.SECONDARY] = no_file_loaded
                return [metadata_values_by_type_dict[MetaDataType.PRIMARY],
                        metadata_values_by_type_dict[MetaDataType.SECONDARY],
                        False]
            else:
                self.meta_data_handler.load_metadata_from_file(file_name, metadata_type)
                metadata_values_by_type_dict[metadata_type] = file_name
                return self.__prepare_load_metadata_from_file_output_callbacks(
                    metadata_values_by_type_dict[MetaDataType.PRIMARY],
                    metadata_values_by_type_dict[MetaDataType.SECONDARY],
                    False)

        if SheldonVisionConstants.DEBUG_EDITABLE_TABLE in triggered_callback:
            row_selected = debug_active_cell[ROW]
            video_path = debug_data_table[row_selected][VIDEO_LOCATION]
            if self.previous_video_file_name and self.previous_video_file_name == video_path:
                return self.__prepare_load_metadata_from_file_output_callbacks(
                    metadata_values_by_type_dict[MetaDataType.PRIMARY],
                    metadata_values_by_type_dict[MetaDataType.SECONDARY],
                    False)
            primary_metadata = self.meta_data_handler.get_debug_metadata_file_path(video_path, MetaDataType.PRIMARY,
                                                                                   row_selected)
            secondary_metadata = self.meta_data_handler.get_debug_metadata_file_path(video_path, MetaDataType.SECONDARY,
                                                                                     row_selected)
            if not primary_metadata or not secondary_metadata:
                return self.__prepare_load_metadata_from_file_output_callbacks(primary_metadata, secondary_metadata, True)
            self.is_ready_to_load_metadata = True
            return self.__prepare_load_metadata_from_file_output_callbacks(primary_metadata, secondary_metadata, False)

        if f"{SheldonVisionConstants.LOCAL_FILE_NOT_FOUND_ID}.{SheldonVisionConstants.SUBMIT_N_CLICKS}" in triggered_callback:
            row_selected = debug_active_cell[ROW]
            video_path = debug_data_table[row_selected][VIDEO_LOCATION]
            if self.previous_video_file_name and self.previous_video_file_name == video_path:
                return self.__prepare_load_metadata_from_file_output_callbacks(
                    metadata_values_by_type_dict[MetaDataType.PRIMARY],
                    metadata_values_by_type_dict[MetaDataType.SECONDARY],
                    False)
            primary_metadata = self.meta_data_handler.get_metadata_file_from_blob(video_path, MetaDataType.PRIMARY,
                                                                                  row_selected)
            secondary_metadata = self.meta_data_handler.get_metadata_file_from_blob(video_path, MetaDataType.SECONDARY,
                                                                                    row_selected)
            self.is_ready_to_load_metadata = True
            return self.__prepare_load_metadata_from_file_output_callbacks(primary_metadata, secondary_metadata, False)

        if f"{SheldonVisionConstants.LOCAL_FILE_NOT_FOUND_ID}.{SheldonVisionConstants.CANCEL_N_CLICKS}" in triggered_callback:
            return self.__prepare_load_metadata_from_file_output_callbacks(
                metadata_values_by_type_dict[MetaDataType.PRIMARY],
                metadata_values_by_type_dict[MetaDataType.SECONDARY],
                False)

    def __prepare_load_metadata_from_file_output_callbacks(self, primary_metadata_label=dash.no_update,
                                                           secondary_metadata_label=dash.no_update,
                                                           local_file_not_found_popup=False):
        """
        create list of callbacks for load metadata from file_output callbacks
        @param primary_metadata_label:
        @param secondary_metadata_label:
        @param local_file_not_found_popup:
        @return:
        """
        no_file_loaded = html.Div(SheldonVisionConstants.NO_FILES_SELECTED_JSON,
                                  style=SheldonVisionConstants.HIGHLIGHT_TEXT_STYLE)
        primary_metadata_filename = self.meta_data_handler.get_metadata_filename(MetaDataType.PRIMARY.value)
        secondary_metadata_filename = self.meta_data_handler.get_metadata_filename(MetaDataType.SECONDARY.value)
        if primary_metadata_label is None and not primary_metadata_filename:
            primary_metadata_label = no_file_loaded
        elif primary_metadata_label is None:
            primary_metadata_label = dash.no_update
        elif primary_metadata_label != dash.no_update:
            primary_metadata_label = html.Div(primary_metadata_label)

        if secondary_metadata_label is None and not secondary_metadata_filename:
            secondary_metadata_label = no_file_loaded
        elif secondary_metadata_label is None:
            secondary_metadata_label = dash.no_update
        elif secondary_metadata_label != dash.no_update:
            secondary_metadata_label = html.Div(secondary_metadata_label)

        return [primary_metadata_label, secondary_metadata_label, local_file_not_found_popup]

    def __on_autorun(self):
        current_video_file_name = self.autorun_from_mail.get('video')
        frame_number = self.autorun_from_mail.get('frame_number')
        primary_metadata = self.autorun_from_mail.get('primary_metadata_path')
        secondary_metadata = self.autorun_from_mail.get('secondary_metadata_path')
        if primary_metadata:
            self.meta_data_handler.load_metadata_file(primary_metadata, MetaDataType.PRIMARY)
        if secondary_metadata:
            self.meta_data_handler.load_metadata_file(secondary_metadata, MetaDataType.SECONDARY)
        if self.previous_video_file_name is None or self.previous_video_file_name != current_video_file_name:
            self.previous_video_file_name = current_video_file_name
            main_ui_output_callbacks = self.__load_video_from_file(current_video_file_name, is_from_dialog=False)[
                SheldonVisionConstants.VIDEO_DATA_IDX]
            time.sleep(SheldonVisionConstants.HALF_SECOND)
            self.__set_frame_number(frame_number)
            self.__check_frame_number_validity(frame_number + 1)
            self.current_frame_number = frame_number
            primary_metadata_general = self.create_meta_data_general(MetaDataType.PRIMARY)
            secondary_metadata_general = self.create_meta_data_general(MetaDataType.SECONDARY)
            offline_graph = self.create_offline_graph(frame_number, MetaDataType.PRIMARY)
            offline_graph_secondary = self.create_offline_graph(frame_number, MetaDataType.SECONDARY)
            sheldon_helpers.modify_main_ui_output_callbacks(main_ui_output_callbacks, slider_value=frame_number,
                                                            frame_input_number_value=frame_number,
                                                            primary_graph_offline_figure=offline_graph,
                                                            secondary_graph_offline_figure=offline_graph_secondary,
                                                            primary_metadata_general=primary_metadata_general,
                                                            secondary_metadata_general=secondary_metadata_general)
        else:
            self.__set_frame_number(frame_number)
            self.__check_frame_number_validity(frame_number + 1)
            primary_metadata_general = self.create_meta_data_general(MetaDataType.PRIMARY)
            secondary_metadata_general = self.create_meta_data_general(MetaDataType.SECONDARY)
            offline_graph = self.create_offline_graph(frame_number, MetaDataType.PRIMARY)
            offline_graph_secondary = self.create_offline_graph(frame_number, MetaDataType.SECONDARY)
            marks = self.__set_marks()
            main_ui_output_callbacks = sheldon_helpers.prepare_main_ui_output_callbacks(slider_value=frame_number,
                                                                                        frame_input_number_value=frame_number,
                                                                                        primary_graph_offline_figure=offline_graph,
                                                                                        secondary_graph_offline_figure=offline_graph_secondary,
                                                                                        primary_metadata_general=primary_metadata_general,
                                                                                        secondary_metadata_general=secondary_metadata_general,
                                                                                        slider_marks_value=marks)

        main_ui_output_callbacks.extend(self.__get_graphs_div_display_status())
        self.waiting_autorun_main_ui = AutoRunStatus.UNAVAILABLE
        return main_ui_output_callbacks

    def __on_video_browser_button_click(self, file_name=None, is_from_dialog=True):
        """
        Execute logic following a click on the browse video button or a URI input.
        Parameters:
        -----------
            file_name : The video name chosen or the URI inserted.
            is_from_dialog : A boolean indicating whether file_name is a file(T) or a URI(F).
        Returns:
        --------
            main_ui_output_callbacks : A series of callbacks modified following the file chosen.
        """
        current_frame_number = self.get_current_frame_number_method_callback() or 1
        main_ui_output_callbacks, has_exception_occurred = self.__load_video_from_file(file_name=file_name, is_from_dialog=is_from_dialog)
        if has_exception_occurred:
            main_ui_output_callbacks.extend(self.__get_graphs_div_display_status())
            return main_ui_output_callbacks
        self.send_get_current_frame_method_callback()
        self.__check_frame_number_validity(current_frame_number, is_equal=True)
        offline_graph = self.create_offline_graph(current_frame_number, MetaDataType.PRIMARY)
        offline_graph_secondary = self.create_offline_graph(current_frame_number, MetaDataType.SECONDARY)
        sheldon_helpers.modify_main_ui_output_callbacks(main_ui_output_callbacks,
                                                        primary_graph_offline_figure=offline_graph,
                                                        secondary_graph_offline_figure=offline_graph_secondary,
                                                        primary_metadata_general=[],
                                                        secondary_metadata_general=[])
        main_ui_output_callbacks.extend(self.__get_graphs_div_display_status())
        return main_ui_output_callbacks

    def __check_frame_number_validity(self, frame_number: int, max_retries: int = 20, is_equal: bool = False):
        def is_frame_equal():
            is_equal_frame = self.get_current_frame_number_method_callback() == frame_number
            return is_equal_frame if is_equal else not is_equal_frame

        while is_frame_equal() and max_retries > 0:
            time.sleep(SheldonVisionConstants.TENTH_SECOND)
            max_retries -= 1

    def __set_marks(self, range_marks: list = None):
        mid = int((self.frames_range[0] + self.frames_range[1]) / 2)
        marks = {i: {'label': str(i)} for i in [self.frames_range[0], mid, self.frames_range[1]]}
        if range_marks:
            all_marks = [range_marks[mark:mark + 2] for mark in range(0, len(range_marks), 2)]
            first_mark = True
            for each_mark in all_marks:
                range_start, range_end = each_mark
                color = SheldonVisionConstants.MARK_COLOR_SELECTED if first_mark else SheldonVisionConstants.MARK_COLOR_EXTENDED
                marks[range_start] = {'label': '|', 'style': {'color': color, 'font-weight': 'bold'}}
                marks[range_end] = {'label': '|', 'style': {'color': color, 'font-weight': 'bold'}}
                if range_end - range_start > 2:
                    for i in range(range_start + 1, range_end):
                        marks[i] = {'label': '=', 'style': {'color': color, 'font-weight': 'bold'}}
                first_mark = False
        return marks

    def __load_video_from_file(self, file_name=None, is_from_dialog=True, range_marks: list = None):
        has_exception_occurred = False
        no_file_selected = sheldon_helpers.prepare_main_ui_output_callbacks(video_files_list_label=html.Div(
            SheldonVisionConstants.NO_FILES_SELECTED,
            style=SheldonVisionConstants.HIGHLIGHT_TEXT_STYLE))

        if is_from_dialog:
            file_name = self.__select_file_from_dialog_box(SheldonVisionConstants.MP4_FILES_TYPE)

        if len(file_name) == 0 and self.previous_video_file_name:
            return sheldon_helpers.prepare_main_ui_output_callbacks(), has_exception_occurred
        elif len(file_name) == 0 and not self.previous_video_file_name:
            has_exception_occurred = True
            return no_file_selected, has_exception_occurred
        else:
            if not self.verify_local_path(file_name, notify_error=False, base_path=self.alternative_base_path_video): ##TODO: Why do we need alternative_base_path_video here??
                if SheldonVisionConstants.BLOB_IDENTIFIER not in file_name:
                    blob_full_path = f'https://{self.storage_account_name}.{SheldonVisionConstants.BLOB_IDENTIFIER}/' \
                                     f'{self.container_name}/{file_name}'
                    blob_full_path_raw_data = f'https://{self.storage_account_name}.{SheldonVisionConstants.BLOB_IDENTIFIER}/' \
                                              f'{self.container_name}/raw_data/{file_name}'
                else:
                    blob_full_path = file_name
                    if '/raw_data/' not in file_name.replace('\\', '/'):
                        blob_prefix = f'https://{self.storage_account_name}.{SheldonVisionConstants.BLOB_IDENTIFIER}/{self.container_name}/'
                        blob_full_path_raw_data = file_name.replace('\\', '/').replace(blob_prefix, f'{blob_prefix}raw_data/')
                    else:
                        blob_full_path_raw_data = None

                self.get_files_list_on_blob(self.verify_blob_path(blob_full_path.replace('\\', '/')))
                files_found = [f for f in self.files_list_on_blob() if f.endswith(SheldonVisionConstants.MP4_SUFFIX)]
                if files_found:
                    file_name = blob_full_path
                elif blob_full_path_raw_data:
                    self.get_files_list_on_blob(self.verify_blob_path(blob_full_path_raw_data.replace('\\', '/')))
                    files_found = [f for f in self.files_list_on_blob() if f.endswith(SheldonVisionConstants.MP4_SUFFIX)]
                    if files_found:
                        file_name = blob_full_path_raw_data

                if not files_found:
                    self.notifications.notify_error('SheldonVision', f'Video not found on Blob - {file_name}')
                    logging.error(f'Video not found on Blob - {file_name}')
                    has_exception_occurred = True
                    return sheldon_helpers.prepare_main_ui_output_callbacks(), has_exception_occurred

            self.send_stop_message_method_callback()
            self.send_new_load_request_method_callback(file_name)
            is_valid_uri = self.validate_path_callback()
            if not is_valid_uri:
                has_exception_occurred = True
                self.notifications.notify_error(title='SheldonVision',
                                                body='Failed to load Video - Invalid URI input or CameraListenerPlugin is down')
                return sheldon_helpers.prepare_main_ui_output_callbacks(video_files_list_label=html.Div(
                    SheldonVisionConstants.INVALID_URI,
                    style=SheldonVisionConstants.HIGHLIGHT_TEXT_STYLE)), has_exception_occurred
            else:
                self.previous_video_file_name = file_name
            self.frames_range = self.get_frames_range_callback()
            self.clear_frames_queue_method_callback()
            self.fps = self.configurations.get_item(SheldonVisionConstants.CONFIG_FPS)
            if self.fps:
                self.set_fps_callback(self.fps)
            else:
                self.fps = self.get_fps_callback()

            marks = self.__set_marks(range_marks)

            self.are_player_buttons_disabled = False
            self.notifications.notify_info('SheldonVision', f'Video loaded successfully - {file_name}')
            self.current_frame_number = 0
            return sheldon_helpers.prepare_main_ui_output_callbacks(slider_value=0, frame_input_number_value=0,
                                                                    slider_min_value=self.frames_range[0],
                                                                    slider_max_value=self.frames_range[1],
                                                                    slider_fps_value=self.fps,
                                                                    fps_input_value=self.fps,
                                                                    slider_marks_value=marks,
                                                                    video_files_list_label=html.Div(
                                                                        file_name)), has_exception_occurred

    def load_recordings_debug_data_from_file(self, browse_button_n_clicks, cell, add_row_n_clicks, add_column_n_clicks, jump_local,
                                             load_jump_http, modal_ok, table_data, columns, rows_data, input_value, modal_input, modal_type):

        triggered_callback = []
        for index in range(0, len(dash.callback_context.triggered)):
            triggered_callback.append(dash.callback_context.triggered[index][PROP_ID])

        file_name = self.configurations.get_item(SheldonVisionConstants.CONFIG_DEBUG_FILE_PATH)
        is_label_hidden = False
        if f'{SheldonVisionConstants.DEBUG_ADD_ROW_BUTTON}.n_clicks' in triggered_callback and add_row_n_clicks > 0 and self.debug_data_frame is not None:
            rows_data.append({c[ID]: '' for c in columns})
            return sheldon_helpers.prepare_jump_output_callback(recording_label_visible=not is_label_hidden,
                                                                recording_table_div_visible=is_label_hidden,
                                                                table_data=rows_data,
                                                                table_columns=columns)

        if f'{SheldonVisionConstants.DEBUG_ADD_COLUMN_BUTTON}.n_clicks' in triggered_callback and add_column_n_clicks > 0 and \
                self.debug_data_frame is not None:
            if not input_value:
                return sheldon_helpers.prepare_jump_output_callback(recording_label_visible=not is_label_hidden,
                                                                    recording_table_div_visible=is_label_hidden,
                                                                    error_message_visible=True,
                                                                    error_message_msg='Column name cannot be empty')

            if [x for x in columns if x['name'] == input_value]:  # validation existing column
                return sheldon_helpers.prepare_jump_output_callback(recording_label_visible=not is_label_hidden,
                                                                    recording_table_div_visible=is_label_hidden,
                                                                    error_message_visible=True,
                                                                    error_message_msg=f'Column already exists: {input_value}')

            columns.append({
                    'id': input_value, 'name': input_value,
                    'renamable': True, 'deletable': True})
            return sheldon_helpers.prepare_jump_output_callback(recording_label_visible=not is_label_hidden,
                                                                recording_table_div_visible=is_label_hidden,
                                                                table_data=rows_data,
                                                                table_columns=columns)

        if f'{SheldonVisionConstants.JUMP_LOADING_LABEL_ID}.hidden' in triggered_callback:
            if self.waiting_jump_loading == AutoRunStatus.WAITING:
                file_name = self.jump_path_http
                self.jump_path_http = None
                self.waiting_jump_loading = AutoRunStatus.LOADING
            else:
                self.jump_path_http = None
                self.waiting_jump_loading = AutoRunStatus.UNAVAILABLE
                return sheldon_helpers.prepare_jump_output_callback()

        if browse_button_n_clicks is None and file_name is None:
            return sheldon_helpers.prepare_jump_output_callback(recording_label_visible=is_label_hidden,
                                                                recording_table_div_visible=is_label_hidden)

        if f"{SheldonVisionConstants.DEBUG_EDITABLE_TABLE}.{SheldonVisionConstants.ACTIVE_CELL_ID}" in triggered_callback:
            data = is_checked_modify_value(cell, table_data)
            return sheldon_helpers.prepare_jump_output_callback(recording_label_visible=not is_label_hidden,
                                                                recording_table_div_visible=is_label_hidden,
                                                                table_data=dash.no_update if data is None else data)

        if not file_name or f"{SheldonVisionConstants.BROWSE_RECORDINGS_DEBUG_DATA_BUTTON_ID}.n_clicks" in triggered_callback or \
                f"{SheldonVisionConstants.DROP_DOWN_JUMP_LOCAL}.n_clicks" in triggered_callback:
            file_name = self.__select_file_from_dialog_box(SheldonVisionConstants.JUMP_FILES_TYPE)

            if len(file_name) == 0 and not self.meta_data_handler.is_jump_file_loaded:
                return sheldon_helpers.prepare_jump_output_callback(recording_label_visible=is_label_hidden,
                                                                    recording_table_div_visible=not is_label_hidden)
            elif len(file_name) == 0:
                return sheldon_helpers.prepare_jump_output_callback()

        if f'{SheldonVisionConstants.INPUT_METADATA_MODAL_OK}.n_clicks' in triggered_callback and modal_input and modal_type == 'Jump':
            file_name = modal_input
        elif f'{SheldonVisionConstants.INPUT_METADATA_MODAL_OK}.n_clicks' in triggered_callback:
            return sheldon_helpers.prepare_jump_output_callback(error_message_visible=dash.no_update)

        self.debug_data_frame, error_counter = self.meta_data_handler.load_multiple_recordings_debug_file(file_name)
        if self.debug_data_frame is None:
            return sheldon_helpers.prepare_jump_output_callback(recording_label_visible=is_label_hidden,
                                                                recording_table_div_visible=not is_label_hidden)

        elif self.debug_data_frame is not None:
            col = [{"name": i, "id": i, 'deletable': True, 'renamable': True} for i in self.debug_data_frame.columns]
            data = self.debug_data_frame.to_dict('records')
            if error_counter == 0:
                self.notifications.notify_info('SheldonVision', 'Jump file loaded successfully')
            else:
                self.notifications.notify_warning('SheldonVision', 'Jump file loaded successfully but some issues detected')
            return sheldon_helpers.prepare_jump_output_callback(recording_label_visible=not is_label_hidden,
                                                                recording_table_div_visible=is_label_hidden,
                                                                table_data=data,
                                                                table_columns=col,
                                                                jump_file_location=file_name)

        self.waiting_jump_loading = AutoRunStatus.UNAVAILABLE
        return sheldon_helpers.prepare_jump_output_callback(recording_label_visible=False,
                                                            recording_table_div_visible=True)

    def export_recordings_debug_data_to_file(self, export_button_n_clicks, table_data):
        if export_button_n_clicks is None:
            return dash.no_update

        file_name = self.__select_file_from_dialog_box(SheldonVisionConstants.JSON_FILES_TYPE, is_save_as_dialog=True)
        self.meta_data_handler.create_multiple_recordings_to_export(table_data, file_name)
        return dash.no_update

    def __set_frame_number(self, frame_number):
        self.clear_frames_queue_method_callback(True)
        self.send_set_frame_message_method_callback(frame_number)
        self.send_get_current_frame_method_callback()
        self.__check_frame_number_validity(int(frame_number) + 1)

    def __collect_clip_data_and_all_range_marks(self, debug_data_table, row_selected):
        base_video_file_name = debug_data_table[row_selected]['Video Location']
        current_video_file_name = self.__get_video_full_path(base_video_file_name)
        frame_number = debug_data_table[row_selected]['Frame Number']
        end_frame_number = debug_data_table[row_selected]['end_frame'] if 'end_frame' in debug_data_table[row_selected] else None
        range_mark = [frame_number, end_frame_number] if end_frame_number else None
        if range_mark:
            for row in debug_data_table:
                if (row['Video Location'] == current_video_file_name or row['Video Location'] == base_video_file_name) and \
                        row['Frame Number'] != frame_number and 'end_frame' in row:
                    range_mark.append(row['Frame Number'])
                    range_mark.append(row['end_frame'])
        return current_video_file_name, frame_number, range_mark

    def __get_video_full_path(self, video_path: str):
        header_video_base_path = self.meta_data_handler.get_video_path()
        video_base_path_to_use = self.alternative_base_path_video if self.alternative_base_path_video else header_video_base_path

        video_suffix = self.meta_data_handler.get_video_suffix()
        if video_base_path_to_use and not video_path.startswith(video_base_path_to_use):
            video_path = os.path.join(video_base_path_to_use, video_path)
        if video_suffix and not video_path.endswith(video_suffix):
            video_path = video_path + video_suffix
        if self.verify_local_path(os.path.normpath(video_path), notify_error=False):
            return os.path.normpath(video_path)
        
        if SheldonVisionConstants.BLOB_IDENTIFIER in video_path:
            return video_path
        elif SheldonVisionConstants.BLOB_IDENTIFIER not in video_path and self.storage_account_name and self.container_name:
            return f'https://{self.storage_account_name}.{SheldonVisionConstants.BLOB_IDENTIFIER}/{self.container_name}/{video_path}'
        else:
            self.notifications.notify_error('SheldonVision', 'Blob details are not configured - Cannot load video')
            logging.error(f'Error with blob details, account: {self.storage_account_name}, container: {self.container_name}')
            return ''

    def __get_range_marks_by_clip_name(self):
        if self.previous_video_file_name and self.meta_data_handler.is_jump_file_loaded:
            return self.meta_data_handler.get_all_jump_frame_range_by_clip_path(self.previous_video_file_name)
        return []

    def __load_new_debug_recording(self, active_debug_table_cell, debug_data_table):
        if self.is_ready_to_load_metadata:
            self.is_ready_to_load_metadata = False
            row_selected = active_debug_table_cell[ROW]
            current_video_file_name, frame_number, range_mark = self.__collect_clip_data_and_all_range_marks(
                debug_data_table, row_selected)
            if current_video_file_name and (self.previous_video_file_name is None or self.previous_video_file_name != current_video_file_name):
                primary_metadata = self.meta_data_handler.get_debug_metadata_file_path(current_video_file_name,
                                                                                       MetaDataType.PRIMARY,
                                                                                       row_selected,
                                                                                       False)
                secondary_metadata = self.meta_data_handler.get_debug_metadata_file_path(current_video_file_name,
                                                                                         MetaDataType.SECONDARY,
                                                                                         row_selected,
                                                                                         False)
                if not primary_metadata:
                    primary_metadata = self.meta_data_handler.get_metadata_file_from_blob(current_video_file_name,
                                                                                          MetaDataType.PRIMARY,
                                                                                          row_selected)
                if not secondary_metadata:
                    secondary_metadata = self.meta_data_handler.get_metadata_file_from_blob(current_video_file_name,
                                                                                            MetaDataType.SECONDARY,
                                                                                            row_selected)
                self.meta_data_handler.load_metadata_file(primary_metadata, MetaDataType.PRIMARY)
                self.meta_data_handler.load_metadata_file(secondary_metadata, MetaDataType.SECONDARY)
                self.previous_video_file_name = current_video_file_name
                main_ui_output_callbacks, has_exception_occurred = self.__load_video_from_file(current_video_file_name, is_from_dialog=False,
                                                                                               range_marks=range_mark)
                if has_exception_occurred:
                    self.notifications.notify_error('SheldonVision',
                                                    f'Failed to load video - {current_video_file_name}')
                    logging.error(f'Failed to load video - {current_video_file_name}')
                    main_ui_output_callbacks = sheldon_helpers.prepare_main_ui_output_callbacks()
                    main_ui_output_callbacks.extend(self.__get_graphs_div_display_status())
                    return main_ui_output_callbacks
                time.sleep(SheldonVisionConstants.HALF_SECOND)
                self.__set_frame_number(frame_number)
                self.__check_frame_number_validity(frame_number + 1)
                self.current_frame_number = frame_number
                primary_metadata_general = self.create_meta_data_general(MetaDataType.PRIMARY)
                secondary_metadata_general = self.create_meta_data_general(MetaDataType.SECONDARY)
                offline_graph = self.create_offline_graph(frame_number, MetaDataType.PRIMARY)
                offline_graph_secondary = self.create_offline_graph(frame_number, MetaDataType.SECONDARY)
                sheldon_helpers.modify_main_ui_output_callbacks(main_ui_output_callbacks, slider_value=frame_number,
                                                                frame_input_number_value=frame_number,
                                                                primary_graph_offline_figure=offline_graph,
                                                                secondary_graph_offline_figure=offline_graph_secondary,
                                                                primary_metadata_general=primary_metadata_general,
                                                                secondary_metadata_general=secondary_metadata_general)
                main_ui_output_callbacks.extend(self.__get_graphs_div_display_status())
                return main_ui_output_callbacks
            elif not current_video_file_name:
                main_ui_output_callbacks = sheldon_helpers.prepare_main_ui_output_callbacks()
                main_ui_output_callbacks.extend(self.__get_graphs_div_display_status())
                return main_ui_output_callbacks
            else:
                self.current_frame_number = frame_number
                return self.__create_offline_graph_for_frame(frame_number, range_mark)
        else:
            main_ui_output_callbacks = sheldon_helpers.prepare_main_ui_output_callbacks()
            main_ui_output_callbacks.extend(self.__get_graphs_div_display_status())
            return main_ui_output_callbacks

    def __on_dropdown_selection_change(self, primary_graph_dropdown_value, secondary_graph_dropdown_value,
                                       frames_slider_value):
        self.__update_graph_dropdown_values(primary_graph_dropdown_value, secondary_graph_dropdown_value)
        offline_graph = dash.no_update
        offline_graph_secondary = dash.no_update

        if not self.is_playing:
            offline_graph = self.create_offline_graph(frames_slider_value, MetaDataType.PRIMARY)
            offline_graph_secondary = self.create_offline_graph(frames_slider_value, MetaDataType.SECONDARY)

        main_ui_output_callbacks = sheldon_helpers.prepare_main_ui_output_callbacks(
            primary_graph_offline_figure=offline_graph,
            secondary_graph_offline_figure=offline_graph_secondary)
        main_ui_output_callbacks.extend(self.__get_graphs_div_display_status())

        return main_ui_output_callbacks

    def __on_fast_back_button_click(self):
        first_frame_number = 0
        self.__set_frame_number(first_frame_number)

        offline_graph = self.create_offline_graph(first_frame_number, MetaDataType.PRIMARY)
        offline_graph_secondary = self.create_offline_graph(first_frame_number, MetaDataType.SECONDARY)
        primary_metadata_general = self.create_meta_data_general(MetaDataType.PRIMARY)
        secondary_metadata_general = self.create_meta_data_general(MetaDataType.SECONDARY)

        main_ui_output_callbacks = sheldon_helpers.prepare_main_ui_output_callbacks(
            slider_value=first_frame_number,
            frame_input_number_value=first_frame_number,
            primary_graph_offline_figure=offline_graph,
            secondary_graph_offline_figure=offline_graph_secondary,
            primary_metadata_general=primary_metadata_general,
            secondary_metadata_general=secondary_metadata_general)

        main_ui_output_callbacks.extend(self.__get_graphs_div_display_status())

        return main_ui_output_callbacks

    def __on_pause_button_click(self):
        self.send_pause_message_method_callback()
        current_frame_number = self.get_current_frame_number_method_callback()
        self.current_frame_number = current_frame_number
        if current_frame_number == self.frames_range[1]:
            self.clear_frames_queue_method_callback(True)
            main_ui_output_callbacks = sheldon_helpers.prepare_main_ui_output_callbacks()
            main_ui_output_callbacks.extend(self.__get_graphs_div_display_status())
            return main_ui_output_callbacks

        offline_graph = self.create_offline_graph(current_frame_number, MetaDataType.PRIMARY)
        offline_graph_secondary = self.create_offline_graph(current_frame_number, MetaDataType.SECONDARY)
        primary_metadata_general = self.create_meta_data_general(MetaDataType.PRIMARY)
        secondary_metadata_general = self.create_meta_data_general(MetaDataType.SECONDARY)

        main_ui_output_callbacks = sheldon_helpers.prepare_main_ui_output_callbacks(
            slider_value=current_frame_number,
            frame_input_number_value=current_frame_number,
            primary_graph_offline_figure=offline_graph,
            secondary_graph_offline_figure=offline_graph_secondary,
            primary_metadata_general=primary_metadata_general,
            secondary_metadata_general=secondary_metadata_general)

        main_ui_output_callbacks.extend(self.__get_graphs_div_display_status())

        return main_ui_output_callbacks

    def __on_slider_interval_tick(self, pause_button_n_clicks, frames_slider_value):
        current_frame_number = self.get_current_frame_number_method_callback()
        if pause_button_n_clicks is not None or not self.is_playing:
            offline_graph = self.create_offline_graph(frames_slider_value, MetaDataType.PRIMARY)
            offline_graph_secondary = self.create_offline_graph(frames_slider_value, MetaDataType.SECONDARY)
            primary_metadata_general = self.create_meta_data_general(MetaDataType.PRIMARY)
            secondary_metadata_general = self.create_meta_data_general(MetaDataType.SECONDARY)

            main_ui_output_callbacks = sheldon_helpers.prepare_main_ui_output_callbacks(
                slider_value=current_frame_number,
                frame_input_number_value=current_frame_number,
                primary_graph_offline_figure=offline_graph,
                secondary_graph_offline_figure=offline_graph_secondary,
                primary_metadata_general=primary_metadata_general,
                secondary_metadata_general=secondary_metadata_general,
                video_files_list_label=html.Div(self.previous_video_file_name))
            main_ui_output_callbacks.extend(self.__get_graphs_div_display_status())

            return main_ui_output_callbacks

        if self.is_on_dragging:
            main_ui_output_callbacks = sheldon_helpers.prepare_main_ui_output_callbacks()
        else:
            main_ui_output_callbacks = sheldon_helpers.prepare_main_ui_output_callbacks(
                slider_value=current_frame_number,
                frame_input_number_value=current_frame_number,
                primary_metadata_general=[],
                secondary_metadata_general=[])

        main_ui_output_callbacks.extend(self.__get_graphs_div_display_status())
        return main_ui_output_callbacks

    def __on_back_forward_button_click(self, frames_slider_value):
        offline_graph = self.create_offline_graph(frames_slider_value, MetaDataType.PRIMARY)
        offline_graph_secondary = self.create_offline_graph(frames_slider_value, MetaDataType.SECONDARY)
        primary_metadata_general = self.create_meta_data_general(MetaDataType.PRIMARY)
        secondary_metadata_general = self.create_meta_data_general(MetaDataType.SECONDARY)

        main_ui_output_callbacks = sheldon_helpers.prepare_main_ui_output_callbacks(
            slider_value=frames_slider_value,
            frame_input_number_value=frames_slider_value,
            primary_graph_offline_figure=offline_graph,
            secondary_graph_offline_figure=offline_graph_secondary,
            primary_metadata_general=primary_metadata_general,
            secondary_metadata_general=secondary_metadata_general)

        main_ui_output_callbacks.extend(self.__get_graphs_div_display_status())
        return main_ui_output_callbacks

    def __create_offline_graph_for_frame(self, frames_number, meta_data_type: MetaDataType = None):
        def verify_callback_necessity():
            return self.current_frame_number != frames_number

        def exit_callback():
            main_ui_output_callbacks = sheldon_helpers.prepare_main_ui_output_callbacks(
                frame_input_number_value=self.current_frame_number if not self.is_playing else dash.no_update,
                slider_value=self.current_frame_number if not self.is_playing else dash.no_update)
            main_ui_output_callbacks.extend(self.__get_graphs_div_display_status())
            return main_ui_output_callbacks

        def verify_graph_created_successfully(metadata_type: MetaDataType, num_of_retries: int = 5):
            offline_graph = self.create_offline_graph(frames_number, metadata_type)
            if verify_callback_necessity():
                return dash.no_update, False

            while offline_graph is None and num_of_retries > 0:
                num_of_retries -= 1
                offline_graph = self.create_offline_graph(frames_number, metadata_type)
                if verify_callback_necessity():
                    return dash.no_update, False
            return offline_graph, True

        if self.is_playing:
            self.__set_frame_number(frames_number)
            return exit_callback()

        offline_graph_update = dash.no_update
        offline_graph_secondary_update = dash.no_update
        primary_metadata_general = dash.no_update
        secondary_metadata_general = dash.no_update
        match meta_data_type:
            case MetaDataType.PRIMARY:
                offline_graph_update = self.create_offline_graph(frames_number, MetaDataType.PRIMARY)
                primary_metadata_general = self.create_meta_data_general(MetaDataType.PRIMARY)
            case MetaDataType.SECONDARY:
                offline_graph_secondary_update = self.create_offline_graph(frames_number, MetaDataType.SECONDARY)
                secondary_metadata_general = self.create_meta_data_general(MetaDataType.SECONDARY)
            case _:
                offline_graph_update, is_ok = verify_graph_created_successfully(MetaDataType.PRIMARY, 5)
                if not is_ok:
                    return exit_callback()
                offline_graph_secondary_update, is_ok = verify_graph_created_successfully(MetaDataType.SECONDARY, 5)
                if not is_ok:
                    return exit_callback()
                primary_metadata_general = self.create_meta_data_general(MetaDataType.PRIMARY)
                if verify_callback_necessity():
                    return exit_callback()
                secondary_metadata_general = self.create_meta_data_general(MetaDataType.SECONDARY)

        main_ui_output_callbacks = sheldon_helpers.prepare_main_ui_output_callbacks(
            slider_value=int(frames_number),
            frame_input_number_value=frames_number,
            primary_graph_offline_figure=offline_graph_update,
            secondary_graph_offline_figure=offline_graph_secondary_update,
            primary_metadata_general=primary_metadata_general,
            secondary_metadata_general=secondary_metadata_general)

        main_ui_output_callbacks.extend(self.__get_graphs_div_display_status())
        return main_ui_output_callbacks
    def __set_auto_range(self, auto_range):
        for meta_data_type in MetaDataType:
            if self.fig[meta_data_type] is None or self.fig[meta_data_type].layout.xaxis.range is None or \
                    self.fig[meta_data_type].layout.yaxis.range is None:
                return
            self.fig[meta_data_type].update_xaxes(
                autorange=auto_range)
            self.fig[meta_data_type].update_yaxes(
                autorange=auto_range)

    def __on_close_network_click(self, n_clicks):
        if n_clicks is None:
            return dash.no_update
        self.close_network(close_type=SigmundCloseTypeProto.Value('Hard'))
        os._exit(0)

    def __update_figures_zoom_levels(self, meta_data_type: MetaDataType = MetaDataType.PRIMARY):
        XAXIS = 'xaxis'
        YAXIS = 'yaxis'
        XAXIS_AUTO_RANGE = f'{XAXIS}.autorange'
        YAXIS_AUTO_RANGE = f'{YAXIS}.autorange'
        RANGE_0 = 'range[0]'
        RANGE_1 = 'range[1]'

        x_start_range = self.last_figure_layout.get(f'{XAXIS}.{RANGE_0}')
        x_stop_range = self.last_figure_layout.get(f'{XAXIS}.{RANGE_1}')
        y_start_range = self.last_figure_layout.get(f'{YAXIS}.{RANGE_0}')
        y_stop_range = self.last_figure_layout.get(f'{YAXIS}.{RANGE_1}')

        success = True

        if XAXIS_AUTO_RANGE in self.last_figure_layout and YAXIS_AUTO_RANGE in self.last_figure_layout:
            self.__set_auto_range(True)
        elif (x_start_range and x_start_range < 0) or (y_start_range and y_start_range < 0):
            self.__set_auto_range(True)
        elif x_start_range and x_stop_range and y_start_range and y_stop_range:
            self.__set_auto_range(False)
            x_start_range = self.last_figure_layout[f'{XAXIS}.{RANGE_0}']
            x_stop_range = self.last_figure_layout[f'{XAXIS}.{RANGE_1}']
            y_start_range = self.last_figure_layout[f'{YAXIS}.{RANGE_0}']
            y_stop_range = self.last_figure_layout[f'{YAXIS}.{RANGE_1}']

            self.fig[MetaDataType.PRIMARY].update_xaxes(range=[x_start_range, x_stop_range]).update_yaxes(range=[y_start_range, y_stop_range])
            self.fig[MetaDataType.SECONDARY].update_xaxes(range=[x_start_range, x_stop_range]).update_yaxes(range=[y_start_range, y_stop_range])
        else:
            success = False

        return success

    def __handle_figures_zoom_level(self, triggered_callback, primary_relayout_data, secondary_relayout_data,
                                    meta_data_type: MetaDataType = MetaDataType.PRIMARY):
        is_layout = False
        if any(SheldonVisionConstants.PRIMARY_GRAPH_OFFLINE_FIGURE_ID in s for s in triggered_callback):
            self.last_figure_layout = primary_relayout_data
            is_layout = True
        elif any(SheldonVisionConstants.SECONDARY_GRAPH_OFFLINE_FIGURE_ID in s for s in triggered_callback):
            self.last_figure_layout = secondary_relayout_data
            is_layout = True

        if is_layout and not self.__page_refresh and self.fig[meta_data_type] is not None:
            if self.__update_figures_zoom_levels():
                output_callbacks = sheldon_helpers.prepare_main_ui_output_callbacks(
                    primary_graph_offline_figure=self.fig[MetaDataType.PRIMARY],
                    secondary_graph_offline_figure=self.fig[MetaDataType.SECONDARY])
                output_callbacks.extend(self.__get_graphs_div_display_status())
                return True, output_callbacks
        output_callbacks = sheldon_helpers.prepare_main_ui_output_callbacks()
        output_callbacks.extend(self.__get_graphs_div_display_status())
        return False, output_callbacks

    def __handle_metadata_loading_from_config(self, meta_data_type: MetaDataType):
        metadata_path = self.configurations.get_item(SheldonVisionConstants.CONFIG_METADATA_FILE_PATH, meta_data_type.value)
        if metadata_path:
            while self.meta_data_handler.loading_metadata:  # avoiding override data
                time.sleep(0.05)
            self.meta_data_handler.load_metadata_file(metadata_path, meta_data_type)
            return [html.Div(metadata_path)]
        else:
            return [html.Div(SheldonVisionConstants.NO_FILES_SELECTED_JSON,
                             style=SheldonVisionConstants.HIGHLIGHT_TEXT_STYLE)]

    def __on_fps_change(self, fps_value):
        self.set_fps_callback(fps_value)
        self.fps = fps_value
        output_callbacks = sheldon_helpers.prepare_main_ui_output_callbacks(fps_input_value=fps_value, slider_fps_value=fps_value)
        output_callbacks.extend(self.__get_graphs_div_display_status())
        return output_callbacks

    def __on_speed_change(self, speed_value_slider):
        int_speed_value = int(speed_value_slider)
        self.speed = SheldonVisionConstants.DECIMATION_SPEED_VALUES[int_speed_value]
        output_callbacks = sheldon_helpers.prepare_main_ui_output_callbacks(slider_speed_value=int_speed_value,
                                                                            input_speed_value=self.speed)
        output_callbacks.extend(self.__get_graphs_div_display_status())
        return output_callbacks

    def __on_decimation_button_clicked(self, slider_fps_style, slider_speed_style):
        decimation_button_style = SheldonVisionConstants.DECIMATION_BUTTONS_STYLE
        decimation_button_style['background-color'] = SheldonVisionConstants.DECIMATION_COLOR_OFF
        slider_style_on = {'display': 'block'}
        slider_style_off = {'display': 'none'}

        if not self.meta_data_handler.is_metadata_file_loaded:
            output_callbacks = sheldon_helpers.prepare_main_ui_output_callbacks(
                decimation_button_style=decimation_button_style,
                slider_fps_style=slider_style_on,
                slider_speed_style=slider_style_off)

        else:
            self.is_decimated = not self.is_decimated

            if self.is_decimated:
                decimation_button_style['background-color'] = SheldonVisionConstants.DECIMATION_COLOR_ON
                output_callbacks = sheldon_helpers.prepare_main_ui_output_callbacks(
                    decimation_button_style=decimation_button_style,
                    slider_fps_style=slider_style_off,
                    slider_speed_style=slider_style_on)

            else:
                decimation_button_style['background-color'] = SheldonVisionConstants.DECIMATION_COLOR_OFF
                output_callbacks = sheldon_helpers.prepare_main_ui_output_callbacks(decimation_button_style=decimation_button_style,
                                                                                    slider_fps_style=slider_style_on,
                                                                                    slider_speed_style=slider_style_off)
        output_callbacks.extend(self.__get_graphs_div_display_status())
        return output_callbacks

    def download_file_from_blob(self, metadata_file: str, metadata_type: MetaDataType, timeout_seconds: float = 30) -> str:
        local_dir = os.path.join(SheldonVisionConstants.LOCAL_METADATA_DOWNLOAD_LOCATION, str(metadata_type.value))
        file_path = self.meta_data_handler.verify_blob_path(metadata_file)
        return self.download_file_from_blob_callback(file_path, local_dir, timeout_seconds)

    def handle_autorun_from_mail(self, video_path: str, primary_metadata: str, secondary_metadata: str, frame_number: int):
        self.autorun_from_mail = {'video': video_path, 'frame_number': frame_number}
        if primary_metadata:
            primary_metadata_path = self.download_file_from_blob(primary_metadata, MetaDataType.PRIMARY)
            self.autorun_from_mail['primary_metadata_path'] = primary_metadata_path
            self.autorun_from_mail['primary_metadata_path_blob'] = primary_metadata
            self.waiting_autorun_metadata_primary = AutoRunStatus.WAITING

        if secondary_metadata:
            secondary_metadata_path = self.download_file_from_blob(secondary_metadata, MetaDataType.SECONDARY)
            self.autorun_from_mail['secondary_metadata_path'] = secondary_metadata_path
            self.autorun_from_mail['secondary_metadata_path_blob'] = secondary_metadata
            self.waiting_autorun_metadata_secondary = AutoRunStatus.WAITING

        self.waiting_autorun_main_ui = AutoRunStatus.WAITING

    def handle_load_jump_http(self, jump_path: str):
        self.jump_path_http = jump_path
        self.waiting_jump_loading = AutoRunStatus.WAITING
