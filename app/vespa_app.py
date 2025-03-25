import io
import logging
import os
import zipfile
from datetime import datetime, timedelta

import requests  # pip install requests


logger = logging.getLogger(__name__)

VESPA_APPLICATION_ENDPOINT = "http://192.168.1.27:2922/application/v2"  
VESPA_APPLICATION_SCHEMA_PATH = "app/docker/app-text"  


def in_memory_zip_from_file_bytes(file_contents: dict[str, bytes]) -> io.BytesIO:
    """Create an in-memory ZIP file from a dictionary of file contents."""
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
        for filename, content in file_contents.items():
            zipf.writestr(filename, content)
    zip_buffer.seek(0)
    return zip_buffer

def deploy_vespa_application(
    index_name: str,
    vespa_schema_path: str,
) -> None:
    """Deploy a Vespa application package, updating only validation-overrides.xml."""
    deploy_url = f"{VESPA_APPLICATION_ENDPOINT}/tenant/default/prepareandactivate"
    logger.info(f"Deploying Vespa application package to {deploy_url}")

    # File paths for Vespa configuration files
    schema_file = os.path.join(vespa_schema_path, "schemas", "tv9_news.sd")
    services_file = os.path.join(vespa_schema_path, "services.xml")
    overrides_file = os.path.join(vespa_schema_path, "validation-overrides.xml")

    # Read files
    with open(services_file, "rb") as services_f:
        services_content = services_f.read()

    with open(schema_file, "rb") as schema_f:
        schema_content = schema_f.read()

    with open(overrides_file, "r") as overrides_f:
        overrides_template = overrides_f.read()

    # Set validation override date (7 days from now)
    now = datetime.now()
    date_in_7_days = now + timedelta(days=7)
    formatted_date = date_in_7_days.strftime("%Y-%m-%d")
    overrides_content = overrides_template.replace("DATE_REPLACEMENT", formatted_date)

    # Create ZIP file in memory
    zip_dict = {
        "services.xml": services_content,
        "validation-overrides.xml": overrides_content.encode("utf-8"),
        f"schemas/{index_name}.sd": schema_content,
    }
    zip_file = in_memory_zip_from_file_bytes(zip_dict)

    # Deploy the application package
    headers = {"Content-Type": "application/zip"}
    response = requests.post(deploy_url, headers=headers, data=zip_file)

    if response.status_code != 200:
        logger.error(f"Failed to deploy Vespa application. Response: {response.text}")
        raise RuntimeError(f"Failed to deploy Vespa application. Response: {response.text}")
    else:
        logger.info("Vespa application deployed successfully")


if __name__ == "__main__":
    deploy_vespa_application(
        index_name="tv9_news",
        vespa_schema_path=VESPA_APPLICATION_SCHEMA_PATH,
    )



# Reference 
# https://github.com/onyx-dot-app/onyx/blob/main/backend/onyx/document_index/vespa
# https://docs.vespa.ai/en/reference/validation-overrides.html