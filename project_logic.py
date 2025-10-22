# type: ignore
# project_logic.py
"""
This module contains the core business logic for the application,
encapsulated in the ProjectLogic class. It interacts with the Meraki API
through the MerakiAPIWrapper to perform specific operations.
"""
import meraki
from meraki_tools.my_logging import get_logger
from meraki_tools.meraki_api_utils import MerakiAPIWrapper
from logging import Logger # Import Logger for type hinting
from typing import Any, Dict, List, Tuple, Optional # Import types for better type hinting, added Optional
from datetime import datetime, timedelta # Import for date/time calculations in new functions

# Initialize a module-level logger.
logger: Logger = get_logger()

class ProjectLogic:
    """
    Encapsulates the business logic for the application.

    This class provides methods to interact with the Meraki API
    and perform specific operations based on the application's requirements.
    It uses an instance of MerakiAPIWrapper for all API communications.
    """
    _api_utils: MerakiAPIWrapper
    logger: Logger

    def __init__(self, api_utils: MerakiAPIWrapper) -> None:
        """
        Initializes the ProjectLogic class with a MerakiAPIWrapper instance.

        Args:
            api_utils: An instance of MerakiAPIWrapper for Meraki API interactions.
        """
        self._api_utils = api_utils
        self.logger = get_logger()
        self.logger.info("ProjectLogic initialized with API_Utils instance.")

    def get_unique_product_types(self) -> List[str]:
        """
        Retrieves a list of unique product types from all networks in the organization.
        This is used to populate dropdowns for product-specific selections.

        Returns:
            A sorted list of unique product type strings (e.g., ['wireless', 'appliance']).
        """
        unique_product_types: Set[str] = set()
        try:
            networks = self._api_utils.list_networks()
            for network in networks:
                if 'productTypes' in network and isinstance(network['productTypes'], list):
                    for product_type in network['productTypes']:
                        unique_product_types.add(product_type)
        except Exception as e:
            logger.error(f"Error fetching unique product types: {e}", exc_info=True)
            # In a real application, you might want to return a default list
            # or raise the exception depending on how critical this data is.
            return [] # Return an empty list on error

        return sorted(list(unique_product_types))
    
    def get_filtered_event_types(self, product_type: str, event_category: Optional[str] = None) -> Tuple[List[str], List[Dict[str, Any]]]:
        """
        Fetches unique event types for networks matching a product type and optionally filters them by category.

        Args:
            product_type: The product type to filter networks (e.g., 'wireless').
            event_category: Optional. The event category to filter event types (e.g., 'AutoRF').
                            If None, all unique event types across all categories will be returned.

        Returns:
            A tuple: (sorted list of event type strings, list of networks matching product_type).
        """
        dashboard: meraki.DashboardAPI | None = self._api_utils.get_dashboard()
        if not dashboard:
            self.logger.error("Could not obtain Meraki Dashboard API object in ProjectLogic for get_filtered_event_types.")
            return [], []

        self.logger.info(f"Fetching all networks and filtering by product type '{product_type}'...")
        all_networks: List[Dict[str, Any]] = []
        try:
            all_networks = self._api_utils.list_networks(filter_product_type=[product_type])
        except meraki.APIError as e:
            self.logger.error(f"Meraki API Error fetching all networks: {e}")
            return [], []
        except Exception as e:
            self.logger.exception(f"An unexpected error occurred while fetching all networks: {e}")
            return [], []

        if not all_networks:
            self.logger.warning("No networks found using _api_utils.list_networks().")
            return [], []

        if not all_networks:
            self.logger.warning(f"No networks found matching product type '{product_type}'.")
            return [], []

        unique_event_types_set = set()
        for net in all_networks:
            network_id = net.get('id')
            network_name = net.get('name', 'Unknown')
            if not network_id:
                self.logger.warning(f"Skipping network with missing ID: {network_name}")
                continue
            try:
                event_types_for_net = dashboard.networks.getNetworkEventsEventTypes(
                    network_id
                )
                for event in event_types_for_net:
                    event_tuple = (event.get('category'), event.get('type'), event.get('description'))
                    unique_event_types_set.add(event_tuple)
            except meraki.APIError as e:
                self.logger.error(f"Error fetching event types for network {network_name} ({network_id}): {e}")
                continue
            except Exception as e:
                self.logger.exception(f"An unexpected error occurred while fetching event types for network {network_name} ({network_id}): {e}")
                continue

        all_unique_event_definitions: List[Dict[str, str]] = []
        for event_tuple in unique_event_types_set:
            all_unique_event_definitions.append({
                "category": event_tuple[0] if event_tuple[0] is not None else "Unknown",
                "type": event_tuple[1] if event_tuple[1] is not None else "Unknown",
                "description": event_tuple[2] if event_tuple[2] is not None else ""
            })

        # Sort the list of dictionaries by the 'category' key
        all_unique_event_definitions_sorted = sorted(all_unique_event_definitions, key=lambda x: str(x.get('category', '')))
                # Sort the list of dictionaries by the 'category' key, then by 'type'
        all_unique_event_definitions_sorted = sorted(
            all_unique_event_definitions, 
            key=lambda x: (str(x.get('category', '')), str(x.get('type', '')))
        )

        # Apply category filter if specified
        if event_category:
            filtered_definitions = [
                event_def for event_def in all_unique_event_definitions_sorted
                if event_def.get('category') == event_category
            ]
            self.logger.info(f"Found {len(filtered_definitions)} '{event_category}' event definitions for product type '{product_type}'.")
            return filtered_definitions
        else:
            self.logger.info(f"Found {len(all_unique_event_definitions_sorted)} unique event definitions across all categories for product type '{product_type}'.")
            return all_unique_event_definitions_sorted

    def get_network_event_counts(self, product_type: str, selected_event_types: List[str], days_lookback: int) -> Dict[str, Dict[str, Dict[str, int]]]:
        """
        Fetches events for specified networks and event types, then counts them daily.
        Implements manual pagination using 'endingBefore'.

        Args:
            networks_list: A list of network dictionaries (from get_filtered_event_types).
            product_type: The product type to filter events (e.g., 'wireless').
            selected_event_types: A list of event type strings to search for.
            days_lookback: The number of days to look back for events.

        Returns:
            A dictionary: {network_id: {date_str: {event_type: count}}}.
        """
        dashboard: meraki.DashboardAPI | None = self._api_utils.get_dashboard()
        if not dashboard:
            self.logger.error("Could not obtain Meraki Dashboard API object in ProjectLogic for get_network_event_counts.")
            return {}

        if not selected_event_types:
            self.logger.warning("No event types provided for search. Returning empty counts.")
            return {}

        end_time = datetime.now()
        start_time = end_time - timedelta(days=days_lookback)
        occurred_after_str = start_time.isoformat(timespec='seconds') + 'Z'
        # Convert to datetime object for comparison in pagination
        occurred_after_dt = datetime.fromisoformat(occurred_after_str.replace('Z', '+00:00'))

        network_event_counts: Dict[str, Dict[str, Dict[str, int]]] = {}
        self.logger.info(f"Collecting events for the last {days_lookback} days (since {occurred_after_str})...")
        networks_list = self._api_utils.list_networks(filter_product_type=[product_type])
        for net in networks_list:
            network_id = net.get('id')
            network_name = net.get('name', 'Unknown')
            if not network_id:
                self.logger.warning(f"Skipping network with missing ID: {network_name}")
                continue

            self.logger.info(f"  Fetching events for network: {network_name} ({network_id})...")

            all_network_events_for_current_net: List[Dict[str, Any]] = []
            ending_before_timestamp: str | None = None # Used for pagination
            loop_count = 0
            while True:
                try:
                    response_data: Dict[str, Any] = dashboard.networks.getNetworkEvents(
                        network_id,
                        productType=product_type,
                        includedEventTypes=selected_event_types,
                        occurredAfter=occurred_after_str,
                        endingBefore=ending_before_timestamp,
                        perPage=1000 # Max perPage to reduce API calls
                    )
                    loop_count += 1
                    self.logger.debug(f"    Loop count: {loop_count} for network {network_name}")
                    current_page_events = response_data.get('events', [])

                    if not current_page_events:
                        self.logger.debug(f"    No more events returned for network {network_name}. Breaking pagination.")
                        break # No more events were returned

                    all_network_events_for_current_net.extend(current_page_events)

                    page_start_at_str = response_data.get('pageStartAt')
                    if page_start_at_str:
                        page_start_at_dt = datetime.fromisoformat(page_start_at_str.replace('Z', '+00:00'))

                        if page_start_at_dt <= occurred_after_dt:
                            self.logger.debug(f"    Reached or passed occurredAfter ({occurred_after_dt}) for network {network_name}. Breaking pagination.")
                            break # Reached or passed the target start time
                    else:
                        # Fallback if pageStartAt is missing, assume last page if less than perPage
                        if len(current_page_events) < 1000:
                            self.logger.debug(f"    Less than 1000 events on page for network {network_name}. Assuming last page.")
                            break
                        # If pageStartAt is missing and we still got 1000 events, it's an unexpected scenario
                        # but we should probably break to avoid infinite loops if the API isn't providing `pageStartAt`
                        # and we're always getting full pages.
                        self.logger.warning(f"    'pageStartAt' missing in API response for network {network_name} and full page of events returned. Breaking to prevent infinite loop.")
                        break


                    ending_before_timestamp = page_start_at_str # For the next iteration

                except meraki.APIError as e:
                    self.logger.error(f"  Meraki API Error fetching events for network {network_name} ({network_id}): {e}")
                    break
                except Exception as e:
                    self.logger.exception(f"  An unexpected error occurred during pagination for network {network_name} ({network_id}): {e}")
                    break
            self.logger.debug(f"Finished fetching all pages for network {network_name}")
            network_events = all_network_events_for_current_net

            if network_events:
                self.logger.info(f"    Found {len(network_events)} events for network {network_name}.")
                network_event_counts[network_id] = {}
                for event in network_events:
                    if not isinstance(event, dict):
                        self.logger.warning(f"    Skipping malformed event (not a dictionary) in network {network_name}: {event}")
                        continue
                    if 'occurredAt' not in event or 'type' not in event:
                        self.logger.warning(f"    Skipping event with missing 'occurredAt' or 'type' in network {network_name}: {event}")
                        continue

                    try:
                        event_dt = datetime.fromisoformat(event['occurredAt'].replace('Z', '+00:00'))
                        event_date_str = event_dt.strftime('%Y-%m-%d')
                        event_type = event['type']

                        if event_date_str not in network_event_counts[network_id]:
                            network_event_counts[network_id][event_date_str] = {}

                        network_event_counts[network_id][event_date_str].setdefault(event_type, 0)
                        network_event_counts[network_id][event_date_str][event_type] += 1
                    except ValueError as e:
                        self.logger.error(f"    Error parsing 'occurredAt' for event in network {network_name}: {event.get('occurredAt')}. Error: {e}")
                        continue
                    except Exception as e:
                        self.logger.exception(f"    An unexpected error occurred while processing event in network {network_name}: {event}. Error: {e}")
                        continue
            else:
                self.logger.info(f"    No events found for network {network_name}.")

        return network_event_counts