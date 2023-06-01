import argparse
import sys
import os
import re
import traceback
import webbrowser
from threading import Thread, Event, Timer
from PyPluginBase.SigmundPluginBase import SigmundPluginBase
from PyPluginBase.Transport import ISigmundTransport
from PyPluginBase.ProtosParser import ProtosParser
from flask import Flask, Response, request
from plotly.graph_objs import Figure
from queue import Queue
from winreg import HKEY_CURRENT_USER, QueryValueEx, OpenKey

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from PluginSheldonVision.Constants import NO_FRAME_SELECTED, CAMERA_FRAMES_MESSAGE_TYPE, TOTAL_VIDEO_FRAMES_MSG_NAME, \
    PATH_STATUS_MSG, GET_TOTAL_VIDEO_FRAMES_MSG_NAME, PLAY_MESSAGE, SET_FRAME_MESSAGE, PAUSE_MESSAGE, PREVIOUS_FRAME_MESSAGE, \
    NEXT_FRAME_MESSAGE, STOP_MESSAGE, LOAD_REQUEST_MESSAGE, GET_CURRENT_FRAME_MESSAGE, SET_FRAME_PER_SECOND, GET_FRAME_PER_SECOND, \
    FPS_STATUS_MESSAGE, FINISH_UPLOAD_FILE_MSG_TYPE, FINISH_DOWNLOAD_FILE_MSG_TYPE, AZURE_BLOB_MSG_TYPE, AZURE_BLOB_MSG_DOWNLOAD_TYPE, \
    FILES_LIST_IN_BLOB_REQUEST, FILES_LIST_IN_BLOB_RESPONSE
from PluginSheldonVision.PluginSheldonVisionUiDashModule import *
from SheldonCommon.Constants import EMPTY_STRING, TIMEOUT_BEFORE_OPEN_SHELDON_TAB_IN_SEC
from SigmundProtobufPy.AzureBlobProto_pb2 import AzureBlobUploadProto, AzureBlobUploadStatusEnum, AzureBlobDownloadProto, \
    AzureBlobDownloadStatusEnum

server = Flask(__name__)
FramesQueue = Queue()
e_frame_paused_md = {
    MetaDataType.PRIMARY: Event(),
    MetaDataType.SECONDARY: Event()
}
current_frame_number: int | None = None
current_frame = None


def get_frames_from_queue(meta_data_type: MetaDataType = MetaDataType.PRIMARY):
    global current_frame_number
    global current_frame
    while True:
        try:
            e_frame_paused_md[meta_data_type].wait()
            e_frame_paused_md[meta_data_type].clear()
            if meta_data_type == MetaDataType.PRIMARY:
                current_frame, current_frame_number = FramesQueue.get()

            if not current_frame:
                e_frame_paused_md[meta_data_type].clear()
                continue
            current_frame_with_layers = main_sheldonUi.create_online_graph(current_frame,
                                                                           current_frame_number,
                                                                           meta_data_type)
            if type(current_frame_with_layers) is Figure:
                e_frame_paused_md[meta_data_type].clear()
                continue
            try:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + current_frame_with_layers + b'\r\n\r\n')
            except GeneratorExit:
                # This may happen while the loop is running no component available for update.
                # For example, on page refresh
                return
            else:
                continue
        except:
            traceback_string = traceback.format_exc()
            main_sheldonUi.notifications.notify_error(title='Get Frames From Queue',
                                                      body="An exception raised during reading queue, see logs for more details")
            main_sheldonUi.log_method(logging.ERROR, traceback_string)
            get_frames_from_queue()

def clear_frames_queue(clear_queue_only: bool = False):
    global current_frame_number
    global current_frame
    with FramesQueue.mutex:
        if not clear_queue_only:
            current_frame_number = 0
            current_frame = None
        FramesQueue.queue.clear()


@server.route('/video_feed_primary')
def video_feed():
    return Response(get_frames_from_queue(MetaDataType.PRIMARY),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@server.route('/video_feed_secondary')
def video_feed_secondary():
    return Response(get_frames_from_queue(MetaDataType.SECONDARY),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@server.route('/autorun_from_mail')
def autorun_from_mail():
    video_path = request.args.get('video_path')
    primary_metadata = request.args.get('metadata_primary')
    secondary_metadata = request.args.get('metadata_secondary')
    frame_number = int(request.args.get('frame_number'))
    return Response(main_sheldonUi.handle_autorun_from_mail(video_path, primary_metadata, secondary_metadata, frame_number))


@server.route('/load_jump')
def load_jump():
    jump_path = request.args.get('jump_path')
    return Response(main_sheldonUi.handle_load_jump_http(jump_path))


def store_data(msg, frame_number):
    FramesQueue.put((msg, frame_number))


class SheldonVisionUiPlugin(SigmundPluginBase):
    def __init__(self, plugin_name, input_types, output_types, sigmund_transport: ISigmundTransport = None):
        SigmundPluginBase.__init__(self, plugin_name, input_types, output_types, sigmund_transport=sigmund_transport)
        self.query_cycle_range = None
        self.frames_range = NO_FRAME_SELECTED
        self._proto_parser = ProtosParser()
        self.frames_range_received = Event()
        self.frame_received = Event()
        self.path_check_received = Event()
        self.frame_per_second_received = Event()
        self.finish_upload_received = Event()
        self.finish_download_received = Event()
        self.get_files_list_blob = Event()
        self.recording_information = None
        self.reload_application_callback = None
        self.path_status = None
        self.fps_status = None
        self.files_on_blob = []

    def plugin_logic(self):
        message = self.get_next_message()
        try:
            if message.msg_type == TOTAL_VIDEO_FRAMES_MSG_NAME:
                if message.get_string_message():
                    total_frames_strings = message.get_string_message()
                    self.frames_range = [0, int(total_frames_strings)]
                self.frames_range_received.set()
            if message.msg_type == CAMERA_FRAMES_MESSAGE_TYPE:
                store_data(message.msg, int(message.msg_metadata))
                self.frame_received.set()
                for event in e_frame_paused_md.values():
                    event.set()
            if message.msg_type == PATH_STATUS_MSG:
                self.path_status = message.get_string_message()
                self.path_check_received.set()
            if message.msg_type == FPS_STATUS_MESSAGE:
                self.fps_status = int(message.get_string_message())
                self.frame_per_second_received.set()
            if message.msg_type == FINISH_UPLOAD_FILE_MSG_TYPE:
                self.finish_upload_received.set()
            if message.msg_type == FINISH_DOWNLOAD_FILE_MSG_TYPE:
                self.finish_download_received.set()
            if message.msg_type == AZURE_BLOB_MSG_TYPE:
                self.on_error_azure_received(message.msg, AzureBlobUploadProto)
            if message.msg_type == AZURE_BLOB_MSG_DOWNLOAD_TYPE:
                self.on_error_azure_received(message.msg, AzureBlobDownloadProto)
            if message.msg_type == FILES_LIST_IN_BLOB_RESPONSE:
                self.get_files_list_on_blob(message.msg)
                self.get_files_list_blob.set()
        except:
            traceback_string = traceback.format_exc()
            self.send_log(logging.ERROR, traceback_string)
            main_sheldonUi.notifications.notify_error(title='Plugin Logic',
                                                      body=f'An exception raised on plugin logic, see logs for more details')

    def get_files_list_on_blob(self, files_list):
        self.files_on_blob = [x.decode("utf-8") for x in files_list.split()]

    def files_list_on_blob(self):
        return self.files_on_blob

    def verify_blob_path(self, file_path_base: str) -> str:
        is_complete_url = SheldonVisionConstants.BLOB_IDENTIFIER in file_path_base
        if is_complete_url:
            metadata_file_no_storage = file_path_base.split(SheldonVisionConstants.BLOB_IDENTIFIER)[1]
            file_path = '/'.join(metadata_file_no_storage.split('/')[2:])
        else:
            file_path = file_path_base
        return file_path

    def verify_local_path(self, file_path: str, notify_error: bool = True, base_path: str = '') -> str:
        local_re = r'^[a-zA-Z]:\\|^\\{2}\S*\\'
        file_path = os.path.normpath(file_path)
        file_path_with_base_path = os.path.join(base_path, file_path) if base_path else base_path
        if not re.match(local_re, file_path) and not re.match(local_re, file_path_with_base_path):
            return ''
        if not os.path.exists(file_path) and not os.path.exists(file_path_with_base_path) and notify_error:
            main_sheldonUi.notifications.notify_error(title='Sheldon Vision', body=f'Path not found - {file_path}')
        return file_path_with_base_path if os.path.exists(file_path_with_base_path) else file_path if os.path.exists(file_path) else None

    def validate_path(self):
        self.path_check_received.wait()
        self.path_check_received.clear()
        return self.path_status == SheldonVisionConstants.PathStatus.Valid.value

    def get_recording_information_method(self):
        return self.recording_information

    def get_frames_range(self):
        self.frames_range_received.clear()
        self.__send_get_frames_range()
        self.frames_range_received.wait()

        return self.frames_range

    def send_get_files_list(self, blob_path):
        self.files_on_blob = []
        self.get_files_list_blob.clear()
        self.send_message(FILES_LIST_IN_BLOB_REQUEST, blob_path)
        self.get_files_list_blob.wait()

    def send_play_message(self):
        self.send_message(PLAY_MESSAGE, EMPTY_STRING)

    def send_next_frame_message(self):
        self.send_message(NEXT_FRAME_MESSAGE, EMPTY_STRING)

    def send_previous_message(self):
        self.send_message(PREVIOUS_FRAME_MESSAGE, EMPTY_STRING)

    def send_pause_message(self):
        for event in e_frame_paused_md.values():
            event.clear()
        self.send_message(PAUSE_MESSAGE, EMPTY_STRING)

    def send_set_frame_message(self, frame_number):
        for event in e_frame_paused_md.values():
            event.set()
        self.send_message(SET_FRAME_MESSAGE, str(frame_number))

    def send_stop_message(self):
        self.send_message(STOP_MESSAGE, EMPTY_STRING)

    def get_current_frame_number(self) -> int | None:
        return current_frame_number

    def send_new_load_request(self, file_path):
        self.send_message(LOAD_REQUEST_MESSAGE, file_path)
        self.path_status = None

    def __send_get_frames_range(self):
        self.send_message(GET_TOTAL_VIDEO_FRAMES_MSG_NAME, EMPTY_STRING)

    def send_get_current_frame(self):
        self.frame_received.clear()
        self.send_message(GET_CURRENT_FRAME_MESSAGE, EMPTY_STRING)
        self.frame_received.wait()

    def clear_frames_queue(self, clear_queue_only: bool = False):
        return clear_frames_queue(clear_queue_only)

    def get_current_frame(self):
        return current_frame

    def send_get_fps(self):
        self.frame_per_second_received.clear()
        self.send_message(GET_FRAME_PER_SECOND, EMPTY_STRING)
        self.frame_per_second_received.wait()

        return self.fps_status

    def send_set_fps(self, fps):
        self.send_message(SET_FRAME_PER_SECOND, str(fps))

    def send_upload_file_to_blob(self, file_path: str, destination_path: str) -> str:
        self.finish_upload_received.clear()
        azure_proto = AzureBlobUploadProto()
        azure_proto.DestinationFolderPath = destination_path
        azure_proto.Command = AzureBlobUploadStatusEnum.StartUpload
        azure_proto.SourceFilePath.append(file_path)
        self.send_message(AZURE_BLOB_MSG_TYPE, azure_proto.SerializeToString())
        self.finish_upload_received.wait()
        return f'{SheldonVisionConstants.SHELDON_VISION_BLOB_URL}/{SheldonVisionConstants.BLOB_CONTAINER_NAME}/{destination_path}/' \
               f'{os.path.basename(file_path)}'

    def send_download_file_from_blob(self, file_path: str, destination_path: str, timeout_seconds: float = 30) -> str:
        self.finish_download_received.clear()
        azure_proto = AzureBlobDownloadProto()
        azure_proto.DestinationFolderPath = destination_path
        azure_proto.Command = AzureBlobDownloadStatusEnum.StartDownload
        azure_proto.SourceFilePath.append(file_path)
        self.send_message(AZURE_BLOB_MSG_DOWNLOAD_TYPE, azure_proto.SerializeToString())
        self.finish_download_received.wait(timeout=timeout_seconds)
        if not self.finish_download_received.is_set():
            error_message = f'Failed to download from blob, check given path - {file_path}'
            main_sheldonUi.notifications.notify_error(title='Download From Blob', body=error_message)
            return ''
        return os.path.abspath(os.path.join(destination_path, os.path.basename(file_path)))

    def on_error_azure_received(self, message, proto: AzureBlobUploadProto | AzureBlobDownloadProto):
        error = message
        azure_proto_error_msg = proto()
        azure_proto_error_msg.ParseFromString(error)
        error_msg = azure_proto_error_msg.ErrorMsg
        if error_msg != "":
            self.send_log(logging.ERROR, error_msg)
            if SheldonVisionConstants.AZURE_SAS_ERROR in error_msg:
                main_sheldonUi.notifications.notify_error(title='Azure SAS Error', body="SAS token is invalid, please generate a new one")
            else:
                main_sheldonUi.notifications.notify_error(title='Azure Error', body="An exception raised from azure, see logs for more details")


def parse_args(args=None):
    parser = argparse.ArgumentParser(description='SheldonVisionUI Plugin arguments')
    parser.add_argument('-n', '--name', default='SheldonVisionUiPlugin', help='Plugin name')
    parser.add_argument('-i', '--input_types_str', default='', help="Input types with ',' separator")
    parser.add_argument('-o', '--output_types_str', default='', help="Output types with ',' separator")
    parser.add_argument('-c', '--config_file', default='', help="Configuration JSON file to load Video, MetaData files and Debug file")
    parser.add_argument('--storage_account_name', default='', help="Azure Blob storage account name")
    parser.add_argument('--container_name', default='', help="Azure Blob container name")

    args = parser.parse_args(args)
    return args


def get_default_browser():
    with OpenKey(HKEY_CURRENT_USER,
                 r"Software\\Microsoft\\Windows\\Shell\\Associations\\UrlAssociations\\http\\UserChoice") as key:
        browser = QueryValueEx(key, 'Progid')[0]
        return browser


def open_browser():
    webbrowser.open_new(SheldonVisionConstants.SHELDON_VISION_URL)


def start_new_ui(plugin: SheldonVisionUiPlugin, configuration: str, storage_account_name: str, container_name: str) -> MainSheldonVisionUI:
    global server
    # Create new UI.
    sheldonUi = MainSheldonVisionUI(plugin.send_get_current_frame, plugin.get_current_frame, plugin.clear_frames_queue,
                                    plugin.send_stop_message, plugin.send_new_load_request, plugin.get_current_frame_number,
                                    plugin.send_set_frame_message, plugin.send_previous_message, plugin.send_next_frame_message,
                                    plugin.send_pause_message, plugin.send_play_message, plugin.get_recording_information_method,
                                    plugin.get_frames_range, plugin.send_log, plugin.validate_path, plugin.send_get_fps,
                                    plugin.send_set_fps, plugin.close_network, plugin.send_upload_file_to_blob,
                                    plugin.send_download_file_from_blob, plugin.verify_blob_path, plugin.send_get_files_list,
                                    plugin.files_list_on_blob, plugin.verify_local_path, server, configuration, storage_account_name,
                                    container_name)

    # Start UI.
    sheldonUi.start_ui()
    return sheldonUi


if __name__ == '__main__':
    try:
        parsed_args = parse_args(sys.argv[1:])
        input_types_list = parsed_args.input_types_str.split(",")
        output_types_list = parsed_args.output_types_str.split(",")
        input_types_list.append(CAMERA_FRAMES_MESSAGE_TYPE)
        input_types_list.append(TOTAL_VIDEO_FRAMES_MSG_NAME)
        input_types_list.append(PATH_STATUS_MSG)
        input_types_list.append(FPS_STATUS_MESSAGE)
        input_types_list.append(FINISH_UPLOAD_FILE_MSG_TYPE)
        input_types_list.append(FINISH_DOWNLOAD_FILE_MSG_TYPE)
        input_types_list.append(AZURE_BLOB_MSG_TYPE)
        input_types_list.append(AZURE_BLOB_MSG_DOWNLOAD_TYPE)
        input_types_list.append(FILES_LIST_IN_BLOB_RESPONSE)
        input_types_list.pop(0)
        configurations = parsed_args.config_file
        storage_account_name = parsed_args.storage_account_name
        container_name = parsed_args.container_name
        if storage_account_name == '':
            storage_account_name = "presencecv0851576016"
        if container_name == '':
            container_name = "dev-data"

        plugin = SheldonVisionUiPlugin(parsed_args.name, input_types_list, output_types_list)
        # Run plugin in thread
        thread = Thread(target=plugin.start_plugin, daemon=True)
        thread.start()

        Timer(TIMEOUT_BEFORE_OPEN_SHELDON_TAB_IN_SEC, open_browser).start()

        main_sheldonUi = start_new_ui(plugin, configurations, storage_account_name, container_name)
        run_server()

    except:
        traceback_string = traceback.format_exc()
        logging.error(traceback_string)
        main_sheldonUi.notifications.notify_error(title='SheldonVision',
                                                  body='An exception raised on main function, see logs for more details')

