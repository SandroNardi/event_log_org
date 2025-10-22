# Network Event Log Organization Tool

A PyWebIO-based web application for analyzing Cisco Meraki network event logs over time. This tool allows users to select network types, specific log categories, and events, then displays daily event counts with interactive charts.

## Features

- **Interactive Web Interface**: Built with PyWebIO for easy-to-use web-based interface
- **Meraki API Integration**: Connects to Cisco Meraki Dashboard API to fetch network data
- **Event Analysis**: Analyze network events by product type, category, and specific event types
- **Time-based Reporting**: Generate reports for up to 90 days of historical data
- **Interactive Charts**: Visualize event trends using PyEcharts with line charts
- **Multi-step Selection**: Guided workflow for selecting product types, categories, and events
- **Real-time Logging**: Built-in logging system with real-time log display

## Prerequisites

- Python 3.8 or higher
- Cisco Meraki Dashboard API key
- Access to a Meraki organization with networks

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/SandroNardi/event_log_org.git
   cd event_log_org
   ```

2. **Create a virtual environment** (recommended):
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

### Environment Variables

Set the following environment variables:

```bash
# Windows (Command Prompt)
set MK_CSM_KEY=your_meraki_api_key_here
set MK_MAIN_ORG=your_organization_id_here

# Windows (PowerShell)
$env:MK_CSM_KEY="your_meraki_api_key_here"
$env:MK_MAIN_ORG="your_organization_id_here"

# macOS/Linux
export MK_CSM_KEY="your_meraki_api_key_here"
export MK_MAIN_ORG="your_organization_id_here"
```

**Required Environment Variables:**
- `MK_CSM_KEY`: Your Meraki Dashboard API key
- `MK_MAIN_ORG`: Your Meraki organization ID (optional - if not set, you'll be prompted to select an organization)

### Getting a Meraki API Key

1. Log in to your Meraki Dashboard
2. Navigate to **Organization** → **Settings** → **API access**
3. Generate a new API key
4. Copy the key and set it as the `MK_CSM_KEY` environment variable

## Usage

1. **Start the application**:
   ```bash
   python app.py
   ```

2. **Access the web interface**:
   - Open your web browser
   - Navigate to `http://localhost:8080`
   - The application will guide you through the setup process

3. **Application Workflow**:
   - **Organization Selection**: Choose your Meraki organization
   - **Product Type Selection**: Select the network product type (e.g., wireless, appliance)
   - **Category Selection**: Choose event categories to analyze
   - **Event Type Selection**: Select specific event types within those categories
   - **Timeframe Selection**: Set the number of days to look back (1-90 days)
   - **Report Generation**: View interactive charts showing event trends

## Project Structure

```
event_log_org/
├── app.py                 # Main application entry point
├── project_logic.py       # Core business logic
├── project_ui.py          # User interface components
├── about.py              # Application metadata
├── requirements.txt      # Python dependencies
├── meraki_tools/         # Reusable Meraki API utilities
│   ├── __init__.py
│   ├── meraki_api_utils.py  # Meraki API wrapper
│   ├── meraki_ui.py         # PyWebIO UI helpers
│   ├── my_logging.py        # Logging utilities
│   └── style.css           # Custom CSS styles
└── README.MD             # This file
```

## Dependencies

- **pywebio**: Web-based UI framework
- **meraki**: Cisco Meraki Dashboard API client
- **pandas**: Data manipulation and analysis
- **pyecharts**: Interactive chart generation
- **requests**: HTTP library for API requests

## API Requirements

- **Meraki Dashboard API**: Requires API access enabled in your Meraki organization
- **Network Events**: Requires networks with event logging enabled
- **Permissions**: API key must have read access to organizations and networks

## Troubleshooting

### Common Issues

1. **API Key Not Found**:
   - Ensure `MK_CSM_KEY` environment variable is set
   - Verify the API key is valid and has proper permissions

2. **No Networks Found**:
   - Check that your organization has networks
   - Verify the selected product type matches your network types

3. **No Events Found**:
   - Ensure event logging is enabled on your networks
   - Check that the selected time range contains events
   - Verify the selected event types exist for your networks

### Logs

The application includes built-in logging that displays in real-time within the web interface. Check the log panel for detailed information about API calls and any errors.

## Development

### Adding New Features

The application is modular with separate components for:
- **UI Logic**: `project_ui.py` - User interface and interaction handling
- **Business Logic**: `project_logic.py` - Data processing and API interactions
- **API Utilities**: `meraki_tools/` - Reusable Meraki API wrapper

### Customization

- **Styling**: Modify `meraki_tools/style.css` for custom appearance
- **Charts**: Extend chart functionality in `project_ui.py`
- **API Features**: Add new Meraki API methods in `meraki_tools/meraki_api_utils.py`

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.


## Author

**SandroN** - [GitHub](https://github.com/SandroNardi)

## Acknowledgments

- Cisco Meraki for the Dashboard API
- PyWebIO team for the excellent web framework
- PyEcharts for interactive charting capabilities
