# Power BI Reports Exporter

This script is designed to export all Power BI reports within a specified workspace to PNG format. It interacts with the Power BI REST API and handles report export, authentication with Azure AD, and polling to check the export status.

## Features
- Retrieves a list of all Power BI reports in a given workspace.
- Exports reports to PNG format.
- Handles polling to wait for export completion.
- Saves exported reports locally with unique filenames.

## Requirements
- Python 3.7 or higher
- `asyncio` and `aiohttp` libraries
- Power BI REST API access
- Azure AD authentication (OAuth2)

## Installation

1. Clone the repository:

    ```bash
    git clone https://github.com/yourusername/powerbi-exporter.git
    cd powerbi-exporter
    ```

2. Install the required dependencies:

    ```bash
    pip install aiohttp
    ```

## Usage

1. Ensure that you have a valid Azure AD token and the workspace (group) ID for the Power BI workspace.

2. Open the script and replace the `access_token` with your valid OAuth token:

    ```python
    access_token = "your_access_token_here"
    ```

3. Specify the `group_id` (workspace ID) where your Power BI reports are stored:

    ```python
    group_id = UUID("your_group_id_here")
    ```

4. Run the script:

    ```bash
    python export_powerbi_reports.py
    ```

The script will list all the reports in the specified Power BI workspace, then export each report as a PNG file. Exported reports will be saved in the same directory with the appropriate filenames.

## Example

This Python script allows exporting Power BI reports from a specified workspace into PNG format.

## Parameters

- **group_id**:  
  The unique ID of the Power BI workspace containing the reports.
  
- **report_id**:  
  The unique ID of the Power BI report to be exported.

- **FileFormat**:  
  The format of the exported file. This script exports reports in PNG format by default.

- **polling_timeout_minutes**:  
  The time (in minutes) that the script waits for the export operation to complete before timing out.

## Limitations

- The script currently only supports exporting reports in PNG format.
- Ensure that the access token used has the appropriate permissions for exporting reports.
- Make sure the access token is valid and not expired during the export process.

## Usage

1. Set the required parameters in the script.
2. Run the script to export the Power BI report.
