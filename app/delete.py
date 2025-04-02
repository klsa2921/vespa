import requests

# Configuration
# VESPA_URL = "http://localhost:8080"  
VESPA_URL = "http://192.168.1.27:2923"  
SEARCH_ENDPOINT = f"{VESPA_URL}/search/"
DOCUMENT_API_ENDPOINT = f"{VESPA_URL}/document/v1/celebrity_news/celebrity_news/docid/"



def delete_employee_by_id(empid):
    """Delete a single employee by empid."""
    response = requests.delete(f"{DOCUMENT_API_ENDPOINT}{empid}")
    if response.status_code == 200:
        print(f"Employee {empid} successfully deleted.")
    else:
        print(f"Failed to delete employee {empid}: {response.text}")
        return False
    return True


def delete_all_text():
    """Delete all employee documents from the Vespa index."""
    employee_ids = get_all_text_ids()
    
    if not employee_ids:
        print("No texts found in the index.")
        return
    
    print(f"Found {len(employee_ids)} employees to delete.")
    
    for empid in employee_ids:
        delete_employee_by_id(empid)
    
    print("All employees deletion process completed.")

def main():
    delete_all_text()


def get_all_text_ids():
    """Retrieve all employee IDs from the index."""
    yql = "select id from sources celebrity_news where true"
    payload = {
        "yql": yql,
        "hits": 50 
    }
    response = requests.post(SEARCH_ENDPOINT, json=payload, headers={"Content-Type": "application/json"})
    
    if response.status_code != 200:
        print(f"Failed to query texts: {response.text}")
        return []
    
    results = response.json()
    if "root" not in results or "children" not in results["root"]:
        return []
    
    return [hit["fields"]["id"] for hit in results["root"]["children"]]


if __name__ == "__main__":
    main()