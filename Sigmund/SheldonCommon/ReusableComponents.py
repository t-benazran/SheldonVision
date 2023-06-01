import re
import dash_bootstrap_components as dbc
from dash import dash_table, dcc, html
from pandas import DataFrame
import dash_mantine_components as dmc
from dash_iconify import DashIconify
#import dash_daq.ToggleSwitch

from SheldonCommon.Constants import TAB_ID_PREFIX, ALGO_TAB_DROP_DOWN
from SheldonCommon.styles import Styles

MATERIAlIZE_CSS = "https://cdnjs.cloudflare.com/ajax/libs/materialize/1.0.0/css/materialize.min.css"
BOOTSTRAP_ICONS = "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.9.1/font/bootstrap-icons.css"


def camel_case_to_space_delimited(camel_case_string):
    return re.sub(r'((?<=[a-z])[A-Z]|(?<!\A)[A-Z](?=[a-z]))', r' \1', camel_case_string)


def build_component(class_name, component=html.Div):
    def component_func(*args, className="", **kwargs):
        return component(*args, className=class_name + " " + className, **kwargs)

    return component_func


def Col(*args, width, **kwargs):
    class_name = f"col-md-{width}"
    return html.Div(*args, className=class_name, **kwargs)


def __create_single_slider(component_id, min_slider_range, max_slider_range, mid, disabled=False):
    return dcc.Slider(
        id=component_id,
        min=min_slider_range,
        max=max_slider_range,
        value=0,
        step=1,
        marks={i: {'label': str(i)} for i in [min_slider_range, mid, max_slider_range]},
        tooltip={"always_visible": False},
        disabled=disabled
    )


def __create_range_slider(component_id, min_slider_range, max_slider_range, mid, disabled=False):
    return dcc.RangeSlider(
        id=component_id,
        min=min_slider_range,
        max=max_slider_range,
        marks={i: str(i) for i in [min_slider_range, mid, max_slider_range]},
        tooltip={"always_visible": False},
        disabled=disabled
    )


def __create_pre_defined_slider(component_id: str, range_list: list[float], value: float, disabled: bool = False, step: int | None = 1,
                                included: bool = True, is_linear: bool = True, show_tooltip: bool = True) -> dcc.Slider:
    range_list = sorted(range_list)
    if not is_linear:
        min_slider_value = 0
        max_slider_value = len(range_list) - 1
        marks = {i: str(range_list[i]) for i in range(len(range_list))}
        set_value = range_list.index(value)
    else:
        min_slider_value = range_list[0]
        max_slider_value = range_list[-1]
        marks = {i: str(i) for i in range_list}
        set_value = value
    return dcc.Slider(
        id=component_id,
        min=min_slider_value,
        max=max_slider_value,
        marks=marks,
        tooltip={"always_visible": False} if show_tooltip else None,
        disabled=disabled,
        value=set_value,
        step=step,
        included=included
    )


def toggle_switch(component_id, value, size):
    return dash_daq.ToggleSwitch.ToggleSwitch(id=component_id, value=value, size=size)


def slider(component_id, input_range_id, min_slider_range, max_slider_range, label, is_range_slider=True, placeholder="Frame#",
           input_disabled=False, slider_disabled=False, is_predefined_slider=False, range=None, value=None, hidden=False, step=1,
           included=True, is_linear=True, show_tooltip=True):
    mid = int((min_slider_range + max_slider_range) / 2)
    if is_range_slider:
        slider = __create_range_slider(component_id, min_slider_range, max_slider_range, mid, slider_disabled)
    elif is_predefined_slider:
        slider = __create_pre_defined_slider(component_id, range, value, slider_disabled, step, included, is_linear,
                                             show_tooltip=show_tooltip)
    else:
        slider = __create_single_slider(component_id, min_slider_range, max_slider_range, mid, slider_disabled)

    return html.Div(
        [
            dbc.FormGroup(
                [
                    dbc.Label(label),
                    dbc.Input(
                        style={'width': '20%'},
                        id=input_range_id,
                        placeholder=placeholder,
                        type="string",
                        debounce=True,
                        disabled=input_disabled
                    ),
                ]),
            html.Br(),
            slider,
            dcc.Loading(
                id=f"loading-output-container-{component_id}",
                children=[
                    html.Div(id=f'output-container-{component_id}'),
                    html.Div(id=f'err-container-{component_id}', style={'color': 'red'}),
                ],
                type="dot", color="grey",
                style={"margin": "1rem auto", "width": "99%", "height": "20vh",
                       "text-align": "right", "font-size": "50px", "margin-left": "1%", "margin-right": "0",
                       "margin-top": "30%"}
            )
        ], id=f'slider-{component_id}', style={'display': 'none'} if hidden else {'display': 'block'}
    )


def custom_input(component_id, style, place_holder_text):
    return html.Div([
        dbc.Input(
            style=style,
            id=component_id,
            placeholder=place_holder_text,
            type="string",
            debounce=True
        )]
    )


def custom_button(component_id, label, width=''):
    return html.Div(
        [
            html.Button(label, id=component_id, n_clicks=0, className="btn btn-outline-primary",
                        style={'text-transform': 'none', 'width': width}),
        ]
    )


def custom_button_with_icon(component_id, label='', access_key='', is_disabled=False, icon_class_name='', button_class_name='',
                            icon_style={}, button_style={}, title=''):
    return html.Div(
        [
            html.Button([html.I(className=icon_class_name, style=icon_style), label], id=component_id,
                        accessKey=access_key, className=button_class_name, disabled=is_disabled,
                        style=button_style, title=title),
        ]
    )


def __create_drop_down_menu(component_id: str, values: list, separate_items: bool = False) -> list[dbc.DropdownMenuItem]:
    drop_down_values = []
    num_of_values = len(values)
    for indx, item in enumerate(values):
        drop_down_values.append(dbc.DropdownMenuItem(item, id=f'{component_id}-drop-down-{item.replace(" ", "-")}'))
        if separate_items and indx + 1 < num_of_values:
            drop_down_values.append(dbc.DropdownMenuItem(divider=True))
    return drop_down_values


def custom_button_with_icon_drop_down(component_id: str, label: str = '', access_key: str = '', is_disabled: bool = False,
                                      icon_class_name: str = '', button_class_name: str = '', icon_style: dict = {},
                                      button_style: dict = {}, title: str = '', values: list = [], drop_down_style: dict = {}):
    return html.Div(
        [
            Row([
                html.Button([html.I(className=icon_class_name, style=icon_style), label], id=component_id,
                            accessKey=access_key, className=button_class_name, disabled=is_disabled,
                            style=button_style, title=title),
                dbc.DropdownMenu(id=f'{component_id}-drop-down', children=__create_drop_down_menu(component_id, values, True),
                                 toggle_style=drop_down_style, right=True)
            ])
        ]
    )


def input_modal(component_id: str, title: str, label_text: str):
    return html.Div(
        [
            dbc.Modal(
                [
                    html.Div(dbc.ModalHeader(title), id=f'{component_id}-header'),
                    dbc.ModalBody(children=[
                        html.Div(html.Label(label_text), id=f'{component_id}-label'),
                        dbc.Input(id=f'{component_id}-input'),
                        html.Div(id=f'{component_id}-type', hidden=True, children='hello')
                    ]),
                    dbc.ModalFooter([
                        dbc.Button("OK", id=f'{component_id}-ok-button', className="ms-auto", n_clicks=0, style={'margin': '10px'}),
                        dbc.Button("Cancel", id=f'{component_id}-cancel-button', className="ms-auto", n_clicks=0)
                    ]),
                ],
                id=component_id,
                is_open=False,
                size='lg'
            ),
        ]
)


def icon_button(component_id, width='', icon='', button_name='', is_disabled=False, icon_width=30, icon_height=30):
    return html.Div(
        [
            dmc.Button(button_name, id=component_id,
                       leftIcon=[DashIconify(icon=icon, width=icon_width, height=icon_height),
                                 ], style={'text-transform': 'none', 'width': width},
                       disabled=is_disabled,
                       )])


def render_tabs(tab_id_prefix, tabs_name):
    tabs = []
    for tab_name in tabs_name:
        tabs.append(
            dcc.Tab(
                label=camel_case_to_space_delimited(tab_name),
                value=f'{tab_id_prefix}{tab_name}',
                className='nav-item',
                style=Styles.tab_style, selected_style=Styles.tab_selected_style
            )
        )
    return tabs


def drop_down(component_id, options, value=''):
    return html.Div([
        dcc.Dropdown(
            id=component_id,
            options=options,
            searchable=False,
            value=value
        ),
    ],
        style={"width": "30%"},
    )


def checklist(component_id, options):
    options_param = [{'label': label, 'value': key} for key, label in options.items()]
    return html.Div(dcc.Checklist(id=component_id, options=options_param, value=[0]))


def algo_tab_content(algo_tab_drop_down, drop_down_options, drop_down_value='', graph=None):
    return html.Div(
        [
            dbc.CardBody(children=[
                drop_down(algo_tab_drop_down, drop_down_options, drop_down_value),
                html.Div([graph])])
        ])


def tabs(drop_down_default_options, algo_graph_tab_content_id, final_reports_tab_name, component_id, args):
    return html.Div([
        dcc.Tabs(
            id=component_id,
            value=final_reports_tab_name,
            parent_className='nav nav-tabs',
            className='nav nav-tabs',
            children=render_tabs(TAB_ID_PREFIX, args),
        ),
        dcc.Loading(
            id=f"loading-{algo_graph_tab_content_id}",
            type="circle", color="grey",
            children=[
                html.Div(id=algo_graph_tab_content_id,
                         children=algo_tab_content(ALGO_TAB_DROP_DOWN, drop_down_default_options))
            ])
    ])


def collapse(component_id, data_frame: DataFrame = None):
    card_body = dbc.CardBody(
        dcc.Loading(
            id=f"loading-card-body-{component_id}",
            children=html.Div(children=[create_data_table(component_id, data_frame)],
                              id=f"card-body-{component_id}"),
            type="circle", color="grey",
        )
    )

    return dbc.Collapse(
        dbc.Card(
            children=[card_body]
        ),
        id=f"collapse-{component_id}",
        is_open=False,
        style={'text-transform': 'none'}
    )


def Interval(component_id, interval, disabled=True):
    return dcc.Interval(
        id=component_id,
        interval=interval,
        n_intervals=0,
        disabled=disabled
    ),


def drop_down_multiple(component_id, options, value=''):
    return html.Div([
        dcc.Dropdown(id=component_id,
                     options=options,
                     value=value,
                     multi=True,
                     placeholder="Select (leave blank to include all)",
                     style={'font-size': '13px', 'white-space': 'nowrap', 'text-overflow': 'ellipsis'}
                     )
    ],
        style={'width': '70%', 'margin-top': '5px'})


def create_data_table(component_id, data_frame, is_export=True):
    no_data_in_selection = html.Div(id=f'datatable-interactivity-{component_id}', children="No Data in selected range.")

    if data_frame is None:
        return no_data_in_selection

    if data_frame.size == 0:
        return no_data_in_selection

    columns = [{"name": i, "id": i} for i in data_frame.columns]
    data = data_frame.to_dict('records')

    return html.Div([
        dash_table.DataTable(
            id=f'datatable-interactivity-{component_id}',
            columns=columns,
            data=data,
            page_size=50,
            fixed_rows={'headers': True},
            style_table={'height': '400px', 'overflowY': 'auto', 'overflowX': 'auto', 'textAlign': 'left'},
            style_cell={'textAlign': 'left', 'minWidth': '140px', 'width': '180px'},
            export_format="csv" if is_export else "none",
        ),
        html.Div(id=f'datatable-interactivity-container{component_id}'),
    ])


def create_general_div_by_callback(component_id, data):
    return html.Div(id=f"{component_id}", children=data)


def create_data_div(component_id, data_frame):
    data = data_frame.to_dict('records')
    if len(data) == 1:
        return create_updating_data_table_by_callback(component_id=component_id, data_frame=data_frame, is_export=False)
    else:
        children = [html.Div(id=f"{x['Keys']}-G-Div", children=f'{x["Keys"]} - {x["Values"]}') for x in data]
        return html.Div(id=f"{component_id}Div", children=children)


def create_updating_editable_data_table_by_callback(component_id: str, data_frame: DataFrame, buttons_class: str,
                                                    input_style: dict[str, str], buttons_style: dict[str, str], is_export=True,
                                                    sorted_column='', is_hidden=False):
    columns = [{"name": i, "id": i, 'deletable': True, 'renamable': True} for i in sorted(data_frame.columns)]
    data = data_frame.to_dict('records')

    return html.Div(id=f"{component_id}Div", children=[
        html.Div([
            Row([custom_input(
                component_id=f'{component_id}-adding-rows-name',
                style=input_style,
                place_holder_text='Enter a column name...'
            ),
                custom_button(component_id=f'{component_id}-adding-rows-button', label='Add Column')])

        ], style={'height': 50}),

        dash_table.DataTable(
            id=f'{component_id}-adding-rows-table',
            columns=columns,
            data=data,
            page_size=50,
            fixed_rows={'headers': True},
            style_table={'minHeight': '50px', 'overflowY': 'auto', 'overflowX': 'auto', 'textAlign': 'left'},
            style_cell={'textAlign': 'left', 'minWidth': '140px', 'width': '180px'},
            export_format="csv" if is_export else "none",
            sort_by=[{'column_id': sorted_column, 'direction': 'asc'}],
            sort_action='native',
            editable=True,
            row_deletable=True
        ),
        html.Div(id=f'datatable-interactivity-container-{component_id}'),
        custom_button(component_id=f'{component_id}-editing-rows-button', label='Add Row')
    ], hidden=is_hidden)


def create_updating_data_table_by_callback(component_id, data_frame, is_export=True, sorted_column='', is_hidden=False):
    columns = [{"name": i, "id": i} for i in sorted(data_frame.columns)]
    data = data_frame.to_dict('records')

    return html.Div(id=f"{component_id}Div", children=[
        dash_table.DataTable(
            id=component_id,
            columns=columns,
            data=data,
            page_size=50,
            fixed_rows={'headers': True},
            style_table={'minHeight': '50px', 'overflowY': 'auto', 'overflowX': 'auto', 'textAlign': 'left'},
            style_cell={'textAlign': 'left', 'minWidth': '140px', 'width': '180px'},
            export_format="csv" if is_export else "none",
            sort_by=[{'column_id': sorted_column, 'direction': 'asc'}],
            sort_action='native',
        ),
        html.Div(id=f'datatable-interactivity-container-{component_id}'),
    ], hidden=is_hidden)


def create_notification(component_id_number: int, title: str, message: str, time_to_display: int | bool, base_color: str, style: str,
                        icon: str) -> dmc.Notification:
    """
    Creates user notification pop up
    :param component_id_number: id of the specific notification
    :param title: title of the notification
    :param message: notifications inner message
    :param time_to_display: hoe long should the message be displayed in ms - False for no auto closing
    :param base_color: color of the icon and frame
    :param style: css style, used for background color
    :param icon: DashIconify color name
    :return: dmc.Notification
    """
    return dmc.Notification(
                title=title,
                id=f"simple-notify_{component_id_number}",
                action="show",
                message=message,
                autoClose=time_to_display,
                color=base_color,
                style=style,
                icon=DashIconify(icon=icon),)


def generate_drop_down_options(options, first_option=None, is_sort=False):
    """ Return the Plots types for Drop Down selection
    :param drop_down_options: List of options that shown on drop down at the plot
    """
    if is_sort:
        try:
            options = sorted(options)
        except Exception as e:
            print(e)

    drop_down_options = [{'label': item, 'value': item} for item in options]
    first_option = [{'label': first_option, 'value': first_option}] if first_option is not None else []
    return first_option + drop_down_options


Row = build_component("row")
Card = build_component("card border-primary mb-12")
CardTitle = build_component("card-title")
CardContent = build_component("p-3 mb-3 bg-opacity-25 text-dark")
CardContentNoPadding = build_component("bg-opacity-25 text-dark")
CardAction = build_component("card-action")
