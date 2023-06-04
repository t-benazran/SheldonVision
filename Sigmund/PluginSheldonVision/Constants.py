import inspect
from enum import Enum

PLUGIN_LOG_PATH = f"logs\\SheldonVisionUiPluginPy"
DECIMATION_COLOR_OFF = '#71042F'
DECIMATION_COLOR_ON = '#046816'
NO_FRAME_SELECTED = [0, 0]
MAX_NUM_FRAMES_SELECTED = 1
RECORDING_INFO_CARD_ID = "RecordingInfo"
NO_FRAMES_SELECTED_MESSAGE = 'No frames selected'
FONT_SIZE_20PX = {"font-size": "20px"}
FONT_SIZE_15PX_WHITE = {"font-size": "15px", "color": "white"}
NO_FILES_SELECTED = 'No files selected, Select video(*.mp4) to play by browser button'
NO_FILES_SELECTED_JSON = 'No files selected, Select MetaData(*.json) by browser button'
NO_SETTINGS_FILE_SELECTED = 'No settings file selected'
INSERT_VIDEO_URI_TXT = "Enter Video URI Here:"
INVALID_URI = 'Invalid URI input, please enter a valid URI'
TOGGLE_SWITCH_SIZE = 60
WIDTH_20_STYLE = {'width': '20%'}
WIDTH_100_STYLE = {'width': '100%'}
CLOSE_APPLICATION_COLUMN_STYLE = {'margin': '5px', 'margin-right': '1px'}
URI_INPUT_STYLE = {'width': '20%', 'marginLeft': 710}
URI_INPUT_STYLE_HIDDEN = {'width': '20%', 'marginLeft': 710, 'display': 'none'}
BUTTONS_COLUMN_STYLE = {'margin': '5px'}
BUTTONS_FONT_STYLE_PLAYER = {'width': '70px', 'font-size': '2rem'}
BUTTONS_FONT_STYLE = {'width': '70px', 'font-size': '1.3rem'}
BUTTONS_STYLE = {'text-transform': 'none', 'width': '80px'}
BROWSE_BUTTONS_STYLE = {'text-transform': 'none', 'width': '200px', 'background-color': '#66B2FF'}
DROP_DOWN_BUTTONS_STYLE = {'width': '10px', 'background-color': '#66B2FF'}
CLOSE_NETWORK_BUTTON_STYLE = {'text-transform': 'none', 'width': '100px', 'background-color': '#db2a2a'}
DECIMATION_BUTTONS_STYLE = {'text-transform': 'none', 'width': '200px', 'background-color': DECIMATION_COLOR_OFF}
SEND_MAIL_BUTTONS_STYLE = {'text-transform': 'none', 'width': '120px', 'background-color': '#66B2FF'}
HIGHLIGHT_TEXT_STYLE = {"color": "red", "font-size": "20px"}
INDICATION_TEXT_STYLE = {"color": "lightgray", "font-size": "20px"}
MARGIN_0_STYLE = {'margin': '0'}
PLOT_WIDTH = 640
PLOT_HEIGHT = 480
DEFAULT_FPS = 30
ONLINE_FONT_SIZE = 65
JSON_SUFFIX = 'json'
MP4_SUFFIX = '.mp4'
JSON_FILES_TYPE = (('MetData files', f'*.{JSON_SUFFIX}'),)
JUMP_FILES_TYPE = (('Jump files', f'*.{JSON_SUFFIX}'),)
MP4_FILES_TYPE = (('Video files', f'*{MP4_SUFFIX}'),)
VIDEO_DATA_IDX = 0
HALF_SECOND = 0.5
TENTH_SECOND = 0.1
TEN_MILLISECONDS = 0.01
KEYS = 'Keys'
VALUES = 'Values'
HEADER = 'header'
EMULATED_RESOLUTION = 'emulated_resolution'
EMUMLATION_MATRIX = 'emulation_matrix'
SHELDON_VISION_URL = 'http:127.0.0.1:8050'
SHELDON_VISION_BLOB_URL = 'https://sheldonvision.blob.core.windows.net'
BLOB_CONTAINER_NAME = 'sheldon-vision'
BLOB_IDENTIFIER = 'blob.core.windows.net'
LOCAL_METADATA_DOWNLOAD_LOCATION = r"C:\Tools\Metadata"
POINTS = 'points'
X = 'x'
Y = 'y'
SHELDON_VISION_UI_TITLE = 'SheldonVisionUI'
MARK_COLOR_SELECTED = '#E60000'
MARK_COLOR_EXTENDED = '#990099'
DECIMATION_SPEED_VALUES = [0.25, 0.5, 0.75, 1, 2, 4]

# Keyboard shortcut keys
ALT_PLUS = "Alt+"
FAST_FORWARD_BUTTON = "h"
BACK_BUTTON = "j"
FORWARD_BUTTON = "l"
PAUSE_BUTTON = "k"
PLAY_BUTTON = "i"
VIDEO_BROWSE_BUTTON = "r"
META_DATA_PRIMARY_BROWSE_BUTTON = "t"
META_DATA_SECONDARY_BROWSE_BUTTON = "y"
DEBUG_RECORDINGS_BROWSE_BUTTON = "u"
CLOSE_NETWORK_BUTTON = "c"
SEND_MAIL_BUTTON = "s"
DECIMATION_BUTTON = 'd'

FAST_FORWARD_BUTTON_SHORTCUT = f"{ALT_PLUS}{FAST_FORWARD_BUTTON}"
BACK_BUTTON_SHORTCUT = f"{ALT_PLUS}{BACK_BUTTON}"
FORWARD_BUTTON_SHORTCUT = f"{ALT_PLUS}{FORWARD_BUTTON}"
PAUSE_BUTTON_SHORTCUT = f"{ALT_PLUS}{PAUSE_BUTTON}"
PLAY_BUTTON_SHORTCUT = f"{ALT_PLUS}{PLAY_BUTTON}"
VIDEO_BROWSE_BUTTON_SHORTCUT = f"{ALT_PLUS}{VIDEO_BROWSE_BUTTON}"
META_DATA_PRIMARY_BROWSE_BUTTON_SHORTCUT = f"{ALT_PLUS}{META_DATA_PRIMARY_BROWSE_BUTTON}"
META_DATA_SECONDARY_BROWSE_BUTTON_SHORTCUT = f"{ALT_PLUS}{META_DATA_SECONDARY_BROWSE_BUTTON}"
DEBUG_RECORDINGS_BROWSE_BUTTON_SHORTCUT = f"{ALT_PLUS}{DEBUG_RECORDINGS_BROWSE_BUTTON}"
CLOSE_NETWORK_SHORTCUT = f"{ALT_PLUS}{CLOSE_NETWORK_BUTTON}"
SEND_MAIL_SHORTCUT = f"{ALT_PLUS}{SEND_MAIL_BUTTON}"
DECIMATION_BUTTON_SHORTCUT = f"{ALT_PLUS}{DECIMATION_BUTTON}"


BUTTON_CLASS_NAME = 'btn btn-primary'
BACK_BUTTON_ICON_CLASS_NAME = 'bi bi-skip-start'
CLOSE_APPLICATION_ICON_CLASS_NAME = 'bi bi-x-circle'
PLAY_BUTTON_ICON_CLASS_NAME = 'bi-play'
FORWARD_BUTTON_ICON_CLASS_NAME = 'bi bi-skip-end'
PAUSE_BUTTON_ICON_CLASS_NAME = 'bi bi-pause'
SEARCH_BUTTON_ICON_CLASS_NAME = 'bi bi-search'
FAST_FORWARD_BUTTON_ICON_CLASS_NAME = 'bi bi-skip-backward'
SEND_MAIL_ICON_CLASS_NAME = 'bi bi-envelope'
DECIMATION_ICON_CLASS_NAME = 'bi bi-collection'


class ButtonsIndex(Enum):

    BACK_BUTTON_INDEX = 0
    PLAY_BUTTON_INDEX = 1
    NEXT_BUTTON_INDEX = 2
    SLIDER_INDEX = 3
    PAUSE_BUTTON_INDEX = 5
    VIDEO_BROWSER_BUTTON_INDEX = 6
    METADATA_PRIMARY_BROWSER_BUTTON_INDEX = 7
    METADATA_SECONDARY_BROWSER_BUTTON_INDEX = 8
    MULTIPLE_RECORDING_BROWSER_BUTTON_INDEX = 9
    FAST_BACK_BUTTON_INDEX = 10
    SLIDER_FPS_INDEX = 11
    CLOSE_NETWORK_BUTTON_INDEX = 12
    SEND_MAIL_BUTTON_INDEX = 13
    DECIMATION_SPEED_SLIDER_INDEX = 14
    DECIMATION_BUTTON_INDEX = 15


class OutputCallbacksIdx(Enum):
    SLIDER_VALUE_IDX = 0
    FRAME_INPUT_NUMBER_VALUE_IDX = 1
    SLIDER_MIN_VALUE_IDX = 2
    SLIDER_MAX_VALUE_IDX = 3
    VIDEO_FILES_LIST_LABEL_IDX = 4
    SETTINGS_FILE = 5
    SLIDER_MARKS_VALUE_IDX = 6
    SLIDER_FPS_VALUE_IDX = 7
    FPS_INPUT_VALUE_IDX = 8
    PRIMARY_METADATA_GENERAL_IDX = 9
    SECONDARY_METADATA_GENERAL_IDX = 10
    PRIMARY_GRAPH_OFFLINE_FIGURE_IDX = 11
    SECONDARY_GRAPH_OFFLINE_FIGURE_IDX = 12
    DECIMATION_BUTTONS_STYLE_IDX = 13
    SLIDER_FPS_STYLE_IDX = 14
    SLIDER_SPEED_STYLE_IDX = 15
    SLIDER_SPEED_VALUE_IDX = 16
    INPUT_SPEED_VALUE_IDX = 17
    VIDEO_MODAL_IS_OPEN_IDX = 18


class PathStatus(Enum):
    Valid = "Valid"
    Invalid = "Invalid"


# SheldonVisionUI plugin input types
CAMERA_FRAMES_MESSAGE_TYPE = f"CameraFrame"
GET_TOTAL_VIDEO_FRAMES_MSG_NAME = "GetTotalVideoFrames"
PATH_STATUS_MSG = "PathStatus"
FPS_STATUS_MESSAGE = "FpsStatus"
FINISH_UPLOAD_FILE_MSG_TYPE = "FinishedUploadBlob"
FINISH_DOWNLOAD_FILE_MSG_TYPE = "FinishedDownloadBlob"
FILES_LIST_IN_BLOB_RESPONSE = "FilesListInBlobResponse"


# SheldonVisionUI plugin output types
TOTAL_VIDEO_FRAMES_MSG_NAME = "TotalVideoFrames"
PLAY_MESSAGE = "PlayerPlay"
STOP_MESSAGE = "PlayerStop"
NEXT_FRAME_MESSAGE = "PlayerNextFrame"
PREVIOUS_FRAME_MESSAGE = "PlayerPreviousFrame"
PAUSE_MESSAGE = "PlayerPause"
SET_FRAME_MESSAGE = "PlayerSetFrame"
LOAD_REQUEST_MESSAGE = "LoadRequest"
GET_CURRENT_FRAME_MESSAGE = "GetCurrentFrame"
SET_FRAME_PER_SECOND = "SetFramePerSecond"
GET_FRAME_PER_SECOND = "GetFramePerSecond"
RELAYOUT_DATA_EVENT = 'relayoutData'
CLICK_DATA_EVENT = 'clickData'
AZURE_BLOB_MSG_TYPE = "AzureUploadCommand"
AZURE_BLOB_MSG_DOWNLOAD_TYPE = "AzureDownloadCommand"
FILES_LIST_IN_BLOB_REQUEST = "FilesListInBlobRequest"

# SheldonVision Ids
SEND_MAIL_BUTTON_ID = "SendMailButton"
SEND_MAIL_BUTTON_SEND_ID = "mail-modal-send-button"
SEND_MAIL_BUTTON_CANCEL_ID = "mail-modal-cancel-button"
SEND_MAIL_INPUT_ID = "mail-modal-input"
SEND_MAIL_ADDITIONAL_INPUT_ID = "mail-modal-input-additional"
SEND_MAIL_INVALID_LABEL_ID = "mail-modal-invalid-label"
SEND_MAIL_INVALID_FIELDS_LABEL_ID = "mail-modal-invalid-fields-label"
SEND_MAIL_MODAL_ID = "send-mail-modal"
CLOSE_NETWORK_ID = "CloseNetwork"
BROWSE_BUTTON_ID = "BrowseButton"
TOGGLE_SWITCH_ID = "ToggleSwitch"
URI_INPUT_ID = "URIInput"
PAUSE_BUTTON_ID = "PauseButton"
FAST_BACK_BUTTON_ID = "FastBackButton"
SLIDER_INTERVAL_ID = "SliderInterval"
VIDEO_LOADED_FILES_LIST_ID = "VideoLoadedFilesList"
METADATA_LOADED_FILES_LIST_ID = "MetadataLoadedFilesList"
METADATA_SECONDARY_LOADED_FILES_LIST_ID = "MetadataLoadedFilesListSecondary"
SETTINGS_LOADED_LABEL_ID = "SettingsLabel"
BROWSE_METADATA_BUTTON_ID = "MetaDataButton"
BROWSE_METADATA_SECONDARY_BUTTON_ID = "MetaDataButtonSecondary"
BROWSE_RECORDINGS_DEBUG_DATA_BUTTON_ID = "BrowseRecordingsDebugDataButton"
RECORDINGS_DEBUG_DATA_LABEL_ID = "RecordingsDebugDataLabel"
RECORDINGS_DEBUG_DATA_TABLE_ID = "RecordingsDebugDataTable"
RECORDINGS_DEBUG_DATA_TABLE_DIV_ID = "RecordingsDebugDataTableDiv"
PRIMARY_METADATA_ID = "primary-metadata"
SECONDARY_METADATA_ID = "secondary-metadata"
PRIMARY_GRAPH_ID = "PrimaryGraph"
SECONDARY_GRAPH_ID = "SecondaryGraph"
GRAPH_DIV_ID = "GraphDiv"
SLIDER_FPS_ID = "SliderFPS"
FPS_INPUT_ID = "FpsInput"
FPS_SLIDER_ID = "FpsSlider"
AUTORUN_FROM_MAIL_INTERVAL_ID = "AutoRunFromMail"
ALERTS_INTERVAL_ID = "AlertInterval"
JUMP_LOAD_INTERVAL_ID = "JumpLoadInterval"
DECIMATION_BUTTON_ID = "DecimationButton"
DECIMATION_SPEED_SLIDER_ID = "DecimationSpeedSlider"
DECIMATION_SPEED_INPUT_ID = "DecimationSpeedInput"
FULL_FPS_SLIDER_ID = f'slider-{FPS_SLIDER_ID}'
FULL_SPEED_SLIDER_ID = f'slider-{DECIMATION_SPEED_SLIDER_ID}'
ONLINE_ID = "Online"
OFFLINE_ID = "Offline"
PRIMARY_GENERAL_DIV = f"primary-metadata-general-div"
SECONDARY_GENERAL_DIV = f"secondary-metadata-general-div"
LOCAL_FILE_NOT_FOUND_ID = 'local-file-not-found'
SUBMIT_N_CLICKS = 'submit_n_clicks'
CANCEL_N_CLICKS = 'cancel_n_clicks'
PRIMARY_GRAPH_ONLINE_DIV_ID = f"{PRIMARY_GRAPH_ID}{ONLINE_ID}{GRAPH_DIV_ID}"
SECONDARY_GRAPH_ONLINE_DIV_ID = f"{SECONDARY_GRAPH_ID}{ONLINE_ID}{GRAPH_DIV_ID}"
PRIMARY_GRAPH_OFFLINE_DIV_ID = f"{PRIMARY_GRAPH_ID}{OFFLINE_ID}{GRAPH_DIV_ID}"
SECONDARY_GRAPH_OFFLINE_DIV_ID = f"{SECONDARY_GRAPH_ID}{OFFLINE_ID}{GRAPH_DIV_ID}"
PRIMARY_GRAPH_ONLINE_FIGURE_ID = f"{PRIMARY_GRAPH_ID}{ONLINE_ID}"
SECONDARY_GRAPH_ONLINE_FIGURE_ID = f"{SECONDARY_GRAPH_ID}{ONLINE_ID}"
PRIMARY_GRAPH_OFFLINE_FIGURE_ID = f"{PRIMARY_GRAPH_ID}{OFFLINE_ID}"
SECONDARY_GRAPH_OFFLINE_FIGURE_ID = f"{SECONDARY_GRAPH_ID}{OFFLINE_ID}"
GENERAL_DIV_STATUS_ID = f"GeneralDivStatus"
ACTIVE_CELL_ID = "active_cell"
RECORDINGS_DEBUG_EXPORT_BUTTON_ID = "RecordingsDebugExportButton"
ADDING_ROWS_TABLE = 'adding-rows-table'
ADDING_ROWS_BUTTON = 'adding-rows-button'
EDITING_ROWS_BUTTON = 'editing-rows-button'
ADDING_ROWS_NAME = 'adding-rows-name'
ADDING_ROWS_GRAPH = 'adding-rows-graph'
DEBUG_EDITABLE_TABLE = f'{RECORDINGS_DEBUG_DATA_TABLE_ID}-{ADDING_ROWS_TABLE}'
DEBUG_ADD_COLUMN_BUTTON = f'{RECORDINGS_DEBUG_DATA_TABLE_ID}-{ADDING_ROWS_BUTTON}'
DEBUG_ADD_ROW_BUTTON = f'{RECORDINGS_DEBUG_DATA_TABLE_ID}-{EDITING_ROWS_BUTTON}'
DEBUG_COLUMN_NAME_INPUT = f'{RECORDINGS_DEBUG_DATA_TABLE_ID}-{ADDING_ROWS_NAME}'
ERROR_MESSAGE = 'error-message'
ERROR_MESSAGE_EMAIL = 'error-message-email'
AZURE_SAS_ERROR = "ErrorCode: AuthenticationFailed"
JUMP_FILE_ID = 'jump-file-name'
LOADING_FROM_MAIL_LABEL_ID = 'loading-from-mail'
JUMP_LOADING_LABEL_ID = 'loading-jump'
DROP_DOWN_PRIMARY_LOCAL = f'{BROWSE_METADATA_BUTTON_ID}-drop-down-Local-File'
DROP_DOWN_PRIMARY_BLOB = f'{BROWSE_METADATA_BUTTON_ID}-drop-down-Blob'
DROP_DOWN_SECONDARY_LOCAL = f'{BROWSE_METADATA_SECONDARY_BUTTON_ID}-drop-down-Local-File'
DROP_DOWN_SECONDARY_BLOB = f'{BROWSE_METADATA_SECONDARY_BUTTON_ID}-drop-down-Blob'
DROP_DOWN_JUMP_LOCAL = f'{BROWSE_RECORDINGS_DEBUG_DATA_BUTTON_ID}-drop-down-Local-File'
DROP_DOWN_JUMP_BLOB = f'{BROWSE_RECORDINGS_DEBUG_DATA_BUTTON_ID}-drop-down-Blob'
DROP_DOWN_VIDEO_LOCAL = f'{BROWSE_BUTTON_ID}-drop-down-Local-File'
DROP_DOWN_VIDEO_BLOB = f'{BROWSE_BUTTON_ID}-drop-down-Blob'
INPUT_METADATA_MODAL = 'input-metadata-modal'
INPUT_METADATA_MODAL_INPUT = 'input-metadata-modal-input'
INPUT_METADATA_MODAL_OK = 'input-metadata-modal-ok-button'
INPUT_METADATA_MODAL_CANCEL = 'input-metadata-modal-cancel-button'
INPUT_METADATA_MODAL_TYPE = 'input-metadata-modal-type'
INPUT_METADATA_MODAL_HEADER = 'input-metadata-modal-header'
INPUT_METADATA_MODAL_LABEL = 'input-metadata-modal-label'
LOG_FILE_LINK_INPUT = 'input-log-file-link'
INPUT_VIDEO_MODAL = 'input-video-modal'
INPUT_VIDEO_MODAL_INPUT = 'input-video-modal-input'
INPUT_VIDEO_MODAL_OK = 'input-video-modal-ok-button'
INPUT_VIDEO_MODAL_CANCEL = 'input-video-modal-cancel-button'

CONFIG_VIDEO_FILE_PATH = "Video"
CONFIG_DEBUG_FILE_PATH = "DebugMultiVideosFile"
CONFIG_PRIMARY_SECTION = "Primary"
CONFIG_SECONDARY_SECTION = "Secondary"
CONFIG_METADATA_FILE_PATH = "Metadata"
CONFIG_LAYERS_LIST = "Layers"
CONFIG_FPS = "FPS"

ERROR_FORMAT = '\n\n=========================\n{}\n=========================\n'
FPS_RANGE = [1, 200]


def extract_class_values(cls) -> list[str]:
    instance = cls()
    return [instance.__getattribute__(v) for v in instance.__dir__() if '__' not in v and v != 'get_all']


class Color:
    """
    Define available colors which can be used on the dash
    TestTextLayer uses those colors
    """
    Salmon = 'salmon'
    Crimson = 'crimson'
    Red = 'red'
    DarkRed = 'darkred'
    Pink = 'pink'
    HotPink = 'hotpink'
    Coral = 'coral'
    Orange = 'orange'
    Gold = 'gold'
    Yellow = 'yellow'
    LightYellow = 'lightyellow'
    Khaki = 'khaki'
    Lavender = 'lavender'
    Plum = 'plum'
    Violet = 'violet'
    Magenta = 'magenta'
    DarkViolet = 'darkviolet'
    Indigo = 'indigo'
    Lime = 'lime'
    Green = 'green'
    Olive = 'olive'
    Cyan = 'cyan'
    LightBlue = 'lightblue'
    Blue = 'blue'
    Navy = 'navy'
    Tan = 'tan'
    Chocolate = 'chocolate'
    Brown = 'brown'
    White = 'white'
    Silver = 'silver'
    Gray = 'gray'
    Black = 'black'

    @classmethod
    def get_all(cls):
        """
        Create list of all available colors value
        :return: list of colors value
        """
        return extract_class_values(cls)


class FontFamily:
    """
    Define available font families which can be used on the dash
    TestTextLayer uses those font families
    """
    AndaleMono = 'Andale Mono, monospace'
    Arial = 'Arial, sans-serif'
    ArialBlack = 'Arial Black, sans-serif'
    Baskerville = 'Baskerville, serif'
    BradleyHand = 'Bradley Hand, cursive'
    BrushScriptMT = 'Brush Script MT, cursive'
    ComicSansMS = 'Comic Sans MS, cursive'
    Courier = 'Courier, monospace'
    Georgia = 'Georgia, serif'
    GillSans = 'Gill Sans, sans-serif'
    Helvetica = 'Helvetica, sans-serif'
    Impact = 'Impact, sans-serif'
    Lucida = 'Lucida, monospace'
    Luminari = 'Luminari, fantasy'
    Monaco = 'Monaco, monospace'
    Palatino = 'Palatino, serif'
    Tahoma = 'Tahoma, sans-serif'
    TimesNewRoman = 'Times New Roman, serif'
    TrebuchetMS = 'Trebuchet MS, sans-serif'
    Verdana = 'Verdana, sans-serif'

    @classmethod
    def get_all(cls):
        """
        Create list of all available font families value
        :return: list of font families value
        """
        return extract_class_values(cls)


class Font:
    """
    Define available fonts which can be used on the dash
    TestTextLayer uses those fonts
    """
    Arial = 'arial.ttf'
    ArialBlack = 'ariblk.ttf'
    Baskerville = 'baskvill.ttf'
    BradleyHand = 'bradhitx.ttf'
    BrushScriptMT = 'brushsci.ttf'
    Calibri = "calibri.ttf"
    ComicSansMS = 'comici.ttf'
    Courier = 'cour.ttf'
    David = "david.ttf"
    Georgia = 'georgia.ttf'
    Impact = 'impact.ttf'
    Lucida = 'lucon.ttf'
    Tahoma = 'tahoma.ttf'
    TimesNewRoman = 'times.ttf'
    TrebuchetMS = 'trebuc.ttf'
    Verdana = 'verdana.ttf'

    @classmethod
    def get_all(cls):
        """
        Create list of all available fonts value
        :return: ist of fonts value
        """
        return extract_class_values(cls)
