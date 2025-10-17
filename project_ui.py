# type: ignore
# project_ui.py
"""
This module defines the ProjectUI class, responsible for rendering the user interface
and handling user interactions within the PyWebIO application.
It integrates with the Meraki API utilities and project-specific business logic.
"""
# Standard library imports
import logging
from typing import Any, Dict, List, Tuple, Optional
from datetime import datetime, timedelta

# Third-party library imports
import pandas as pd
from pyecharts import options as opts
from pyecharts.charts import Line, Page
from pywebio.output import toast, use_scope, put_buttons, put_markdown, put_text, put_html,put_loading
from pywebio.input import input_group, checkbox, actions, input as pywebio_input, select

# Project-specific imports
from meraki_tools.my_logging import get_logger
from project_logic import ProjectLogic  # type: ignore
from meraki_tools.meraki_api_utils import MerakiAPIWrapper

# Initialize a module-level logger.
logger: logging.Logger = get_logger()

class ProjectUI:
    """
    Manages the user interface and interaction flow for the application.

    This class handles displaying menus, processing user actions, and
    integrating with the Meraki API through `MerakiAPIWrapper` and
    application-specific logic via `ProjectLogic`.
    """
    _api_utils: MerakiAPIWrapper
    _project_logic: ProjectLogic
    logger: logging.Logger
    app_scope_name: str

    def __init__(self, api_utils: MerakiAPIWrapper, app_scope_name: str) -> None:
        """
        Initializes the ProjectUI class with API utilities and application scope.

        Args:
            api_utils: An instance of MerakiAPIWrapper for interacting with the Meraki API.
            app_scope_name: The name of the PyWebIO scope for UI rendering.
        """
        self._api_utils = api_utils
        self._project_logic = ProjectLogic(api_utils=api_utils)
        self.logger = get_logger()
        self.app_scope_name = app_scope_name
        self.logger.info("ProjectUI initialized with API_Utils and ProjectLogic instances.")

    def app_main_menu(self) -> None:
        """
        Displays the main navigation menu for the application.

        This menu is shown after an organization has been successfully selected
        and provides options to navigate to different functionalities like
        Identity management, Option 2, and Option 3.
        """
        logger.info("Entering app_main_menu function.")

        if self._api_utils is None:
            error_message = "API_Utils instance is not available. Please ensure it was set during ProjectUI initialization."
            logger.error(error_message)
            raise ValueError(error_message)

        try:
            with use_scope(self.app_scope_name, clear=True):
                # Display the currently selected organization's name and ID.
                put_markdown(f"### Organization: {self._api_utils.get_organization_name()} (id: {self._api_utils.get_organization_id()})")
                logger.info(f"Displaying main menu for organization: {self._api_utils.get_organization_name()} (id: {self._api_utils.get_organization_id()})")

                # Get unique product types from project logic
                # Assuming ProjectLogic has a method `get_unique_product_types`
                # If not implemented yet, a hardcoded list is used as a fallback.
                try:
                    product_types = self._project_logic.get_unique_product_types()
                except AttributeError:
                    logger.warning("`get_unique_product_types` not found in ProjectLogic. Using hardcoded list.")
                    product_types = ['wireless', 'appliance', 'switch', 'security'] # Fallback hardcoded list

                if not product_types:
                    put_text("No product types available for selection.")
                    return

                form_data = input_group(
                    "Select Product Type",
                    [
                        select(
                            name="product_type_selection",
                            label="Select a Product Type",
                            options=[(pt.capitalize(),pt) for pt in product_types],
                            required=True,
                            help_text="Choose a Meraki product type to view its network logs."
                        ),
                        actions(
                            name="action",
                            buttons=[
                                {"label": "View Logs", "value": "view_logs", "color": "primary"},
                            ]
                        )
                    ]
                )

                if form_data and form_data.get("action") == "view_logs":
                    selected_product_type = form_data.get("product_type_selection")
                    if selected_product_type:
                        self.handle_product_type_selection(selected_product_type)
                    else:
                        toast("Please select a product type.", color="warn")
                        self.app_main_menu() # Re-render main menu to allow selection again

        except Exception as e:
            logger.exception(f"An unexpected error occurred in app_main_menu: {e}")
            toast(f"An unexpected error occurred: {e}", color="error", duration=0)

    def handle_product_type_selection(self, product_type: str) -> None:
        """
        Handles the selection of a product type from the main menu dropdown.

        Args:
            product_type: The selected product type (e.g., "wireless", "appliance").
        """
        logger.info(f"Handling product type selection: {product_type}")
        try:
            self.display_network_event_selection_ui(product_type)
        except Exception as e:
            logger.exception(f"An unexpected error occurred in handle_product_type_selection for product type '{product_type}': {e}")
            toast(f"An unexpected error occurred: {e}", color="error", duration=0)

    def handle_main_menu_action(self, action: str) -> None:
        """
        Handles actions triggered from general navigation buttons (e.g., "Back to Main Menu").
        """
        logger.info(f"Handling main menu action: {action}")
        try:
            if action == "main_menu" or action == "networks_logs":
                # "networks_logs" action now also leads back to the main menu
                # to allow re-selection of product type.
                self.app_main_menu()
        except Exception as e:
            logger.exception(f"An unexpected error occurred in handle_main_menu_action for action '{action}': {e}")
            toast(f"An unexpected error occurred: {e}", color="error", duration=0)

    def display_network_event_selection_ui(self, product_type: str) -> None:
        """
        Displays a UI allowing the user to select multiple network event types,
        grouped by category, and specify a lookback period for analysis.
        The UI is tailored for the given product_type.
        """
        logger.info(f"Entering display_network_event_selection_ui function for product type: {product_type}.")

        with use_scope(self.app_scope_name, clear=True):
            all_event_definitions = self._project_logic.get_filtered_event_types(
                product_type=product_type,
                event_category=None # Get all categories for the selected product type
            )

            if not all_event_definitions:
                put_text(f"No network event types found for {product_type} networks or an error occurred.")
                put_buttons([{"label": "Back to Main Menu", "value": "main_menu"}], onclick=self.handle_main_menu_action)
                return

            categorized_events: Dict[str, List[Dict[str, str]]] = {}
            for event_def in all_event_definitions:
                print(event_def)
                category = event_def.get("category", "Uncategorized")
                if category not in categorized_events:
                    categorized_events[category] = []
                categorized_events[category].append(event_def)

            all_checkbox_options: List[Tuple[str, str]] = []

            sorted_categories = sorted(categorized_events.keys())
            for category in sorted_categories:
                sorted_events_in_category = sorted(categorized_events[category], key=lambda x: x.get("type", ""))
                for event_def in sorted_events_in_category:
                    event_type = event_def.get("type", "Unknown Type")
                    description = event_def.get("description", "No description available")
                    all_checkbox_options.append((f"[{category}] - {description}", event_type))

            form_data = input_group(
                f"{product_type.capitalize()} Event Type and Timeframe Selection",
                [
                    pywebio_input(
                        name="days_lookback",
                        label="Days to look back for events",
                        type="number",
                        value=7,
                        min=1,
                        max=90,
                        help_text="Enter the number of days to retrieve events for (max 90)."
                    ),
                    checkbox(
                        name="selected_event_types",
                        options=all_checkbox_options,
                        help_text="Check all event types you wish to analyze."
                    ),
                    actions(
                        name="action",
                        buttons=[
                            {"label": "Generate Report", "value": "generate_report", "color": "primary"},
                            {"label": "Back to Main Menu", "value": "main_menu", "color": "secondary"}
                        ]
                    )
                ]
            )

            if form_data:
                if form_data.get("action") == "generate_report":
                    selected_types: List[str] = form_data.get("selected_event_types", [])
                    days_lookback_raw = form_data.get("days_lookback")

                    if not selected_types:
                        toast("Please select at least one event type.", color="warn")
                        self.display_network_event_selection_ui(product_type)
                        return

                    try:
                        days_lookback: int = int(days_lookback_raw)
                        if not (1 <= days_lookback <= 90):
                            toast("Days lookback must be a number between 1 and 90.", color="warn")
                            self.display_network_event_selection_ui(product_type)
                            return
                    except (ValueError, TypeError):
                        toast("Invalid value for 'Days to look back'. Please enter a number.", color="warn")
                        self.display_network_event_selection_ui(product_type)
                        return

                    toast("Fetching event counts... This may take a moment.", color="info", duration=5)
                    with put_loading():
                        event_counts_data = self._project_logic.get_network_event_counts(
                        product_type=product_type,
                        selected_event_types=selected_types,
                        days_lookback=days_lookback
                    )

                    with use_scope(self.app_scope_name, clear=True):
                        self.display_event_counts_graph(product_type, event_counts_data, days_lookback, f"{product_type.capitalize()} Network Event Counts")
                        put_buttons([{"label": "Back to Event Selection", "value": "networks_logs"},
                                     {"label": "Back to Main Menu", "value": "main_menu"}],
                                    onclick=self.handle_main_menu_action)

                elif form_data.get("action") == "main_menu":
                    self.app_main_menu()
            else:
                put_text("No selection made or action cancelled.")
                put_buttons([{"label": "Back to Main Menu", "value": "main_menu"}], onclick=self.handle_main_menu_action)

    def display_event_counts_graph(self, product_type: str, event_counts_data: Dict[str, Dict[str, Dict[str, int]]], days_lookback: int, display_title: str) -> None:
        """
        Displays aggregated event counts in interactive line charts using PyEcharts and PyWebIO.
        Generates one chart per event type, with a separate line for each network and a total line.

        Args:
            product_type: The Meraki product type (e.g., 'wireless', 'appliance').
            event_counts_data: A dictionary where keys are network_ids, and values are
                                    dictionaries of daily counts.
            days_lookback: The number of days the data covers.
            display_title: The title for the overall graph section.
        """
        networks_list=self._api_utils.list_networks(filter_product_type=[product_type])
        network_names_map = {net['id']: net['name'] for net in networks_list}

        flat_data = []
        for network_id, daily_counts in event_counts_data.items():
            current_network_name = network_names_map.get(network_id, f"Unknown Network ({network_id})")
            for date_str, event_types_counts in daily_counts.items():
                for event_type, count in event_types_counts.items():
                    flat_data.append({
                        'Date': pd.to_datetime(date_str).date(),
                        'NetworkID': network_id,
                        'NetworkName': current_network_name,
                        'EventType': event_type,
                        'Count': count
                    })

        if not flat_data:
            put_markdown(f"## No events were collected for any network in the last {days_lookback} days.")
            return

        df_all_events = pd.DataFrame(flat_data)
        df_all_events = df_all_events.sort_values(by=['EventType', 'Date', 'NetworkName'])

        put_markdown(f"# {display_title} (Last {days_lookback} Days)")

        page = Page()

        today_date = datetime.now().date()
        start_date = today_date - timedelta(days=days_lookback - 1)
        full_date_range = pd.date_range(start=start_date, end=today_date, freq='D').date
        full_date_range_str = [d.strftime('%Y-%m-%d') for d in full_date_range]

        for target_event_type in sorted(df_all_events['EventType'].unique()):
            df_event_type = df_all_events[df_all_events['EventType'] == target_event_type]

            network_series_data_map = {}

            l = (
                Line(init_opts=opts.InitOpts(width="1400px", height="325px")) # Y-axis height halved
                .add_xaxis(xaxis_data=full_date_range_str)
                .set_global_opts(
                    title_opts=opts.TitleOpts(title=f"Daily '{target_event_type}' Events"),
                    tooltip_opts=opts.TooltipOpts(trigger="axis"),
                    yaxis_opts=opts.AxisOpts(
                        type_="value",
                        name="Event Count",
                        min_=0,
                        axislabel_opts=opts.LabelOpts(formatter="{value}")
                    ),
                    xaxis_opts=opts.AxisOpts(
                        type_="category",
                        name="Date",
                        boundary_gap=False,
                        axislabel_opts=opts.LabelOpts(rotate=45)
                    ),
                    legend_opts=opts.LegendOpts(is_show=True, pos_top="top", pos_left="right")
                )
            )

            for network_id, network_name in network_names_map.items():
                df_network_event_type = df_event_type[df_event_type['NetworkID'] == network_id].set_index('Date')

                series_data = df_network_event_type['Count'].reindex(full_date_range, fill_value=0).tolist()
                network_series_data_map[network_name] = series_data

                if any(count > 0 for count in series_data):
                    l.add_yaxis(
                        series_name=network_name,
                        y_axis=series_data,
                        linestyle_opts=opts.LineStyleOpts(width=2),
                        label_opts=opts.LabelOpts(is_show=False),
                        markpoint_opts=opts.MarkPointOpts(
                            data=[
                                opts.MarkPointItem(type_="max", name="Max Value"),
                                opts.MarkPointItem(type_="min", name="Min Value"),
                            ]
                        )
                    )

            total_event_counts_for_type = [0] * len(full_date_range)
            for i in range(len(full_date_range)):
                for network_name in network_series_data_map:
                    total_event_counts_for_type[i] += network_series_data_map[network_name][i]

            if any(count > 0 for count in total_event_counts_for_type):
                l.add_yaxis(
                    "Total Events",
                    total_event_counts_for_type,
                    linestyle_opts=opts.LineStyleOpts(width=4, type_="solid", opacity=0.8),
                    itemstyle_opts=opts.ItemStyleOpts(color="#FF0000"),
                    label_opts=opts.LabelOpts(is_show=False),
                    markpoint_opts=opts.MarkPointOpts(
                        data=[
                            opts.MarkPointItem(type_="max", name="Max Total"),
                            opts.MarkPointItem(type_="min", name="Min Total"),
                        ]
                    )
                )

            if l.options.get('series'):
                page.add(l)

        put_html(page.render_notebook())