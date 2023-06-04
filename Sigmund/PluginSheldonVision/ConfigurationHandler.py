import os
import json
import logging
from typing import Union
import PluginSheldonVision.Constants as SheldonVisionConstants
from PluginSheldonVision.Helpers import init_logger_settings
from PluginSheldonVision.NotificationsHandler import Notification


class ConfigurationHandler:
    def __init__(self, configuration_file_path: str, notifications: Notification = None, perform_validation: bool = True,
                 log_file_path: str = ""):
        self.perform_validation = perform_validation
        self.notifications = notifications
        self.__configuration_file_path = configuration_file_path
        self.__configurations = self.__read_configurations(configuration_file_path)
        if log_file_path:
            init_logger_settings(log_file_path, logging)

    @property
    def is_ok(self) -> bool:
        return self.__configurations != {}

    @property
    def configuration_file_path(self) -> str:
        return self.__configuration_file_path

    def get_item(self, item_name: str, section: str = None) -> Union[str, None]:
        ret_value = None
        if section:
            if section in self.__configurations and item_name in self.__configurations[section]:
                ret_value = self.__configurations[section][item_name]
        else:
            if item_name in self.__configurations:
                ret_value = self.__configurations[item_name]
        return ret_value

    def __validate_specific_config_item(self, config_data: dict, item_name: str, section: str = None):
        try:
            section_to_validate = config_data[section] if section else config_data
        except KeyError:
            logging.error(SheldonVisionConstants.ERROR_FORMAT.format(f'Section is not defined in configuration file: {section}, '
                                                                     f'tested for {item_name}'))
            if self.notifications:
                self.notifications.notify_warning(title='Config Handler',
                                                  body=f'Section is not defined in configuration file: {section}, tested for {item_name}')
        else:
            if item_name not in section_to_validate:
                section_str = f'{section} -> ' if section else ''
                logging.error(SheldonVisionConstants.ERROR_FORMAT.format(f'Item is not defined in configuration file: '
                                                                         f'{section_str}{item_name}'))
                if self.notifications:
                    self.notifications.notify_warning(title='Config Handler',
                                                      body=f'Item is not defined in configuration file: {section_str}{item_name}')

    def __validate_configurations(self, config_data):
        self.__validate_specific_config_item(config_data, SheldonVisionConstants.CONFIG_VIDEO_FILE_PATH)
        self.__validate_specific_config_item(config_data, SheldonVisionConstants.CONFIG_DEBUG_FILE_PATH)
        self.__validate_specific_config_item(config_data, SheldonVisionConstants.CONFIG_FPS)
        self.__validate_specific_config_item(config_data, SheldonVisionConstants.CONFIG_METADATA_FILE_PATH,
                                             SheldonVisionConstants.CONFIG_PRIMARY_SECTION)
        self.__validate_specific_config_item(config_data, SheldonVisionConstants.CONFIG_LAYERS_LIST,
                                             SheldonVisionConstants.CONFIG_PRIMARY_SECTION)
        self.__validate_specific_config_item(config_data, SheldonVisionConstants.CONFIG_METADATA_FILE_PATH,
                                             SheldonVisionConstants.CONFIG_SECONDARY_SECTION)
        self.__validate_specific_config_item(config_data, SheldonVisionConstants.CONFIG_LAYERS_LIST,
                                             SheldonVisionConstants.CONFIG_SECONDARY_SECTION)

    def __read_configurations(self, configurations_file: str) -> Union[dict, None]:
        if configurations_file and os.path.exists(configurations_file):
            try:
                with open(configurations_file, 'r') as json_file:
                    config = json.loads(json_file.read())
                    if self.perform_validation:
                        self.__validate_configurations(config)
                    return config
            except Exception as ex:
                logging.error(SheldonVisionConstants.ERROR_FORMAT.format(f'Failed to load configurations\n{ex}'))
                if self.notifications:
                    self.notifications.notify_error(title='Config Handler', body=f'Failed to load configurations, see logs for more details')
        if configurations_file and not os.path.exists(configurations_file):
            logging.error(SheldonVisionConstants.ERROR_FORMAT.format(f'Configurations file not exist - {configurations_file}'))
            if self.notifications:
                self.notifications.notify_error(title='Config Handler', body=f'Configurations file not exist - {configurations_file}')
        return {}
