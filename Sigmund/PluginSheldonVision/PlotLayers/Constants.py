import os
from PluginSheldonVision.ConfigurationHandler import ConfigurationHandler
settings = ConfigurationHandler(os.path.abspath(os.path.join(__file__, '..', '..',  'settings.json')), perform_validation=False)

PLOT_LAYER_SECTION = 'PlotLayer'

LEFT = settings.get_item('LEFT', PLOT_LAYER_SECTION)
HEIGHT = settings.get_item('HEIGHT', PLOT_LAYER_SECTION)
WIDTH = settings.get_item('WIDTH', PLOT_LAYER_SECTION)
TOP = settings.get_item('TOP', PLOT_LAYER_SECTION)
BOUNDING_BOX = settings.get_item('BOUNDING_BOX', PLOT_LAYER_SECTION)
SOURCE = settings.get_item('SOURCE', PLOT_LAYER_SECTION)
MESSAGE = settings.get_item('MESSAGE', PLOT_LAYER_SECTION)
OBJECTS = settings.get_item('OBJECTS', PLOT_LAYER_SECTION)
