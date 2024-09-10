import asyncio
import aiohttp
import time
from enum import Enum
from uuid import UUID


"""
Script to export all Power BI reports within a specified workspace in PNG format.

This script retrieves a list of reports from the Power BI workspace (specified by `group_id`) 
and iteratively exports each report as a PNG file using the Power BI REST API. The exported 
files are saved locally with unique filenames. The script handles:
- Authentication with Azure AD.
- Fetching reports from the workspace.
- Polling to wait for the export to complete.

Usage:
- Ensure you have provided the correct `group_id` (workspace ID).
- Run the script to automatically download all reports in the workspace.

Dependencies:
- asyncio
- Your custom `exporter` module with the `export_power_bi_report` function.

"""

class FileFormat(Enum):
    PDF = "PDF"
    PNG = "PNG"

class ExportState(Enum): 
    SUCCEEDED = "Succeeded"
    FAILED = "Failed"

class PowerBIExporter:
    def __init__(self, access_token, base_url="https://api.powerbi.com/v1.0/myorg"):
        self.access_token = access_token
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

    async def list_reports(self, group_id: UUID):
        url = f"{self.base_url}/groups/{group_id}/reports"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers) as response:
                response.raise_for_status()
                result = await response.json()
                return result.get('value', [])

    async def export_power_bi_report(self, report_id: UUID, group_id: UUID, file_format: FileFormat, 
                                     polling_timeout_minutes: int, page_names: list = None, url_filter: str = None):
        max_retries = 3
        for attempt in range(max_retries):
            try:
                export_id = await self.post_export_request(report_id, group_id, file_format, page_names, url_filter)
                export = await self.poll_export_request(report_id, group_id, export_id, polling_timeout_minutes)

                if export is None or export['status'] == ExportState.FAILED.value:
                    if 'retryAfter' in export:
                        await asyncio.sleep(export['retryAfter'])
                        continue
                    return None

                if export['status'] == ExportState.SUCCEEDED.value:
                    return await self.get_exported_file(report_id, group_id, export)

            except Exception as e:
                print(f"Error during export attempt {attempt + 1}: {str(e)}")
                if attempt == max_retries - 1:
                    raise

        return None

    async def post_export_request(self, report_id, group_id, file_format, page_names, url_filter):
        url = f"{self.base_url}/groups/{group_id}/reports/{report_id}/ExportTo"
        data = {
            "format": file_format.value,  # Ensure this is passed correctly
        }
        print(url)

        if page_names:
            data["pageNames"] = page_names
        if url_filter:
            data["urlFilter"] = url_filter

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=self.headers, json=data) as response:
                response.raise_for_status()
                result = await response.json()
                return result['id']

    async def poll_export_request(self, report_id, group_id, export_id, polling_timeout_minutes):
        url = f"{self.base_url}/groups/{group_id}/reports/{report_id}/exports/{export_id}"
        start_time = time.time()
        while time.time() - start_time < polling_timeout_minutes * 60:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers) as response:
                    response.raise_for_status()
                    result = await response.json()
                    if result['status'] in [ExportState.SUCCEEDED.value, ExportState.FAILED.value]:
                        return result
            await asyncio.sleep(5)
        return None

    async def get_exported_file(self, report_id, group_id, export):
        url = export['resourceLocation']
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers) as response:
                response.raise_for_status()
                content = await response.read()
                return {
                    'content': content,
                    'filename': f"{export['reportName']}.{export['resourceFileExtension']}"
                }

async def main():
    access_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsIng1dCI6IktRMnRBY3JFN2xCYVZWR0JtYzVGb2JnZEpvNCIsImtpZCI6IktRMnRBY3JFN2xCYVZWR0JtYzVGb2JnZEpvNCJ9.eyJhdWQiOiJodHRwczovL2FuYWx5c2lzLndpbmRvd3MubmV0L3Bvd2VyYmkvYXBpIiwiaXNzIjoiaHR0cHM6Ly9zdHMud2luZG93cy5uZXQvYThlNWQ1NzEtNDNlOC00YzNjLTk2YmUtMzQ0MTU2Y2Y2ODg3LyIsImlhdCI6MTcyNDA4Mzc3MywibmJmIjoxNzI0MDgzNzczLCJleHAiOjE3MjQwODgwOTEsImFjY3QiOjAsImFjciI6IjEiLCJhaW8iOiJBWlFBYS84WEFBQUF5dnVSUmlTSFd3WXBQNGxON2RLYXp3TG1RMk1BRHlQSnE5QWVqM0VtejBEUUdKMEg2U0xqRHZqaEMxVUg4YmxtaThXd1JEY1ZYY0lPMEpLRHNhd0g4TjBuV2tXamtFbW15WmE2S3BmT2QzdmozaS8yZE5Ka0Nib1VtN3I2U0FsNmhkYWdsekxsMENUeGZvU1dXcnZReFdFejBYa3B3QU5LRUM1ZGlET1p4bUFsRzMwaXhBM2gxRU5vNG5walBzM2YiLCJhbXIiOlsicnNhIiwibWZhIl0sImFwcGlkIjoiODcxYzAxMGYtNWU2MS00ZmIxLTgzYWMtOTg2MTBhN2U5MTEwIiwiYXBwaWRhY3IiOiIwIiwiZGV2aWNlaWQiOiI0YWRiMDVhYS00YWQ5LTQ2MjAtYTAzZi0zYjYxOWIxM2FkYzciLCJmYW1pbHlfbmFtZSI6IkluYW1kYXIiLCJnaXZlbl9uYW1lIjoiSnVuZWQgU2hhYmJpciIsImlkdHlwIjoidXNlciIsImlwYWRkciI6IjI0MDk6NDBjMjoyMDRiOmM2NTQ6MWM1ZDplODA5OmJmM2Q6ZGE3YSIsIm5hbWUiOiJKdW5lZCBTaGFiYmlyIEluYW1kYXIiLCJvaWQiOiJmNWFlNmVhOC1kODY3LTQ5NDktYmRjMS1lOGE5ODFiMTVmMjgiLCJvbnByZW1fc2lkIjoiUy0xLTUtMjEtMTI4MDAwNjAyNi0yODU0MDk1ODc5LTM2MDI2MDA3NzctMjU5NjkiLCJwdWlkIjoiMTAwMzIwMDI2QjUxRkM1OSIsInJoIjoiMC5BUklBY2RYbHFPaERQRXlXdmpSQlZzOW9od2tBQUFBQUFBQUF3QUFBQUFBQUFBRFdBSGcuIiwic2NwIjoidXNlcl9pbXBlcnNvbmF0aW9uIiwic2lnbmluX3N0YXRlIjpbImR2Y19tbmdkIiwiZHZjX2NtcCIsImttc2kiXSwic3ViIjoiT2FaSFVtVGZod21UQnhCSnItZm5KeTIyRGZ5d1dEcVppUDZNOWJfa1pRUSIsInRpZCI6ImE4ZTVkNTcxLTQzZTgtNGMzYy05NmJlLTM0NDE1NmNmNjg4NyIsInVuaXF1ZV9uYW1lIjoiSnVuZWQuaW5hbWRhckBpbGluay1zeXN0ZW1zLmNvbSIsInVwbiI6Ikp1bmVkLmluYW1kYXJAaWxpbmstc3lzdGVtcy5jb20iLCJ1dGkiOiI5LTZJbDdwRkRVdTVFTUhtTThRSUFBIiwidmVyIjoiMS4wIiwid2lkcyI6WyJiNzlmYmY0ZC0zZWY5LTQ2ODktODE0My03NmIxOTRlODU1MDkiXSwieG1zX2lkcmVsIjoiMjQgMSJ9.pdA4koYrZfCh0HV_VrbeHY0cVlBD7V9kCneMqS1djf5PcHFpg2K-AKBvqnCDKNg8DCqnN4-FR4pyUQ74YFP3uprGPG88MWOI9h-SnNS_Rt2lqEzLgHtbUQR-IlDBcdnNI7GysWEyMCg_r37qb8SC0VKkOjIEjBwqF9ua-24D_MvPzbaOP9Gda6DHuZCOGMVjzAq3cBy2P3oZ3JO06SA0f2X5lnDWW0uQ3zHp0XBhcB1wsKD0Lzgq22viVOgm5KrObkeI_KGbxdT7c5QqTQfLSW8DefxmwP1WP5-AysLpYR8c7pzRyIxfHEbri8nMrKu5w2D3AtG_3lAV-fXHu4389A"
    group_id = UUID("1db5655f-0a1b-4109-9209-91909dbd0b08")
    
    exporter = PowerBIExporter(access_token)
    
    # List reports
    reports = await exporter.list_reports(group_id)
    print("Available reports:")
    for report in reports:
        print(f"ID: {report['id']}, Name: {report['name']}")
    
    if reports:
        for report in reports:
            report_id = UUID(report['id'])  # Get the report ID for each report
            print(f"Exporting report: {report['name']} (ID: {report_id})")

            result = await exporter.export_power_bi_report(
                report_id, 
                group_id, 
                FileFormat.PNG, 
                polling_timeout_minutes=10
            )

            if result:
                with open(result['filename'], 'wb') as f:
                    f.write(result['content'])
                print(f"Report exported successfully as {result['filename']}")
            else:
                print(f"Failed to export report: {report['name']}")
                
            break
    else:
        print("No reports found")
    
if __name__ == "__main__":
     asyncio.run(main())

