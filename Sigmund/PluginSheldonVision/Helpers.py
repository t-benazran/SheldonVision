import dash
from PluginSheldonVision.Constants import OutputCallbacksIdx


def prepare_main_ui_output_callbacks(slider_value=dash.no_update,
                                     frame_input_number_value=dash.no_update,
                                     slider_min_value=dash.no_update,
                                     slider_max_value=dash.no_update,
                                     video_files_list_label=dash.no_update,
                                     settings_file=dash.no_update,
                                     slider_marks_value=dash.no_update,
                                     slider_fps_value=dash.no_update,
                                     fps_input_value=dash.no_update,
                                     primary_metadata_general=dash.no_update,
                                     secondary_metadata_general=dash.no_update,
                                     primary_graph_offline_figure=dash.no_update,
                                     secondary_graph_offline_figure=dash.no_update,
                                     decimation_button_style=dash.no_update,
                                     slider_fps_style=dash.no_update,
                                     slider_speed_style=dash.no_update,
                                     slider_speed_value=dash.no_update,
                                     input_speed_value=dash.no_update,
                                     video_modal_is_open=dash.no_update):
    """
    create list of callbacks for main ui
    @param slider_value:
    @param frame_input_number_value:
    @param slider_min_value:
    @param slider_max_value:
    @param video_files_list_label:
    @param settings_file:
    @param slider_marks_value:
    @param slider_fps_value:
    @param fps_input_value:
    @param primary_metadata_general:
    @param secondary_metadata_general:
    @param primary_graph_offline_figure:
    @param secondary_graph_offline_figure:
    @param decimation_button_style:
    @param slider_fps_style:
    @param slider_speed_style:
    @param slider_speed_value:
    @param input_speed_value:
    @param video_modal_is_open:
    @return:
    """
    return [slider_value, frame_input_number_value, slider_min_value, slider_max_value, video_files_list_label, settings_file,
            slider_marks_value, slider_fps_value, fps_input_value, primary_metadata_general, secondary_metadata_general,
            primary_graph_offline_figure, secondary_graph_offline_figure, decimation_button_style, slider_fps_style, slider_speed_style,
            slider_speed_value, input_speed_value, video_modal_is_open]


def modify_main_ui_output_callbacks(callbacks_list_to_modify,
                                    slider_value=None,
                                    frame_input_number_value=None,
                                    slider_min_value=None,
                                    slider_max_value=None,
                                    video_files_list_label=None,
                                    settings_file=None,
                                    slider_marks_value=None,
                                    slider_fps_value=None,
                                    fps_input_value=None,
                                    primary_metadata_general=None,
                                    secondary_metadata_general=None,
                                    primary_graph_offline_figure=None,
                                    secondary_graph_offline_figure=None,
                                    decimation_button_style=None,
                                    slider_fps_style=None,
                                    slider_speed_style=None,
                                    slider_speed_value=None,
                                    input_speed_value=None,
                                    video_modal_is_open=None):
    """
    Modify list of callbacks for main ui parameters:
    -----------
        callbacks_list_to_modify : The list of main ui callbacks to modify.
        slider_value : The value of the slider.
        frame_input_number : The current frame number.
        slider_min_value : The minimal value of the slider.
        slider_max_value : The maximal value fo the slider.
        video_files_list_label : List of videos loaded.
        slider_marks_value : The marks for the slider (mid of the video for example).
        primary_metadata_general : The primary metadata component.
        secondary_metadata_general : The secondary metadata component.
        primary_graph_offline_figure : The primary offline figure.
        secondary_graph_offline_figure : The secondary offline figure.
    """
    if slider_value is not None:
        callbacks_list_to_modify[OutputCallbacksIdx.SLIDER_VALUE_IDX.value] = slider_value
    if frame_input_number_value is not None:
        callbacks_list_to_modify[OutputCallbacksIdx.FRAME_INPUT_NUMBER_VALUE_IDX.value] = frame_input_number_value
    if slider_min_value is not None:
        callbacks_list_to_modify[OutputCallbacksIdx.SLIDER_MIN_VALUE_IDX.value] = slider_min_value
    if slider_max_value is not None:
        callbacks_list_to_modify[OutputCallbacksIdx.SLIDER_MAX_VALUE_IDX.value] = slider_max_value
    if video_files_list_label is not None:
        callbacks_list_to_modify[OutputCallbacksIdx.VIDEO_FILES_LIST_LABEL_IDX.value] = video_files_list_label
    if settings_file is not None:
        callbacks_list_to_modify[OutputCallbacksIdx.SETTINGS_FILE.value] = settings_file
    if slider_marks_value is not None:
        callbacks_list_to_modify[OutputCallbacksIdx.SLIDER_MARKS_VALUE_IDX.value] = slider_marks_value
    if slider_fps_value is not None:
        callbacks_list_to_modify[OutputCallbacksIdx.SLIDER_FPS_VALUE_IDX.value] = slider_fps_value
    if fps_input_value is not None:
        callbacks_list_to_modify[OutputCallbacksIdx.FPS_INPUT_VALUE_IDX.value] = fps_input_value
    if primary_metadata_general is not None:
        callbacks_list_to_modify[OutputCallbacksIdx.PRIMARY_METADATA_GENERAL_IDX.value] = primary_metadata_general
    if secondary_metadata_general is not None:
        callbacks_list_to_modify[OutputCallbacksIdx.SECONDARY_METADATA_GENERAL_IDX.value] = secondary_metadata_general
    if primary_graph_offline_figure is not None:
        callbacks_list_to_modify[OutputCallbacksIdx.PRIMARY_GRAPH_OFFLINE_FIGURE_IDX.value] = primary_graph_offline_figure
    if secondary_graph_offline_figure is not None:
        callbacks_list_to_modify[OutputCallbacksIdx.SECONDARY_GRAPH_OFFLINE_FIGURE_IDX.value] = secondary_graph_offline_figure
    if decimation_button_style is not None:
        callbacks_list_to_modify[OutputCallbacksIdx.DECIMATION_BUTTONS_STYLE_IDX.value] = decimation_button_style
    if slider_fps_style is not None:
        callbacks_list_to_modify[OutputCallbacksIdx.SLIDER_FPS_STYLE_IDX.value] = slider_fps_style
    if slider_speed_style is not None:
        callbacks_list_to_modify[OutputCallbacksIdx.SLIDER_SPEED_STYLE_IDX.value] = slider_speed_style
    if slider_speed_value is not None:
        callbacks_list_to_modify[OutputCallbacksIdx.SLIDER_SPEED_VALUE_IDX.value] = slider_speed_value
    if input_speed_value is not None:
        callbacks_list_to_modify[OutputCallbacksIdx.INPUT_SPEED_VALUE_IDX.value] = input_speed_value
    if video_modal_is_open is not None:
        callbacks_list_to_modify[OutputCallbacksIdx.VIDEO_MODAL_IS_OPEN_IDX.value] = video_modal_is_open


def prepare_player_output_callbacks(pause_button_n_clicks=dash.no_update,
                                    play_button_n_clicks=dash.no_update,
                                    play_button_is_disabled=dash.no_update,
                                    pause_button_is_disabled=dash.no_update,
                                    slider_interval_is_disabled=dash.no_update,
                                    forward_button_is_disabled=dash.no_update,
                                    back_button_is_disabled=dash.no_update,
                                    fast_forward_button_is_disabled=dash.no_update):
    """
    create list of callbacks for ui player
    @param pause_button_n_clicks:
    @param play_button_n_clicks:
    @param play_button_is_disabled:
    @param pause_button_is_disabled:
    @param slider_interval_is_disabled:
    @param forward_button_is_disabled:
    @param back_button_is_disabled:
    @param fast_forward_button_is_disabled:
    @return:
    """
    return [pause_button_n_clicks, play_button_n_clicks, play_button_is_disabled, pause_button_is_disabled, slider_interval_is_disabled,
            forward_button_is_disabled, back_button_is_disabled, fast_forward_button_is_disabled]


def prepare_browse_blob_output_callback(modal_is_open=dash.no_update,
                                        modal_type=dash.no_update,
                                        modal_input=dash.no_update,
                                        modal_title=dash.no_update,
                                        modal_label=dash.no_update):
    """
    :param modal_is_open:
    :param modal_type:
    :param modal_input:
    :param modal_title:
    :param modal_label:
    :return:
    """
    return [modal_is_open,  modal_type, modal_input,  modal_title, modal_label]


def prepare_jump_output_callback(recording_label_visible=dash.no_update,
                                 recording_table_div_visible=dash.no_update,
                                 table_data=dash.no_update,
                                 table_columns=dash.no_update,
                                 error_message_visible=False,
                                 error_message_msg=dash.no_update,
                                 jump_file_location=dash.no_update):
    """
    :param recording_label_visible:
    :param recording_table_div_visible:
    :param table_data:
    :param table_columns:
    :param error_message_visible:
    :param error_message_msg:
    :param jump_file_location:
    :return:
    """
    return [recording_label_visible, recording_table_div_visible, table_data, table_columns, error_message_visible, error_message_msg,
            jump_file_location]


def add_file_suffix(file_name, suffix):
    if file_name.endswith(f'.{suffix}'):
        file_name = file_name
    else:
        file_name = file_name + f'.{suffix}'
    return file_name


def get_index_from_list_by_condition(condition, indices_list: list, is_reversed: bool) -> int:
    if not is_reversed:
        return next((value for value in indices_list if condition(value)), -1)
    else:
        return next((indices_list[i] for i in range(len(indices_list) - 1, -1, -1) if condition(indices_list[i])), -1)
