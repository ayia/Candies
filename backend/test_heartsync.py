"""Test Heartsync/Adult API"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from gradio_client import Client

print("Connecting to Heartsync/Adult...")
client = Client("Heartsync/Adult")

print("\n=== API ENDPOINTS ===")
api_info = client.view_api(return_format='dict')
if api_info:
    for endpoint_name, endpoint_info in api_info.items():
        print(f"\nEndpoint: {endpoint_name}")
        print(f"  Info: {endpoint_info}")
