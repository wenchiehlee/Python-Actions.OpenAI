import openai
import requests
import os
import time
import json
from dotenv import load_dotenv

# Load secret .env file
load_dotenv()

def get_openai_cost_and_usage(api_key, start_time, next_page=None):
    """
    Retrieves the cost and usage information for an OpenAI organization using an admin key.

    Parameters:
        api_key (str): The OpenAI admin API key for authentication.
        start_time (int): The start time for the cost query as a UNIX timestamp.
        next_page (str): The next page token for pagination (optional).

    Returns:
        dict: A dictionary containing cost and usage details.
    """
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    # OpenAI API Endpoint for costs
    cost_url = f"https://api.openai.com/v1/organization/costs?start_time={start_time}"
    if next_page:
        cost_url += f"&page={next_page}"

    try:
        # Fetch cost and usage information
        cost_response = requests.get(cost_url, headers=headers)
        cost_response.raise_for_status()
        cost_data = cost_response.json()

        return cost_data

    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error: {e}")
        print(f"Response Content: {e.response.json()}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"An error occurred while making the API request: {e}")
        return None

def process_and_display_cost_info(cost_info, total_usage):
    """
    Processes and displays cost and usage information in a readable format.

    Parameters:
        cost_info (dict): The cost and usage data retrieved from the API.
        total_usage (dict): A dictionary to accumulate total usage and cost.
    """
    if not cost_info or "data" not in cost_info:
        print("No valid cost data available.")
        return

    for bucket in cost_info.get("data", []):
        start_time = bucket.get("start_time", 0)
        end_time = bucket.get("end_time", 0)
        results = bucket.get("results", [])

        if results:
            print(f"Time Range: {time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(start_time))} to {time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(end_time))}")
            for result in results:
                print(f"  - Cost: ${result.get('amount', {}).get('value', 0):.6f} {result.get('amount', {}).get('currency', 'USD')}\n    Line Item: {result.get('line_item', 'N/A')}\n    Project ID: {result.get('project_id', 'N/A')}")
                # Accumulate total cost
                amount = result.get("amount", {}).get("value", 0)
                total_usage["total_cost"] += amount
                total_usage["entries"].append(result)

    if cost_info.get("has_more", False):
        print("More data is available. Fetching additional pages...")

def fetch_all_cost_data(api_key, start_time):
    """
    Fetches all cost and usage data by iterating through paginated results.

    Parameters:
        api_key (str): The OpenAI admin API key for authentication.
        start_time (int): The start time for the cost query as a UNIX timestamp.

    Returns:
        None
    """
    next_page = None
    total_usage = {"total_cost": 0, "entries": []}

    while True:
        cost_info = get_openai_cost_and_usage(api_key, start_time, next_page)
        if cost_info:
            process_and_display_cost_info(cost_info, total_usage)
            if cost_info.get("has_more"):
                next_page = cost_info.get("next_page")
            else:
                break
        else:
            print("Failed to retrieve cost and usage information.")
            break

    # Display summary of total usage and cost
    print("\nSummary of Usage for Last 30 Days:")
    print(f"Total Cost: ${total_usage['total_cost']:.6f} USD")
    print(f"Total Entries: {len(total_usage['entries'])}")

    # Save summary as JSON files
    with open("TotalCost.json", "w") as total_cost_file:
        json.dump({
            "schemaVersion": 1,
            "label": "Total Cost for Last 30 Days",
            "message": f"${total_usage['total_cost']:.6f} USD",
            "color": "blue"
        }, total_cost_file, indent=4)

    with open("TotalEntry.json", "w") as total_entry_file:
        json.dump({
            "schemaVersion": 1,
            "label": "Total Entries for Last 30 Days",
            "message": str(len(total_usage['entries'])),
            "color": "yellow"
        }, total_entry_file, indent=4)

    print("Summary JSON files created: TotalCost.json and TotalEntry.json")

if __name__ == "__main__":
    # Set your OpenAI API key here (or use environment variables)
    openai_admin_api_key = os.getenv("OPENAI_ADMIN_API_KEY") or "your_openai_admin_key_here"

    if openai_admin_api_key == "your_openai_admin_key_here":
        print("Please set your API key in the code or as an environment variable.")
    else:
        # Use the current time as the end time and query for the last 30 days
        current_time = int(time.time())
        start_time = current_time - 30 * 24 * 60 * 60  # 30 days ago

        print(f"Querying cost and usage data from {time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(start_time))} to now...")
        fetch_all_cost_data(openai_admin_api_key, start_time=start_time)
