# type: ignore
# project_ui.py
"""
This module defines the ProjectUI class, responsible for rendering the user interface
and handling user interactions within the PyWebIO application.
It integrates with the Meraki API utilities and project-specific business logic.
"""
from pywebio.output import toast, use_scope, put_buttons, put_markdown, put_text
from meraki_tools.my_logging import get_logger
from project_logic import ProjectLogic  # Import the new ProjectLogic class # type: ignore
from meraki_tools.meraki_api_utils import MerakiAPIWrapper
from logging import Logger # Import Logger for type hinting

# Initialize a module-level logger.
logger: Logger = get_logger()

class ProjectUI:
    """
    Manages the user interface and interaction flow for the application.

    This class handles displaying menus, processing user actions, and
    integrating with the Meraki API through `MerakiAPIWrapper` and
    application-specific logic via `ProjectLogic`.
    """
    _api_utils: MerakiAPIWrapper
    _project_logic: ProjectLogic
    logger: Logger
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

        # Although type hints suggest _api_utils is always MerakiAPIWrapper,
        # this check adds robustness in case of unexpected state.
        if self._api_utils is None:
            error_message = "API_Utils instance is not available. Please ensure it was set during ProjectUI initialization."
            logger.error(error_message)
            raise ValueError(error_message)

        try:
            with use_scope(self.app_scope_name, clear=True):
                # Display the currently selected organization's name and ID.
                put_markdown(f"### Organization: {self._api_utils.get_organization_name()} (id: {self._api_utils.get_organization_id()})")
                logger.info(f"Displaying main menu for organization: {self._api_utils.get_organization_name()} (id: {self._api_utils.get_organization_id()})")
                
                # Render buttons for main menu actions.
                put_buttons(
                    [
                        {"label": "Identity", "value": "identity"},
                        {"label": "Option 2", "value": "opt_2"},
                        {"label": "Option 3", "value": "opt_3"},
                    ],
                    onclick=self.handle_main_menu_action,
                )
        except Exception as e:
            logger.exception(f"An unexpected error occurred in app_main_menu: {e}")
            toast(f"An unexpected error occurred: {e}", color="error", duration=0)

    def handle_main_menu_action(self, action: str) -> None:
        """
        Handles actions triggered from the main menu buttons.

        Args:
            action: A string representing the value of the button clicked (e.g., "identity", "opt_2").
        """
        logger.info(f"Handling main menu action: {action}")
        try:
            if action == "identity":
                # Execute project logic for identity and display the result.
                identity: str = self._project_logic.example_function() # Assuming example_function returns a string
                self.display(identity)
            elif action == "opt_2":
                # Placeholder for future functionality related to Option 2.
                pass
            elif action == "opt_3":
                # Placeholder for future functionality related to Option 3.
                pass
        except Exception as e:
            logger.exception(f"An unexpected error occurred in handle_main_menu_action for action '{action}': {e}")
            toast(f"An unexpected error occurred: {e}", color="error", duration=0)

    def display(self, identity: str) -> None:
        """
        Displays the provided identity information within the application scope.

        Args:
            identity: The string content to be displayed.
        """
        with use_scope(self.app_scope_name, clear=True):
            put_text(identity)