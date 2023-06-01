import glob
import os
import re
import time
import traceback
import pandas as pd
from pathlib import Path
import json
import logging
from enum import Enum
from typing import TypedDict, Tuple
from PluginSheldonVision import Helpers
from SheldonCommon.Constants import EMPTY_STRING
from PluginSheldonVision.ConfigurationHandler import ConfigurationHandler
from PluginSheldonVision.NotificationsHandler import Notification

pd.options.mode.chained_assignment = None  # Disable output of pandas warnings

settings = ConfigurationHandler(os.path.abspath(os.path.join(__file__, '..', 'settings.json')), perform_validation=False)
METADATA_SECTION = 'Metadata'
GENERAL_SECTION = 'General'

IS_CHECKED_ID = settings.get_item('IS_CHECKED_ID', METADATA_SECTION)
COLUMN_ID = settings.get_item('COLUMN_ID', METADATA_SECTION)
ROW = settings.get_item('ROW', METADATA_SECTION)
FRAME_ID = settings.get_item('FRAME_ID', METADATA_SECTION)
KEYS = settings.get_item('KEYS', METADATA_SECTION)
VIDEO_LOCATION = settings.get_item('VIDEO_LOCATION', METADATA_SECTION)
FRAME_NUMBER = settings.get_item('FRAME_NUMBER', METADATA_SECTION)
TYPE = settings.get_item('TYPE', METADATA_SECTION)
MESSAGE = settings.get_item('MESSAGE', METADATA_SECTION)
DEBUG = settings.get_item('DEBUG', METADATA_SECTION)
HEADER = settings.get_item('HEADER', METADATA_SECTION)
PRIMARY_METADATA = settings.get_item('PRIMARY_METADATA', METADATA_SECTION)
SECONDARY_METADATA = settings.get_item('SECONDARY_METADATA', METADATA_SECTION)
PRIMARY_METADATA_TITLE = settings.get_item('PRIMARY_METADATA_TITLE', METADATA_SECTION)
SECONDARY_METADATA_TITLE = settings.get_item('SECONDARY_METADATA_TITLE', METADATA_SECTION)
END_FRAME = settings.get_item('END_FRAME', METADATA_SECTION)
PRIMARY_REPORT = settings.get_item('PRIMARY_REPORT', METADATA_SECTION)
SECONDARY_REPORT = settings.get_item('SECONDARY_REPORT', METADATA_SECTION)
LOGS_PATH = settings.get_item('LOGS_PATH', METADATA_SECTION)
LOG_FILE_NAME = settings.get_item('LOG_FILE_NAME', METADATA_SECTION)
PRIMARY_LOG_PATH = settings.get_item('PRIMARY_LOG_PATH', METADATA_SECTION)
SECONDARY_LOG_PATH = settings.get_item('SECONDARY_LOG_PATH', METADATA_SECTION)
VIDEO_LOCATION_SECTION = settings.get_item('VIDEO_LOCATION_SECTION', METADATA_SECTION)
VIDEO_PATH = settings.get_item('VIDEO_PATH', METADATA_SECTION)
VIDEO_SUFFIX = settings.get_item('VIDEO_SUFFIX', METADATA_SECTION)

PRIMARY_META_DATA_PATH = settings.get_item('PRIMARY_META_DATA_PATH', GENERAL_SECTION) #TODO: Take that from config file
PRIMARY_METADATA_LOG_NAME = settings.get_item('PRIMARY_METADATA_LOG_NAME', GENERAL_SECTION) #TODO: Take that from config file

SECONDARY_META_DATA_PATH = settings.get_item('SECONDARY_META_DATA_PATH', GENERAL_SECTION) #TODO: Take that from config file
SECONDARY_METADATA_LOG_NAME = settings.get_item('SECONDARY_METADATA_LOG_NAME', GENERAL_SECTION) #TODO: Take that from config file


CHECKED_ICON = '✅'
UNCHECKED_ICON = '⬜'
dictionary_keys = {KEYS: {TYPE: DEBUG}}
NO_DATA_MESSAGE = "No Data available for this frame number"
JSON_EXTENSION = ".json"

METADATA = 'metadata'
FILENAME = 'filename'
DECIMATION = 'decimation'


def convert_icon_to_bool(icon):
    """
    Converts icon to a boolean value.
    @param icon:
    @return:
    """
    if icon == CHECKED_ICON:
        return 'True'
    elif icon == UNCHECKED_ICON:
        return 'False'
    else:
        logging.error(f"Icon {icon} is not a valid icon")
        return 'False'


def is_checked_modify_value(cell, data):
    if cell is None:
        return None
    else:
        row_selected = cell[ROW]
        column_name = cell[COLUMN_ID]

        if column_name != IS_CHECKED_ID:
            return None

        if data[row_selected][column_name] == CHECKED_ICON:
            data[row_selected][column_name] = UNCHECKED_ICON

        elif data[row_selected][column_name] == UNCHECKED_ICON or data[row_selected][column_name] == EMPTY_STRING:
            data[row_selected][column_name] = CHECKED_ICON

        return data


class MetaDataType(Enum):
    PRIMARY = 'Primary'
    SECONDARY = 'Secondary'


class MetaDataStruct(TypedDict):
    metadata: dict
    filename: str
    decimation: list


class MetaDataHandler:
    def __init__(self, verify_blob_path, get_blob_files, files_list_on_blob, verify_local_path, download_file_from_blob,
                 notifications: Notification):
        self.__meta_data_list = []
        self.__metadata: dict[MetaDataType.value, MetaDataStruct] = {
            MetaDataType.PRIMARY.value: {METADATA: {}, HEADER: {}, FILENAME: None, DECIMATION: False},
            MetaDataType.SECONDARY.value: {METADATA: {}, HEADER: {}, FILENAME: None, DECIMATION: False}
        }

        self.__multiple_recordings_debug_list = []
        self.__multiple_recordings_debug = pd.DataFrame()
        self.__multiple_recordings_debug_header = {}
        self.__current_decimation_index: int | None = None
        self.loading_metadata = False
        self.verify_blob_path = verify_blob_path
        self.verify_local_path = verify_local_path
        self.get_blob_files = get_blob_files
        self.files_list_on_blob = files_list_on_blob
        self.download_file_from_blob = download_file_from_blob
        self.find_metadata_file = False
        self.notifications = notifications

    @property
    def has_header(self):
        return self.__multiple_recordings_debug_header != {}

    @property
    def is_metadata_file_loaded(self):
        loaded_files = [f for f in self.__metadata.values() if f[FILENAME] is not None]
        return len(loaded_files) > 0

    @property
    def is_jump_file_loaded(self):
        return not self.__multiple_recordings_debug.empty

    def get_header(self, meta_data_type):
        return self.__metadata[meta_data_type.value][HEADER]

    def get_video_path(self) -> str | None:
        if self.has_header:
            if VIDEO_LOCATION_SECTION in self.__multiple_recordings_debug_header:
                return self.__multiple_recordings_debug_header[VIDEO_LOCATION_SECTION][VIDEO_PATH]
        return None

    def get_video_suffix(self) -> str | None:
        if self.has_header:
            if VIDEO_LOCATION_SECTION in self.__multiple_recordings_debug_header:
                return self.__multiple_recordings_debug_header[VIDEO_LOCATION_SECTION][VIDEO_SUFFIX]
        return None

    def get_metadata_properties(self, report_type: str = None) -> Tuple[str | None, str | None]:
        if self.has_header and report_type and report_type in self.__multiple_recordings_debug_header:
            log_base_path = self.__multiple_recordings_debug_header[report_type][LOGS_PATH]
            log_file_name = self.__multiple_recordings_debug_header[report_type][LOG_FILE_NAME]
            return log_base_path, log_file_name
        return None, None

    def get_clip_resolution(self, width, height, meta_data_type):
        header = self.get_header(meta_data_type)
        if len(header) > 0:
            if 'frames_size_raw' in header[HEADER].keys():
                if self.assert_difference_in_metadata_resolutions():
                    raise Exception("Metadata resolutions are different")
                return header[HEADER]['frames_size_raw'][0], header[HEADER]['frames_size_raw'][1], True
            return width, height, True
        return width, height, False

    def assert_difference_in_metadata_resolutions(self):
        header1 = self.get_header(MetaDataType.PRIMARY)
        header2 = self.get_header(MetaDataType.SECONDARY)
        if len(header1) > 0 and len(header2) > 0:
            if 'frames_size_raw' in header1[HEADER].keys() and 'frames_size_raw' in header2[HEADER].keys():
                if header1[HEADER]['frames_size_raw'][0] != header2[HEADER]['frames_size_raw'][0] or header1[HEADER]['frames_size_raw'][1] != header2[HEADER]['frames_size_raw'][1]:
                    return True
        return False

    @property
    def is_decimated_metadata(self) -> bool:
        """
        Indicate if there is metadata file the is decimated
        :return:
        """
        decimated_files = [f for f in self.__metadata.values() if f[DECIMATION]]
        return len(decimated_files) > 0

    def get_decimation_value(self, frame_number: int, is_next_frame: bool) -> int | None:
        primary_metadata_indices = self.__metadata[MetaDataType.PRIMARY.value][DECIMATION]

        # Get the next metadata frame
        if is_next_frame:
            if frame_number >= max(primary_metadata_indices):
                return max(primary_metadata_indices)

            condition = lambda next_value: frame_number < next_value
            self.__current_decimation_index = Helpers.get_index_from_list_by_condition(condition,
                                                                                       primary_metadata_indices,
                                                                                       is_reversed=False)

        # Get the previous metadata frame
        else:
            if frame_number == 0:
                return 0

            condition = lambda prev_value: frame_number > prev_value
            self.__current_decimation_index = Helpers.get_index_from_list_by_condition(condition,
                                                                                       primary_metadata_indices,
                                                                                       is_reversed=True)
        if self.__current_decimation_index == -1:
            self.notifications.notify_error(title='Decimation Error',
                                            body="Decimation logic found next index is -1")

        return self.__current_decimation_index

    def get_data_by_frame_number(self, frame_number: float):
        no_data = [{"name": NO_DATA_MESSAGE,
                    "id": NO_DATA_MESSAGE}]
        data = {
            MetaDataType.PRIMARY.value: no_data,
            MetaDataType.SECONDARY.value: no_data
        }

        for data_type in MetaDataType:
            if frame_number in self.__metadata[data_type.value][METADATA]:
                data[data_type.value] = self.__metadata[data_type.value][METADATA][frame_number]

        return data

    def get_data_for_whole_clip(self, data_type: MetaDataType):
        return self.__metadata[data_type.value][METADATA]

    def get_total_frames_from_data(self, meta_data_type: MetaDataType = MetaDataType.PRIMARY):
        return len(self.__metadata[meta_data_type.value][METADATA])

    def load_metadata_file(self, file_name: str, meta_data_type: MetaDataType = MetaDataType.PRIMARY):
        if not file_name:
            error_message = f'No {meta_data_type.value} metadata file was given'
            logging.error(error_message)
            self.notifications.notify_error(title='Metadata Handler', body=error_message)
            return
        local_path = file_name if self.is_file_exist(file_name, notify_error=False) else \
            self.download_file_from_blob(file_name, meta_data_type) #TODO: Check if file is local or not and don't assume automatically that need to go to blob
        if not local_path:
            return
        self.load_metadata_from_file(local_path, meta_data_type)
        return local_path

    def load_metadata_from_file(self, file_name: str, meta_data_type: MetaDataType = MetaDataType.PRIMARY) -> list | None:
        self.loading_metadata = True
        self.__metadata[meta_data_type.value][METADATA].clear()
        self.__meta_data_list.clear()
        if not self.is_file_exist(file_name):
            return

        error_counter = self.__read_and_parse_json_file(file_name, self.__meta_data_list, 'metadata')
        self.__create_metadata_by_frame_id(meta_data_type)
        self.__metadata[meta_data_type.value][FILENAME] = file_name
        self.__metadata[meta_data_type.value][DECIMATION] = list(self.__metadata[meta_data_type.value][METADATA].keys())
        if error_counter == 0:
            self.notifications.notify_info('SheldonVision', f'{meta_data_type.value} metadata file loaded successfully')
        else:
            self.notifications.notify_warning('SheldonVision',
                                              f'{meta_data_type.value} metadata file loaded successfully but some issues detected')
        self.loading_metadata = False

    def __create_metadata_by_frame_id(self, meta_data_type: MetaDataType = MetaDataType.PRIMARY):
        for frame_id_with_meta_data_proto in self.__meta_data_list:
            if HEADER in frame_id_with_meta_data_proto:
                self.__metadata[meta_data_type.value][HEADER] = frame_id_with_meta_data_proto
                continue
            if int(frame_id_with_meta_data_proto[KEYS][FRAME_ID]) in self.__metadata[meta_data_type.value][METADATA]:
                self.__metadata[meta_data_type.value][METADATA][int(frame_id_with_meta_data_proto[KEYS][FRAME_ID])].append(
                    frame_id_with_meta_data_proto)
            else:
                self.__metadata[meta_data_type.value][METADATA][int(frame_id_with_meta_data_proto[KEYS][FRAME_ID])] = \
                    [frame_id_with_meta_data_proto]

    def get_metadata_filename(self, metadata_type: MetaDataType) -> str | None:
        """
        Gets the file path f a specific metadata file
        :param metadata_type: the metadata type name
        :return: File path if exists else None
        """
        return self.__metadata[metadata_type][FILENAME]

    def load_multiple_recordings_debug_file(self, file_name: str, meta_data_type: MetaDataType = MetaDataType.PRIMARY):
        if not file_name:
            error_message = f'No jump file was given'
            logging.error(error_message)
            self.notifications.notify_error(title='Metadata Handler', body=error_message)
            return
        base_path = PRIMARY_META_DATA_PATH if meta_data_type == MetaDataType.PRIMARY else SECONDARY_META_DATA_PATH ##TODO: Why do we need it??
        if self.verify_local_path(file_name, notify_error=False, base_path=base_path):
            file_name = os.path.normpath(file_name)
            local_path = file_name if self.is_file_exist(file_name, notify_error=False) else ''
        else:
            local_path = self.download_file_from_blob(file_name, meta_data_type, 5)
        if not local_path:
            error_message = f'Failed to get jump file - {file_name}'
            logging.error(error_message)
            self.notifications.notify_error(title='Metadata Handler', body=error_message)
            return
        return self.load_multiple_recordings_debug_from_file(local_path)

    def load_multiple_recordings_debug_from_file(self, file_name):
        self.__multiple_recordings_debug_list.clear()
        self.__multiple_recordings_debug_header.clear()

        file_name = str(Path(file_name))
        if not self.is_file_exist(file_name):
            return

        error_counter = self.__read_and_parse_json_file(file_name, self.__multiple_recordings_debug_list, 'jump')
        return self.__create_multiple_recording_data(), error_counter

    def __read_and_parse_json_file(self, file_name: str, list_to_append: list, type_str: str):
        error_counter = 0
        with open(file_name, 'r') as file:
            for line in file:
                try:
                    list_to_append.append(json.loads(line.strip()))
                except json.decoder.JSONDecodeError as ex:
                    if r'Invalid \escape' in ex.msg:
                        list_to_append.append(json.loads(line.strip().replace('\\', '\\\\')))
                    else:
                        error_counter += 1
                        self.__parsing_error_notification(type_str, file_name, line, traceback.format_exc())
                except:
                    error_counter += 1
                    self.__parsing_error_notification(type_str, file_name, line, traceback.format_exc())
        return error_counter

    def __parsing_error_notification(self, type_str: str, file_name: str, line: str, traceback_string: str):
        logging.error(f"Failed to parse a line in {type_str} file {file_name}: {line}")
        logging.error(traceback_string)
        self.notifications.notify_error(title='Metadata Handler',
                                        body=f"Failed parse a line in the {type_str} file , see logs for more details")

    def get_debug_metadata_file_path(self, video_path: str, metadata_type: MetaDataType, row_selected: int = None,
                                     notify_local_error: bool = True) -> str | None:
        file_path = None
        if self.__multiple_recordings_debug_header: ##the else of this if is for Backward compatible
            video_name = os.path.splitext(os.path.basename(video_path))[0] #Remove file suffix if exist
            metadata_key = PRIMARY_METADATA if metadata_type == MetaDataType.PRIMARY else SECONDARY_METADATA ##Backward compatible
            if metadata_key in self.__multiple_recordings_debug_header: ##Backward compatible
                relevant_metadata_path = self.__multiple_recordings_debug_header[metadata_key]
            else:
                relevant_metadata_path = self.get_metadata_file_path_by_row(row_selected + 1, metadata_type)

            if not relevant_metadata_path:
                error_message = f"Could not detect relevant metadata file"
                self.notifications.notify_error(title='Metadata Handler', body=error_message)
                logging.error(error_message)
                self.find_metadata_file = False
                return None
            file_path = relevant_metadata_path

            
            ##TODO: Remove the following lines
            if 0:
                jump_folder = relevant_metadata_path if relevant_metadata_path.endswith(JSON_EXTENSION) else \
                    os.path.join(relevant_metadata_path, video_name)
                jump_folder = str(Path(jump_folder))
                jump_files = []
                base_path = PRIMARY_META_DATA_PATH if metadata_type == MetaDataType.PRIMARY else SECONDARY_META_DATA_PATH
                local_path = self.verify_local_path(jump_folder, notify_error=notify_local_error, base_path=base_path)
                if local_path:
                    if self.is_file_exist(local_path, notify_error=False) and not jump_folder.endswith(JSON_EXTENSION):
                        try:
                            jump_files = glob.glob(fr'{local_path}\*{JSON_EXTENSION}')
                        except (TypeError, SyntaxError):
                            traceback_string = traceback.format_exc()
                            logging.error(traceback_string)
                    elif local_path.endswith(JSON_EXTENSION):
                        jump_files = [local_path]
                    else:
                        self.find_metadata_file = False
                        return None
                else:
                    self.get_blob_files(self.verify_blob_path(jump_folder.replace('\\', '/')))
                    jump_files = [f for f in self.files_list_on_blob() if f.endswith(JSON_EXTENSION)]
            
            
                if not jump_files and not notify_local_error:
                    self.find_metadata_file = False
                    return None
                if not jump_files:
                    given_path = jump_folder if '/' not in jump_folder else jump_folder.replace('\\', '/')
                    error_message = f"No metadata files were found at the given path - {given_path}"
                    self.notifications.notify_error(title='Metadata Handler', body=error_message)
                    logging.error(error_message)
                else:
                    file_path = jump_files[0]  # TODO: FIX!! it won't always be the first file
        elif row_selected: ##Backward compatible
            raise Exception("This jump file conventionsis not supported anymore")
            # relevant_column = PRIMARY_METADATA_TITLE if metadata_type == MetaDataType.PRIMARY else SECONDARY_METADATA_TITLE
            # file_path = self.get_metadata_file_path_by_row(row_selected, relevant_column)

        self.find_metadata_file = False
        return file_path

    def get_metadata_file_path_by_row(self, row_number: int, metadata_type: MetaDataType) -> str | None:

        ## Get row from jump file
        if row_number is None:
            return None
        relevant_row = self.__multiple_recordings_debug_list[row_number]
        
        ## Get video name from row
        # The supported conventions for rows' keys: for each row there is only VIDEO_LOCATION (video name) field (+start & end frames).
        if VIDEO_LOCATION not in relevant_row[MESSAGE]:
            return None
        video_name: str = relevant_row[MESSAGE][VIDEO_LOCATION]
        
        ## Get path and log_file from jump file header
        report_type = PRIMARY_REPORT if metadata_type == MetaDataType.PRIMARY else SECONDARY_REPORT
        jump_file_header_base_path, jump_file_header_log_file_name = self.get_metadata_properties(report_type)
        
        ## Get alternative path anf log_name from setting/ configuration files - they are supperior for jump file
        if metadata_type == MetaDataType.PRIMARY:
            base_path_to_use = PRIMARY_META_DATA_PATH if PRIMARY_META_DATA_PATH else jump_file_header_base_path
            log_file_name_or_suffix = PRIMARY_METADATA_LOG_NAME if PRIMARY_METADATA_LOG_NAME else jump_file_header_log_file_name
        elif metadata_type == MetaDataType.SECONDARY:
            base_path_to_use = SECONDARY_META_DATA_PATH if SECONDARY_META_DATA_PATH else jump_file_header_base_path
            log_file_name_or_suffix = SECONDARY_METADATA_LOG_NAME if SECONDARY_METADATA_LOG_NAME else jump_file_header_log_file_name
        else:
            assert (0)
        
        ## Concat the base_path_to_use if needed
        log_path = os.path.join(base_path_to_use, video_name) if base_path_to_use and (not video_name.startswith(base_path_to_use)) else video_name
        
        ## Check if need to concat the "log_path" with "log_file_name_or_suffix"
        if (not log_file_name_or_suffix) or\
            (len(log_file_name_or_suffix) == 0) or\
            log_path.endswith(log_file_name_or_suffix): # `log_file_name_or_suffix` is not exists OR empty str OR `log_path` already endswith `log_file_name_or_suffix`
            assert (f"meta_data_log value must be either: 1. a log file name or 2. file suffix or 3. the 'GT' alias\nYou can define meta_data_log in {metadata_type.name}_METADATA_LOG_NAME in setting.json or log_file_name in jump file geader")
        else:
            if log_file_name_or_suffix.upper().strip() == "GT":  ## This is an alias fot GT suffix
                log_file_name_or_suffix = ".json"
            if log_file_name_or_suffix.startswith("."): # if `log_file_name_or_suffix` is file suffix need to concat strings
                log_path = log_path + log_file_name_or_suffix 
            else: # If `log_file_name_or_suffix` is actual file name, need to concat as library + file using join
                log_path = os.path.join(log_path, log_file_name_or_suffix)

        return log_path

### ADDED IN MANUAL MERGE ==>
    def get_metadata_file_from_blob(self, video_path, metadata_type: MetaDataType, row_selected: int = None):
        while self.find_metadata_file:
            time.sleep(0.01)  # wait for metadata file search to be completed since blob searching is longer and data might be incorrect
        self.find_metadata_file = True
        file_path = None
        if self.__multiple_recordings_debug_header:
            video_name = os.path.splitext(os.path.basename(video_path))[0]
            metadata_key = PRIMARY_METADATA if metadata_type == MetaDataType.PRIMARY else SECONDARY_METADATA
            if metadata_key in self.__multiple_recordings_debug_header:
                relevant_metadata_path = self.__multiple_recordings_debug_header[metadata_key]
            else:
                log_path_key = PRIMARY_LOG_PATH if metadata_type == MetaDataType.PRIMARY else SECONDARY_LOG_PATH
                report_type = PRIMARY_REPORT if metadata_type == MetaDataType.PRIMARY else SECONDARY_REPORT
                relevant_metadata_path = self.get_metadata_file_path_by_row(row_selected + 1, log_path_key, report_type)

            if not relevant_metadata_path:
                error_message = f"Could not detect relevant metadata file"
                self.notifications.notify_error(title='Metadata Handler', body=error_message)
                logging.error(error_message)
                self.find_metadata_file = False
                return None

            jump_folder = relevant_metadata_path if relevant_metadata_path.endswith(JSON_EXTENSION) else \
                os.path.join(relevant_metadata_path, video_name)
            jump_folder = str(Path(jump_folder))
            self.get_blob_files(self.verify_blob_path(jump_folder.replace('\\', '/')))
            jump_files = [f for f in self.files_list_on_blob() if f.endswith(JSON_EXTENSION)]
            if not jump_files:
                given_path = jump_folder if '/' not in jump_folder else jump_folder.replace('\\', '/')
                error_message = f"No metadata files were found at the given blob path - {given_path}"
                self.notifications.notify_error(title='Metadata Handler', body=error_message)
                logging.error(error_message)
            else:
                file_path = jump_files[0]  # TODO: FIX!! it won't always be the first file
        elif row_selected:
            relevant_column = PRIMARY_METADATA_TITLE if metadata_type == MetaDataType.PRIMARY else SECONDARY_METADATA_TITLE
            file_path = self.get_metadata_file_path_by_row(row_selected, relevant_column)

        self.find_metadata_file = False
        return file_path
		### <<== ADDED IN MANUAL MERGE
		
    def __create_multiple_recording_data(self):
        self.__multiple_recordings_debug = pd.DataFrame()

        for multiple_recording_debug_proto in self.__multiple_recordings_debug_list:
            if KEYS in multiple_recording_debug_proto and multiple_recording_debug_proto[KEYS][TYPE] == DEBUG:
                df_dictionary = pd.DataFrame([multiple_recording_debug_proto[MESSAGE]])
                self.__multiple_recordings_debug = pd.concat([self.__multiple_recordings_debug, df_dictionary], ignore_index=True)

            if HEADER in multiple_recording_debug_proto:
                self.__multiple_recordings_debug_header = multiple_recording_debug_proto[HEADER]

        ordered_column = [IS_CHECKED_ID, VIDEO_LOCATION, FRAME_NUMBER]
        original_column = list(self.__multiple_recordings_debug.columns)

        for item in ordered_column:
            if item in original_column:
                original_column.remove(item)

        ordered_column.extend(original_column)
        self.__multiple_recordings_debug = self.__multiple_recordings_debug.reindex(columns=ordered_column)

        for index in range(0, len(self.__multiple_recordings_debug[IS_CHECKED_ID])):
            self.__multiple_recordings_debug[IS_CHECKED_ID][index] = CHECKED_ICON if self.__multiple_recordings_debug[IS_CHECKED_ID][
                                                                                         index] == 'True' else UNCHECKED_ICON
        return self.__multiple_recordings_debug

    def create_multiple_recordings_header_to_export(self, exported_data: list) -> list:
        """
        Adding header data to jump JSON file in case exists
        :param exported_data: data to export
        :return: list with header data if exists
        """
        if self.__multiple_recordings_debug_header:
            ordered_header = dict(sorted(self.__multiple_recordings_debug_header.items()))
            exported_data.append({HEADER: ordered_header})
        return exported_data

    def create_multiple_recordings_to_export(self, table_data: list[dict], file_name: str):
        exported_data = []
        try:
            self.create_multiple_recordings_header_to_export(exported_data)
            for item in table_data:
                temp_dictionary = dictionary_keys.copy()
                item[IS_CHECKED_ID] = convert_icon_to_bool(item[IS_CHECKED_ID])
                temp_dictionary[MESSAGE] = item
                exported_data.append(temp_dictionary)
            self.__save_multiple_recordings_debug_to_file(exported_data, file_name)
        except:
            traceback_string = traceback.format_exc()
            logging.error(traceback_string)
            self.notifications.notify_error(title='Metadata Handler',
                                            body="An exception raised while exporting the data, see logs for more details")

    def __save_multiple_recordings_debug_to_file(self, exported_data, file_name):
        with open(file_name, 'w') as outfile:
            for item in exported_data:
                json.dump(item, outfile)
                outfile.write('\n')

    def is_file_exist(self, file_name: str, notify_error: bool = True) -> bool:
        if os.path.exists(file_name) is False:
            if notify_error:
                error_message = f"{file_name} not found"
                self.notifications.notify_error(title='Metadata Handler', body=error_message)
                logging.error(error_message)
            return False
        return True

    def get_all_jump_frame_range_by_clip_path(self, clip_path: str) -> list:
        events = []
        for row in self.__multiple_recordings_debug.iterrows():
            if row[1][VIDEO_LOCATION] == clip_path:
                events.extend([int(row[1][FRAME_NUMBER]), int(row[1][END_FRAME])])
        return events
