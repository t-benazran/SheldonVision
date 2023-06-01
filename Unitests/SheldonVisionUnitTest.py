import sys
import os
import unittest
from unittest import mock

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from PyPluginBase.Transport.TestingTransport import TestingTransport
from PyPluginBase.UnitTestsInfra.SigmundUnitTestCommon import *
from PyPluginBase.Common import Constants
from PluginSheldonVision.PluginSheldonVisionUi import *
from PluginSheldonVision.MetaDataHandler import KEYS, FRAME_ID, NO_DATA_MESSAGE, MetaDataType, CHECKED_ICON, UNCHECKED_ICON, TYPE, DEBUG, \
    MESSAGE
from PluginSheldonVision.Constants import CONFIG_VIDEO_FILE_PATH, CONFIG_DEBUG_FILE_PATH, CONFIG_METADATA_FILE_PATH, \
    CONFIG_PRIMARY_SECTION, CONFIG_LAYERS_LIST, CONFIG_SECONDARY_SECTION
from PluginSheldonVision.PluginSheldonVisionUiDashModule import MainSheldonVisionUI
from dash._callback_context import context_value
from dash._utils import AttributeDict
from SheldonCommon.Constants import N_CLICKS_ID, TRIGGER_INPUTS_ID

DEFAULT_PLUGIN_NAME = 'TestPlugin'
SIGMUND_TYPE = "Sigmund"
CLOSE_NETWORK_MSG = 'CloseNetworkHard'


DEBUG_BASE_TABLE_ROWS = [{"IsChecked": CHECKED_ICON, "Video Location": "C:\\Temp\\clip.mp4", "Frame Number": 1, "end_frame": 60},
                         {"IsChecked": UNCHECKED_ICON, "Video Location": "C:\\Temp\\clip.mp4", "Frame Number": 93, "end_frame": 94},
                         {"IsChecked": CHECKED_ICON, "Video Location": "C:\\Temp\\clip.mp4", "Frame Number": 96, "end_frame": 100},
                         {"IsChecked": UNCHECKED_ICON, "Video Location": "C:\\Temp\\clip.mp4", "Frame Number": 106, "end_frame": 118},
                         {"IsChecked": CHECKED_ICON, "Video Location": "C:\\Temp\\clip.mp4", "Frame Number": 120, "end_frame": 121},
                         {"IsChecked": UNCHECKED_ICON, "Video Location": "C:\\Temp\\clip.mp4", "Frame Number": 124, "end_frame": 126}]

DEBUG_BASE_TABLE_COLUMNS = [{'name': 'IsChecked', 'id': 'IsChecked', 'deletable': True, 'renamable': True},
                            {'name': 'Video Location', 'id': 'Video Location', 'deletable': True, 'renamable': True},
                            {'name': 'Frame Number', 'id': 'Frame Number', 'deletable': True, 'renamable': True},
                            {'name': 'end_frame', 'id': 'end_frame', 'deletable': True, 'renamable': True}]


class SheldonUiPluginUnitTest(unittest.TestCase):
    def setUp(self):
        self.plugin_name = "SheldonVisionPlugin"
        self.transport = TestingTransport(self.plugin_name)
        self.inputs = [CAMERA_FRAMES_MESSAGE_TYPE, TOTAL_VIDEO_FRAMES_MSG_NAME, FPS_STATUS_MESSAGE]
        self.presence_log_file_name = "presence_log.json"
        self.presence_log_file_name_secondary = "presence_log_secondary.json"
        self.inputs_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'SheldonVisionInputs'))
        self.configurations_path = os.path.abspath(os.path.join(self.inputs_path, 'configurations'))
        self.multiple_recordings_debug_file = os.path.abspath(os.path.join(self.inputs_path, "MultipleVideosDebug.json"))
        self.meta_data_file = os.path.abspath(os.path.join(self.inputs_path, self.presence_log_file_name))
        self.meta_data_file_secondary = os.path.abspath(os.path.join(self.inputs_path, self.presence_log_file_name_secondary))
        self.exception = f"{self.presence_log_file_name} not found"

    def test_init_success(self):
        """
        Test init success
        @return:
        """
        plugin = SheldonVisionUiPlugin(self.plugin_name, self.inputs, [], self.transport)
        is_init_pass = check_test_init(plugin, self.transport)

        self.assertEqual(self.plugin_name, plugin.plugin_name)
        self.assertTrue(plugin.is_plugin_registered)
        self.assertTrue(is_init_pass)
        output_msg = self.transport.get_output_message()  # Counters
        self.assertEqual(output_msg.msg_type, f"Sigmund:{Constants.PLUGIN_COUNTERS_MSG_TYPE}")

    def test_send_frame_range_msg(self):
        """
        Test sending frame range message
        @return:
        """
        number_of_frames = "700"
        plugin = SheldonVisionUiPlugin(self.plugin_name, self.inputs, [], self.transport)
        send_registration_ack_message(self.plugin_name, self.transport)

        sigmund_msg = SigmundMsg(TOTAL_VIDEO_FRAMES_MSG_NAME, DEFAULT_PLUGIN_NAME, number_of_frames, "")

        self.transport.send_message_to_plugin(sigmund_msg)
        send_stop_message(self.plugin_name, self.transport)
        is_reg_ask_sent = run_plugin_and_check_registration_ask(plugin, self.transport)

        self.assertTrue(is_reg_ask_sent)
        self.assertEqual(self.plugin_name, plugin.plugin_name)
        self.assertTrue(plugin.frames_range, [0, number_of_frames])

    def test_meta_data_load(self):
        """
        Test loading meta data file
        @return:
        """
        frame_number = 5.0
        notification = mock.MagicMock()
        meta_data_handler = MetaDataHandler(None, None, None, None, None, notification)
        meta_data_handler.load_metadata_from_file(self.meta_data_file)
        data = meta_data_handler.get_data_by_frame_number(frame_number)
        for item in data[MetaDataType.PRIMARY.value]:
            self.assertTrue(item[KEYS][FRAME_ID], frame_number)

    def test_meta_data_get_not_valid_frame_number(self):
        """
        Test getting metadata for not valid frame number
        @return:
        """
        frame_number = 5000.0
        notification = mock.MagicMock()
        meta_data_handler = MetaDataHandler(None, None, None, None, None, notification)
        meta_data_handler.load_metadata_from_file(self.meta_data_file)
        data = meta_data_handler.get_data_by_frame_number(frame_number)
        for item in data[MetaDataType.PRIMARY.value]:
            self.assertTrue(item['name'], NO_DATA_MESSAGE)
            self.assertTrue(item['id'], NO_DATA_MESSAGE)

    def test_meta_data_load_none_existing_file(self):
        """
        Test loading wrong metadata file
        @return:
        """
        notification = mock.MagicMock()
        meta_data_handler = MetaDataHandler(None, None, None, None, None, notification)
        error_message = f"{self.presence_log_file_name} not found"
        print(f"current path : {os.getcwd()}")
        meta_data_handler.load_multiple_recordings_debug_from_file(self.presence_log_file_name)
        notification.notify_error.assert_called_with(title='Metadata Handler', body=error_message)

    def test_multiple_recording_class_load_(self):
        """
        Test loading multiple recordings debug file
        @return:
        """
        data_rows = 8
        notification = mock.MagicMock()
        meta_data_handler = MetaDataHandler(None, None, None, None, None, notification)
        data = meta_data_handler.load_multiple_recordings_debug_from_file(self.multiple_recordings_debug_file)
        self.assertTrue(len(data), data_rows)

    def test_multiple_recording_class_load_none_existing_file(self):
        """
        Test loading wrong multiple recordings debug file
        @return:
        """
        notification = mock.MagicMock()
        meta_data_handler = MetaDataHandler(None, None, None, None, None, notification)
        error_message = f"{self.presence_log_file_name} not found"
        print(f"current path : {os.getcwd()}")
        meta_data_handler.load_multiple_recordings_debug_from_file(self.presence_log_file_name)
        notification.notify_error.assert_called_with(title='Metadata Handler', body=error_message)

    def test_loading_request(self):
        """
        Test loading request
        @return:
        """
        video_file = "c:\\test.mp4"
        plugin = SheldonVisionUiPlugin(self.plugin_name, self.inputs, [], self.transport)
        send_registration_ack_message(self.plugin_name, self.transport)
        sheldonUi = MainSheldonVisionUI(plugin.send_get_current_frame, plugin.get_current_frame, plugin.clear_frames_queue,
                                        plugin.send_stop_message, plugin.send_new_load_request, plugin.get_current_frame_number,
                                        plugin.send_set_frame_message, plugin.send_previous_message, plugin.send_next_frame_message,
                                        plugin.send_pause_message, plugin.send_play_message, plugin.get_recording_information_method,
                                        plugin.get_frames_range, plugin.send_log, plugin.validate_path, plugin.send_get_fps,
                                        plugin.send_set_fps, plugin.close_network, plugin.send_upload_file_to_blob,
                                        plugin.send_download_file_from_blob, plugin.send_get_files_list, plugin.files_list_on_blob, server,
                                        None, None, None, None, None)
        sheldonUi.send_new_load_request_method_callback(video_file)
        output = self.transport.get_output_message()
        self.assertTrue(output.msg_type, SheldonVisionConstants.LOAD_REQUEST_MESSAGE)
        self.assertTrue(output.msg, video_file)

    def test_stop_message(self):
        """
        Test that the stop message is sent to the plugin
        @return:
        """
        plugin = SheldonVisionUiPlugin(self.plugin_name, self.inputs, [], self.transport)
        send_registration_ack_message(self.plugin_name, self.transport)
        sheldonUi = MainSheldonVisionUI(plugin.send_get_current_frame, plugin.get_current_frame, plugin.clear_frames_queue,
                                        plugin.send_stop_message, plugin.send_new_load_request, plugin.get_current_frame_number,
                                        plugin.send_set_frame_message, plugin.send_previous_message, plugin.send_next_frame_message,
                                        plugin.send_pause_message, plugin.send_play_message, plugin.get_recording_information_method,
                                        plugin.get_frames_range, plugin.send_log, plugin.validate_path, plugin.send_get_fps,
                                        plugin.send_set_fps, plugin.close_network, plugin.send_upload_file_to_blob,
                                        plugin.send_download_file_from_blob, plugin.verify_blob_path, plugin.send_get_files_list,
                                        plugin.files_list_on_blob, plugin.verify_local_path, server, None, None, None)
        sheldonUi.send_stop_message_method_callback()
        output = self.transport.get_output_message()
        self.assertTrue(output.msg_type, SheldonVisionConstants.STOP_MESSAGE)

    def test_pause_message(self):
        """
        Test if the pause message is sent to the plugin
        @return:
        """
        plugin = SheldonVisionUiPlugin(self.plugin_name, self.inputs, [], self.transport)
        send_registration_ack_message(self.plugin_name, self.transport)
        sheldonUi = MainSheldonVisionUI(plugin.send_get_current_frame, plugin.get_current_frame, plugin.clear_frames_queue,
                                        plugin.send_stop_message, plugin.send_new_load_request, plugin.get_current_frame_number,
                                        plugin.send_set_frame_message, plugin.send_previous_message, plugin.send_next_frame_message,
                                        plugin.send_pause_message, plugin.send_play_message, plugin.get_recording_information_method,
                                        plugin.get_frames_range, plugin.send_log, plugin.validate_path, plugin.send_get_fps,
                                        plugin.send_set_fps, plugin.close_network, plugin.send_upload_file_to_blob,
                                        plugin.send_download_file_from_blob, plugin.verify_blob_path, plugin.send_get_files_list,
                                        plugin.files_list_on_blob, plugin.verify_local_path, server, None, None, None)
        sheldonUi.send_pause_message_method_callback()
        output = self.transport.get_output_message()
        self.assertTrue(output.msg_type, SheldonVisionConstants.PAUSE_MESSAGE)

    def test_set_frame_message(self):
        """
        Test that the set frame message is sent to the plugin
        @return:
        """
        frame_number = 5
        plugin = SheldonVisionUiPlugin(self.plugin_name, self.inputs, [], self.transport)
        send_registration_ack_message(self.plugin_name, self.transport)
        sheldonUi = MainSheldonVisionUI(plugin.send_get_current_frame, plugin.get_current_frame, plugin.clear_frames_queue,
                                        plugin.send_stop_message, plugin.send_new_load_request, plugin.get_current_frame_number,
                                        plugin.send_set_frame_message, plugin.send_previous_message, plugin.send_next_frame_message,
                                        plugin.send_pause_message, plugin.send_play_message, plugin.get_recording_information_method,
                                        plugin.get_frames_range, plugin.send_log, plugin.validate_path, plugin.send_get_fps,
                                        plugin.send_set_fps, plugin.close_network, plugin.send_upload_file_to_blob,
                                        plugin.send_download_file_from_blob, plugin.verify_blob_path, plugin.send_get_files_list,
                                        plugin.files_list_on_blob, plugin.verify_local_path, server, None, None, None)
        sheldonUi.send_set_frame_message_method_callback(frame_number)
        output = self.transport.get_output_message()
        self.assertTrue(output.msg_type, SheldonVisionConstants.SET_FRAME_MESSAGE)
        self.assertTrue(output.msg, str(frame_number))

    def test_get_total_frames_message(self):
        """
        Test that the total frame message is sent and stored at the plugin
        @return:
        """
        total_frames = "5000"
        self.transport.input_types = self.inputs
        plugin = SheldonVisionUiPlugin(self.plugin_name, self.inputs, [], self.transport)
        send_registration_ack_message(self.plugin_name, self.transport)

        sigmund_msg = SigmundMsg(TOTAL_VIDEO_FRAMES_MSG_NAME, DEFAULT_PLUGIN_NAME, total_frames, "")

        self.transport.send_message_to_plugin(sigmund_msg)

        send_stop_message(self.plugin_name, self.transport)
        is_reg_ask_sent = run_plugin_and_check_registration_ask(plugin, self.transport)
        self.assertTrue(is_reg_ask_sent)

        self.assertTrue(plugin.frames_range, [0, int(total_frames)])

    def test_send_camera_frame_message(self):
        """
        Test that the camera frame message is sent to the plugin
        @return:
        """
        sent_frame_number = "7"
        sent_frame_data = bytes([1, 2, 3])
        self.transport.input_types = self.inputs
        plugin = SheldonVisionUiPlugin(self.plugin_name, self.inputs, [], self.transport)
        send_registration_ack_message(self.plugin_name, self.transport)

        sigmund_msg = SigmundMsg(CAMERA_FRAMES_MESSAGE_TYPE, DEFAULT_PLUGIN_NAME, sent_frame_data, sent_frame_number)

        self.transport.send_message_to_plugin(sigmund_msg)
        send_stop_message(self.plugin_name, self.transport)
        is_reg_ask_sent = run_plugin_and_check_registration_ask(plugin, self.transport)

        self.assertTrue(is_reg_ask_sent)
        (frame_data, frame_number) = FramesQueue.get()
        self.assertTrue(sent_frame_data, frame_data)
        self.assertTrue(sent_frame_number, frame_number)

    def test_ui_output_callbacks_on_play_button(self):
        """
        Test that the ui output callbacks are called on play button
        @return:
        """
        play_click = 1
        pause_click = None
        self.transport.input_types = self.inputs
        play_button_disabled = True
        plugin = SheldonVisionUiPlugin(self.plugin_name, self.inputs, [], self.transport)
        sheldonUi = MainSheldonVisionUI(plugin.send_get_current_frame, plugin.get_current_frame, plugin.clear_frames_queue,
                                        plugin.send_stop_message, plugin.send_new_load_request, plugin.get_current_frame_number,
                                        plugin.send_set_frame_message, plugin.send_previous_message, plugin.send_next_frame_message,
                                        plugin.send_pause_message, plugin.send_play_message, plugin.get_recording_information_method,
                                        plugin.get_frames_range, plugin.send_log, plugin.validate_path, plugin.send_get_fps,
                                        plugin.send_set_fps, plugin.close_network, plugin.send_upload_file_to_blob,
                                        plugin.send_download_file_from_blob, plugin.send_get_files_list, plugin.files_list_on_blob, server,
                                        None, None, None, None, None)
        context_value.set(
            AttributeDict(**{f"{TRIGGER_INPUTS_ID}": [{f"{PROP_ID}": f"{PLAY_BUTTON_ID}{N_CLICKS_ID}", "value": "1"}]}))

        callback_output = sheldonUi.on_play_button(play_click, pause_click, None, None)
        expected_callback_output = sheldon_helpers.prepare_player_output_callbacks(pause_button_n_clicks=dash.no_update,
                                                                                   play_button_n_clicks=1,
                                                                                   play_button_is_disabled=play_button_disabled,
                                                                                   pause_button_is_disabled=not play_button_disabled,
                                                                                   slider_interval_is_disabled=not play_button_disabled,
                                                                                   forward_button_is_disabled=play_button_disabled,
                                                                                   back_button_is_disabled=play_button_disabled,
                                                                                   fast_forward_button_is_disabled=play_button_disabled)

        self.assertListEqual(callback_output, expected_callback_output)

    def test_ui_output_callbacks_on_pause_button(self):
        """
        Test that the ui output callbacks are called on pause button
        @return:
        """
        play_click = 0
        pause_click = 1
        self.transport.input_types = self.inputs
        play_button_disabled = False
        plugin = SheldonVisionUiPlugin(self.plugin_name, self.inputs, [], self.transport)
        sheldonUi = MainSheldonVisionUI(plugin.send_get_current_frame, plugin.get_current_frame, plugin.clear_frames_queue,
                                        plugin.send_stop_message, plugin.send_new_load_request, plugin.get_current_frame_number,
                                        plugin.send_set_frame_message, plugin.send_previous_message, plugin.send_next_frame_message,
                                        plugin.send_pause_message, plugin.send_play_message, plugin.get_recording_information_method,
                                        plugin.get_frames_range, plugin.send_log, plugin.validate_path, plugin.send_get_fps,
                                        plugin.send_set_fps, plugin.close_network, plugin.send_upload_file_to_blob,
                                        plugin.send_download_file_from_blob, plugin.verify_blob_path, plugin.send_get_files_list,
                                        plugin.files_list_on_blob, plugin.verify_local_path, server, None, None, None)
        context_value.set(AttributeDict(
            **{f"{TRIGGER_INPUTS_ID}": [
                {f"{PROP_ID}": f"{SheldonVisionConstants.PAUSE_BUTTON_ID}{N_CLICKS_ID}", "value": "1"}]}))

        sheldonUi.is_playing = True
        callback_output = sheldonUi.on_play_button(play_click, pause_click, None, None)
        expected_callback_output = sheldon_helpers.prepare_player_output_callbacks(
            pause_button_n_clicks=None,
            play_button_n_clicks=play_click,
            play_button_is_disabled=play_button_disabled,
            pause_button_is_disabled=not play_button_disabled,
            slider_interval_is_disabled=not play_button_disabled,
            forward_button_is_disabled=play_button_disabled,
            back_button_is_disabled=play_button_disabled,
            fast_forward_button_is_disabled=play_button_disabled
        )

        self.assertListEqual(callback_output, expected_callback_output)

    def test_close_network_request(self):
        """
        Test close network request
        @return:
        """
        plugin = SheldonVisionUiPlugin(self.plugin_name, self.inputs, [], self.transport)
        send_registration_ack_message(self.plugin_name, self.transport)
        sheldonUi = MainSheldonVisionUI(plugin.send_get_current_frame, plugin.get_current_frame, plugin.clear_frames_queue,
                                        plugin.send_stop_message, plugin.send_new_load_request, plugin.get_current_frame_number,
                                        plugin.send_set_frame_message, plugin.send_previous_message, plugin.send_next_frame_message,
                                        plugin.send_pause_message, plugin.send_play_message, plugin.get_recording_information_method,
                                        plugin.get_frames_range, plugin.send_log, plugin.validate_path, plugin.send_get_fps,
                                        plugin.send_set_fps, plugin.close_network, plugin.send_upload_file_to_blob,
                                        plugin.send_download_file_from_blob, plugin.verify_blob_path, plugin.send_get_files_list,
                                        plugin.files_list_on_blob, plugin.verify_local_path, server, None, None, None)
        sheldonUi.close_network(close_type=SigmundCloseTypeProto.Value('Hard'))
        output = self.transport.get_output_message()
        self.assertTrue(output.msg_type, SIGMUND_TYPE)
        self.assertTrue(output.msg, CLOSE_NETWORK_MSG)

    def test_multiple_metadata_files(self):
        frame_number_not_equal = 65.0
        frame_number_equal = 200.0
        notification = mock.MagicMock()
        meta_data_handler = MetaDataHandler(None, None, None, None, None, notification)
        meta_data_handler.load_metadata_from_file(self.meta_data_file)
        meta_data_handler.load_metadata_from_file(self.meta_data_file_secondary, MetaDataType.SECONDARY)
        data = meta_data_handler.get_data_by_frame_number(frame_number_not_equal)
        self.assertNotEqual(data[MetaDataType.PRIMARY.value], data[MetaDataType.SECONDARY.value])
        data = meta_data_handler.get_data_by_frame_number(frame_number_equal)
        self.assertEqual(data[MetaDataType.PRIMARY.value], data[MetaDataType.SECONDARY.value])

    @mock.patch('PluginSheldonVision.PluginSheldonVisionUiDashModule.set_app_instance')
    def test_configurations_dual_ok(self, set_app):
        json_config_path = os.path.abspath(os.path.join(self.configurations_path, 'configuration.json'))
        main_sheldon_ui = MainSheldonVisionUI(None, None, None, None, None, None, None, None, None, None, None, None, None, None, None,
                                              None, None, None, None, None, None, None, None, None, None, json_config_path, None, None)
        self.assertTrue(main_sheldon_ui.configurations.get_item(CONFIG_VIDEO_FILE_PATH))
        self.assertTrue(main_sheldon_ui.configurations.get_item(CONFIG_DEBUG_FILE_PATH))
        self.assertTrue(main_sheldon_ui.configurations.get_item(CONFIG_METADATA_FILE_PATH, CONFIG_PRIMARY_SECTION))
        self.assertTrue(main_sheldon_ui.configurations.get_item(CONFIG_LAYERS_LIST, CONFIG_PRIMARY_SECTION))
        self.assertTrue(main_sheldon_ui.configurations.get_item(CONFIG_METADATA_FILE_PATH, CONFIG_SECONDARY_SECTION))
        self.assertTrue(main_sheldon_ui.configurations.get_item(CONFIG_LAYERS_LIST, CONFIG_SECONDARY_SECTION))

    @mock.patch('PluginSheldonVision.PluginSheldonVisionUiDashModule.set_app_instance')
    def test_configurations_wrong_format(self, set_app):
        json_config_path = os.path.abspath(os.path.join(self.configurations_path, 'configuration_invalid.json'))
        main_sheldon_ui = MainSheldonVisionUI(None, None, None, None, None, None, None, None, None, None, None, None, None, None, None,
                                              None, None, None, None, None, None, None, None, None, None, json_config_path, None, None)
        self.assertFalse(main_sheldon_ui.configurations.is_ok)

    @mock.patch('PluginSheldonVision.PluginSheldonVisionUiDashModule.set_app_instance')
    def test_configurations_single(self, set_app):
        json_config_path = os.path.abspath(os.path.join(self.configurations_path, 'configuration_single.json'))
        main_sheldon_ui = MainSheldonVisionUI(None, None, None, None, None, None, None, None, None, None, None, None, None, None, None,
                                              None, None, None, None, None, None, None, None, None, None, json_config_path, None, None)
        self.assertTrue(main_sheldon_ui.configurations.get_item(CONFIG_VIDEO_FILE_PATH))
        self.assertTrue(main_sheldon_ui.configurations.get_item(CONFIG_DEBUG_FILE_PATH))
        self.assertTrue(main_sheldon_ui.configurations.get_item(CONFIG_METADATA_FILE_PATH, CONFIG_PRIMARY_SECTION))
        self.assertTrue(main_sheldon_ui.configurations.get_item(CONFIG_LAYERS_LIST, CONFIG_PRIMARY_SECTION))
        self.assertFalse(main_sheldon_ui.configurations.get_item(CONFIG_METADATA_FILE_PATH, CONFIG_SECONDARY_SECTION))
        self.assertFalse(main_sheldon_ui.configurations.get_item(CONFIG_LAYERS_LIST, CONFIG_SECONDARY_SECTION))

    @mock.patch('PluginSheldonVision.PluginSheldonVisionUiDashModule.set_app_instance')
    def test_configurations_incomplete_layer(self, set_app):
        json_config_path = os.path.abspath(os.path.join(self.configurations_path, 'configuration_incomplete_layer.json'))
        main_sheldon_ui = MainSheldonVisionUI(None, None, None, None, None, None, None, None, None, None, None, None, None, None, None,
                                              None, None, None, None, None, None, None, None, None, None, json_config_path, None, None)
        self.assertTrue(main_sheldon_ui.configurations.get_item(CONFIG_VIDEO_FILE_PATH))
        self.assertTrue(main_sheldon_ui.configurations.get_item(CONFIG_DEBUG_FILE_PATH))
        self.assertTrue(main_sheldon_ui.configurations.get_item(CONFIG_METADATA_FILE_PATH, CONFIG_PRIMARY_SECTION))
        self.assertTrue(main_sheldon_ui.configurations.get_item(CONFIG_LAYERS_LIST, CONFIG_PRIMARY_SECTION))
        self.assertTrue(main_sheldon_ui.configurations.get_item(CONFIG_METADATA_FILE_PATH, CONFIG_SECONDARY_SECTION))
        self.assertFalse(main_sheldon_ui.configurations.get_item(CONFIG_LAYERS_LIST, CONFIG_SECONDARY_SECTION))

    @mock.patch('PluginSheldonVision.PluginSheldonVisionUiDashModule.set_app_instance')
    def test_configurations_incomplete_metadata(self, set_app):
        json_config_path = os.path.abspath(os.path.join(self.configurations_path, 'configuration_incomplete_metadata.json'))
        main_sheldon_ui = MainSheldonVisionUI(None, None, None, None, None, None, None, None, None, None, None, None, None, None, None,
                                              None, None, None, None, None, None, None, None, None, None, json_config_path, None, None)
        self.assertTrue(main_sheldon_ui.configurations.get_item(CONFIG_VIDEO_FILE_PATH))
        self.assertTrue(main_sheldon_ui.configurations.get_item(CONFIG_DEBUG_FILE_PATH))
        self.assertTrue(main_sheldon_ui.configurations.get_item(CONFIG_METADATA_FILE_PATH, CONFIG_PRIMARY_SECTION))
        self.assertTrue(main_sheldon_ui.configurations.get_item(CONFIG_LAYERS_LIST, CONFIG_PRIMARY_SECTION))
        self.assertTrue(main_sheldon_ui.configurations.get_item(CONFIG_LAYERS_LIST, CONFIG_SECONDARY_SECTION))
        self.assertFalse(main_sheldon_ui.configurations.get_item(CONFIG_METADATA_FILE_PATH, CONFIG_SECONDARY_SECTION))

    @mock.patch('PluginSheldonVision.PluginSheldonVisionUiDashModule.set_app_instance')
    def test_configurations_incomplete_debug(self, set_app):
        json_config_path = os.path.abspath(os.path.join(self.configurations_path, 'configuration_incomplete_debug.json'))
        main_sheldon_ui = MainSheldonVisionUI(None, None, None, None, None, None, None, None, None, None, None, None, None, None, None,
                                              None, None, None, None, None, None, None, None, None, None, json_config_path, None, None)
        self.assertTrue(main_sheldon_ui.configurations.get_item(CONFIG_VIDEO_FILE_PATH))
        self.assertTrue(main_sheldon_ui.configurations.get_item(CONFIG_METADATA_FILE_PATH, CONFIG_PRIMARY_SECTION))
        self.assertTrue(main_sheldon_ui.configurations.get_item(CONFIG_LAYERS_LIST, CONFIG_PRIMARY_SECTION))
        self.assertTrue(main_sheldon_ui.configurations.get_item(CONFIG_METADATA_FILE_PATH, CONFIG_SECONDARY_SECTION))
        self.assertTrue(main_sheldon_ui.configurations.get_item(CONFIG_LAYERS_LIST, CONFIG_SECONDARY_SECTION))
        self.assertFalse(main_sheldon_ui.configurations.get_item(CONFIG_DEBUG_FILE_PATH))

    @mock.patch('PluginSheldonVision.PluginSheldonVisionUiDashModule.set_app_instance')
    def test_configurations_incomplete_video(self, set_app):
        json_config_path = os.path.abspath(os.path.join(self.configurations_path, 'configuration_incomplete_video.json'))
        main_sheldon_ui = MainSheldonVisionUI(None, None, None, None, None, None, None, None, None, None, None, None, None, None, None,
                                              None, None, None, None, None, None, None, None, None, None, json_config_path, None, None)
        self.assertTrue(main_sheldon_ui.configurations.get_item(CONFIG_DEBUG_FILE_PATH))
        self.assertTrue(main_sheldon_ui.configurations.get_item(CONFIG_METADATA_FILE_PATH, CONFIG_PRIMARY_SECTION))
        self.assertTrue(main_sheldon_ui.configurations.get_item(CONFIG_LAYERS_LIST, CONFIG_PRIMARY_SECTION))
        self.assertTrue(main_sheldon_ui.configurations.get_item(CONFIG_METADATA_FILE_PATH, CONFIG_SECONDARY_SECTION))
        self.assertTrue(main_sheldon_ui.configurations.get_item(CONFIG_LAYERS_LIST, CONFIG_SECONDARY_SECTION))
        self.assertFalse(main_sheldon_ui.configurations.get_item(CONFIG_VIDEO_FILE_PATH))

    @mock.patch('PluginSheldonVision.PluginSheldonVisionUiDashModule.set_app_instance')
    def test_configurations_multiple_layers(self, set_app):
        json_config_path = os.path.abspath(os.path.join(self.configurations_path, 'configuration_multiple_layers.json'))
        main_sheldon_ui = MainSheldonVisionUI(None, None, None, None, None, None, None, None, None, None, None, None, None, None, None,
                                              None, None, None, None, None, None, None, None, None, None, json_config_path, None, None)
        self.assertTrue(main_sheldon_ui.configurations.get_item(CONFIG_VIDEO_FILE_PATH))
        self.assertTrue(main_sheldon_ui.configurations.get_item(CONFIG_DEBUG_FILE_PATH))
        self.assertTrue(main_sheldon_ui.configurations.get_item(CONFIG_METADATA_FILE_PATH, CONFIG_PRIMARY_SECTION))
        self.assertTrue(main_sheldon_ui.configurations.get_item(CONFIG_LAYERS_LIST, CONFIG_PRIMARY_SECTION))
        self.assertTrue(main_sheldon_ui.configurations.get_item(CONFIG_METADATA_FILE_PATH, CONFIG_SECONDARY_SECTION))
        self.assertTrue(main_sheldon_ui.configurations.get_item(CONFIG_LAYERS_LIST, CONFIG_SECONDARY_SECTION))
        assert len(main_sheldon_ui.configurations.get_item(CONFIG_LAYERS_LIST, CONFIG_PRIMARY_SECTION)) == 1
        assert len(main_sheldon_ui.configurations.get_item(CONFIG_LAYERS_LIST, CONFIG_SECONDARY_SECTION)) == 2

    def test_get_frame_per_second(self):
        """
        Test that the get FPS send and handled
        @return:
        """
        fps = "100"
        self.transport.input_types = self.inputs
        plugin = SheldonVisionUiPlugin(self.plugin_name, self.inputs, [], self.transport)
        send_registration_ack_message(self.plugin_name, self.transport)

        sigmund_msg = SigmundMsg(FPS_STATUS_MESSAGE, DEFAULT_PLUGIN_NAME, fps, "")

        self.transport.send_message_to_plugin(sigmund_msg)

        send_stop_message(self.plugin_name, self.transport)
        is_reg_ask_sent = run_plugin_and_check_registration_ask(plugin, self.transport)
        self.assertTrue(is_reg_ask_sent)

        self.assertTrue(plugin.fps_status, fps)
        
    @mock.patch('PluginSheldonVision.PluginSheldonVisionUiDashModule.set_app_instance')
    def test_debug_add_column(self, set_app):
        browse_button_n_clicks = None
        cell = None
        add_row_n_clicks = 0
        add_column_n_clicks = 1
        input_value = 'Test Column'
        self.transport.input_types = self.inputs
        plugin = SheldonVisionUiPlugin(self.plugin_name, self.inputs, [], self.transport)
        sheldonUi = MainSheldonVisionUI(plugin.send_get_current_frame, plugin.get_current_frame, plugin.clear_frames_queue,
                                        plugin.send_stop_message, plugin.send_new_load_request, plugin.get_current_frame_number,
                                        plugin.send_set_frame_message, plugin.send_previous_message, plugin.send_next_frame_message,
                                        plugin.send_pause_message, plugin.send_play_message, plugin.get_recording_information_method,
                                        plugin.get_frames_range, plugin.send_log, plugin.validate_path, plugin.send_get_fps,
                                        plugin.send_set_fps, plugin.close_network, plugin.send_upload_file_to_blob,
                                        plugin.send_download_file_from_blob, plugin.verify_blob_path, plugin.send_get_files_list,
                                        plugin.files_list_on_blob, plugin.verify_local_path, server, None, None, None)
        sheldonUi.debug_data_frame = True
        context_value.set(AttributeDict(
            **{f"{TRIGGER_INPUTS_ID}": [
                {f"{PROP_ID}": f"{SheldonVisionConstants.DEBUG_ADD_COLUMN_BUTTON}{N_CLICKS_ID}", "value": "1"}]}))

        callback_output = sheldonUi.load_recordings_debug_data_from_file(browse_button_n_clicks, cell, add_row_n_clicks,
                                                                         add_column_n_clicks, None, None,  DEBUG_BASE_TABLE_ROWS.copy(),
                                                                         DEBUG_BASE_TABLE_COLUMNS.copy(), DEBUG_BASE_TABLE_ROWS.copy(),
                                                                         input_value, None, None)

        new_columns = DEBUG_BASE_TABLE_COLUMNS.copy()
        new_columns.append({'name': 'Test Column', 'id': 'Test Column', 'deletable': True, 'renamable': True})
        expected_callback_output = [True, False, DEBUG_BASE_TABLE_ROWS.copy(), new_columns, False, dash.no_update, dash.no_update]
        self.assertListEqual(callback_output, expected_callback_output)

    @mock.patch('PluginSheldonVision.PluginSheldonVisionUiDashModule.set_app_instance')
    def test_export_after_change(self, set_app):
        browse_button_n_clicks = None
        cell = None
        add_row_n_clicks = 0
        add_column_n_clicks = 1
        input_value = 'Test Column'
        self.transport.input_types = self.inputs
        plugin = SheldonVisionUiPlugin(self.plugin_name, self.inputs, [], self.transport)
        sheldonUi = MainSheldonVisionUI(plugin.send_get_current_frame, plugin.get_current_frame, plugin.clear_frames_queue,
                                        plugin.send_stop_message, plugin.send_new_load_request, plugin.get_current_frame_number,
                                        plugin.send_set_frame_message, plugin.send_previous_message, plugin.send_next_frame_message,
                                        plugin.send_pause_message, plugin.send_play_message, plugin.get_recording_information_method,
                                        plugin.get_frames_range, plugin.send_log, plugin.validate_path, plugin.send_get_fps,
                                        plugin.send_set_fps, plugin.close_network, plugin.send_upload_file_to_blob,
                                        plugin.send_download_file_from_blob, plugin.verify_blob_path, plugin.send_get_files_list,
                                        plugin.files_list_on_blob, plugin.verify_local_path, server, None, None, None)
        sheldonUi.debug_data_frame = True
        context_value.set(AttributeDict(
            **{f"{TRIGGER_INPUTS_ID}": [
                {f"{PROP_ID}": f"{SheldonVisionConstants.DEBUG_ADD_COLUMN_BUTTON}{N_CLICKS_ID}", "value": "1"}]}))

        callback_output = sheldonUi.load_recordings_debug_data_from_file(browse_button_n_clicks, cell, add_row_n_clicks,
                                                                         add_column_n_clicks, None, None, DEBUG_BASE_TABLE_ROWS.copy(),
                                                                         DEBUG_BASE_TABLE_COLUMNS.copy(), DEBUG_BASE_TABLE_ROWS.copy(),
                                                                         input_value, None, None)

        new_columns = DEBUG_BASE_TABLE_COLUMNS.copy()
        new_columns.append({'name': 'Test Column', 'id': 'Test Column', 'deletable': True, 'renamable': True})
        new_rows = DEBUG_BASE_TABLE_ROWS.copy()
        for indx, row in enumerate(new_rows):
            row['Test Column'] = indx

        test_file = "test_file.json"
        jump_table_after_update = []
        try:
            with mock.patch.object(MainSheldonVisionUI, "_MainSheldonVisionUI__select_file_from_dialog_box", return_value=test_file) as select_file:
                sheldonUi.export_recordings_debug_data_to_file(1, new_rows)
            notification = mock.MagicMock()
            meta_data_handler = MetaDataHandler(None, None, None, None, None, notification)
            json_file_data = meta_data_handler.load_multiple_recordings_debug_from_file(test_file)
            for multiple_recording_debug_proto in meta_data_handler._MetaDataHandler__multiple_recordings_debug_list:
                if KEYS in multiple_recording_debug_proto and multiple_recording_debug_proto[KEYS][TYPE] == DEBUG:
                    jump_table_after_update.append(multiple_recording_debug_proto[MESSAGE])
            self.assertListEqual(new_rows, jump_table_after_update)
        finally:
            if os.path.exists(test_file):
                os.remove(test_file)

    @mock.patch('PluginSheldonVision.PluginSheldonVisionUiDashModule.set_app_instance')
    def test_debug_add_column_empty(self, set_app):
        browse_button_n_clicks = None
        cell = None
        add_row_n_clicks = 0
        add_column_n_clicks = 1
        input_value = ''
        self.transport.input_types = self.inputs
        plugin = SheldonVisionUiPlugin(self.plugin_name, self.inputs, [], self.transport)
        sheldonUi = MainSheldonVisionUI(plugin.send_get_current_frame, plugin.get_current_frame, plugin.clear_frames_queue,
                                        plugin.send_stop_message, plugin.send_new_load_request, plugin.get_current_frame_number,
                                        plugin.send_set_frame_message, plugin.send_previous_message, plugin.send_next_frame_message,
                                        plugin.send_pause_message, plugin.send_play_message, plugin.get_recording_information_method,
                                        plugin.get_frames_range, plugin.send_log, plugin.validate_path, plugin.send_get_fps,
                                        plugin.send_set_fps, plugin.close_network, plugin.send_upload_file_to_blob,
                                        plugin.send_download_file_from_blob, plugin.verify_blob_path, plugin.send_get_files_list,
                                        plugin.files_list_on_blob, plugin.verify_local_path, server, None, None, None)
        sheldonUi.debug_data_frame = True
        context_value.set(AttributeDict(
            **{f"{TRIGGER_INPUTS_ID}": [
                {f"{PROP_ID}": f"{SheldonVisionConstants.DEBUG_ADD_COLUMN_BUTTON}{N_CLICKS_ID}", "value": "1"}]}))

        callback_output = sheldonUi.load_recordings_debug_data_from_file(browse_button_n_clicks, cell, add_row_n_clicks,
                                                                         add_column_n_clicks, None, None, DEBUG_BASE_TABLE_ROWS.copy(),
                                                                         DEBUG_BASE_TABLE_COLUMNS.copy(), DEBUG_BASE_TABLE_ROWS.copy(),
                                                                         input_value, None, None)

        expected_callback_output = [True, False, dash.no_update, dash.no_update, True, 'Column name cannot be empty', dash.no_update]
        self.assertListEqual(callback_output, expected_callback_output)

    @mock.patch('PluginSheldonVision.PluginSheldonVisionUiDashModule.set_app_instance')
    def test_debug_add_column_exists(self, set_app):
        browse_button_n_clicks = None
        cell = None
        add_row_n_clicks = 0
        add_column_n_clicks = 1
        input_value = 'end_frame'
        self.transport.input_types = self.inputs
        plugin = SheldonVisionUiPlugin(self.plugin_name, self.inputs, [], self.transport)
        sheldonUi = MainSheldonVisionUI(plugin.send_get_current_frame, plugin.get_current_frame, plugin.clear_frames_queue,
                                        plugin.send_stop_message, plugin.send_new_load_request, plugin.get_current_frame_number,
                                        plugin.send_set_frame_message, plugin.send_previous_message, plugin.send_next_frame_message,
                                        plugin.send_pause_message, plugin.send_play_message, plugin.get_recording_information_method,
                                        plugin.get_frames_range, plugin.send_log, plugin.validate_path, plugin.send_get_fps,
                                        plugin.send_set_fps, plugin.close_network, plugin.send_upload_file_to_blob,
                                        plugin.send_download_file_from_blob, plugin.verify_blob_path, plugin.send_get_files_list,
                                        plugin.files_list_on_blob, plugin.verify_local_path, server, None, None, None)
        sheldonUi.debug_data_frame = True
        context_value.set(AttributeDict(
            **{f"{TRIGGER_INPUTS_ID}": [
                {f"{PROP_ID}": f"{SheldonVisionConstants.DEBUG_ADD_COLUMN_BUTTON}{N_CLICKS_ID}", "value": "1"}]}))

        callback_output = sheldonUi.load_recordings_debug_data_from_file(browse_button_n_clicks, cell, add_row_n_clicks,
                                                                         add_column_n_clicks, None, None, DEBUG_BASE_TABLE_ROWS.copy(),
                                                                         DEBUG_BASE_TABLE_COLUMNS.copy(), DEBUG_BASE_TABLE_ROWS.copy(),
                                                                         input_value, None, None)

        expected_callback_output = [True, False, dash.no_update, dash.no_update, True, f'Column already exists: {input_value}', dash.no_update]
        self.assertListEqual(callback_output, expected_callback_output)

    @mock.patch('PluginSheldonVision.PluginSheldonVisionUiDashModule.set_app_instance')
    def test_debug_add_rows(self, set_app):
        browse_button_n_clicks = None
        cell = None
        add_row_n_clicks = 1
        add_column_n_clicks = 0
        input_value = ''
        self.transport.input_types = self.inputs
        plugin = SheldonVisionUiPlugin(self.plugin_name, self.inputs, [], self.transport)
        sheldonUi = MainSheldonVisionUI(plugin.send_get_current_frame, plugin.get_current_frame, plugin.clear_frames_queue,
                                        plugin.send_stop_message, plugin.send_new_load_request, plugin.get_current_frame_number,
                                        plugin.send_set_frame_message, plugin.send_previous_message, plugin.send_next_frame_message,
                                        plugin.send_pause_message, plugin.send_play_message, plugin.get_recording_information_method,
                                        plugin.get_frames_range, plugin.send_log, plugin.validate_path, plugin.send_get_fps,
                                        plugin.send_set_fps, plugin.close_network, plugin.send_upload_file_to_blob,
                                        plugin.send_download_file_from_blob, plugin.verify_blob_path, plugin.send_get_files_list,
                                        plugin.files_list_on_blob, plugin.verify_local_path, server, None, None, None)
        sheldonUi.debug_data_frame = True
        context_value.set(AttributeDict(
            **{f"{TRIGGER_INPUTS_ID}": [
                {f"{PROP_ID}": f"{SheldonVisionConstants.DEBUG_ADD_ROW_BUTTON}{N_CLICKS_ID}", "value": "1"}]}))

        callback_output = sheldonUi.load_recordings_debug_data_from_file(browse_button_n_clicks, cell, add_row_n_clicks,
                                                                         add_column_n_clicks, None, None, DEBUG_BASE_TABLE_ROWS.copy(),
                                                                         DEBUG_BASE_TABLE_COLUMNS.copy(), DEBUG_BASE_TABLE_ROWS.copy(),
                                                                         input_value, None, None)

        new_rows = DEBUG_BASE_TABLE_ROWS.copy()
        new_rows.append({"IsChecked": '', "Video Location": "", "Frame Number": '', "end_frame": ''})
        expected_callback_output = [True, False, new_rows, DEBUG_BASE_TABLE_COLUMNS.copy(), False, dash.no_update, dash.no_update]
        self.assertListEqual(callback_output, expected_callback_output)
