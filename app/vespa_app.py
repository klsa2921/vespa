import io
import os
import zipfile
from datetime import datetime, timedelta

import requests  # type: ignore
from onyx.utils.logger import setup_logger

logger = setup_logger()

VESPA_APPLICATION_ENDPOINT = "http://localhost:8080/application/v1"  # Adjust as needed
VESPA_APPLICATION_SCHEMA_PATH = "app/docker/app-text"  # Adjust as needed
def in_memory_zip_from_file_bytes(file_contents: dict[str, bytes]) -> io.BytesIO:
    """Create an in-memory ZIP file from a dictionary of file contents."""
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
        for filename, content in file_contents.items():
            zipf.writestr(filename, content)
    zip_buffer.seek(0)
    return zip_buffer

def _create_document_xml_lines(doc_names: list[str]) -> str:
    """Generate XML lines for documents in services.xml."""
    doc_lines = [
        f'<document type="{doc_name}" mode="index" />'
        for doc_name in doc_names
        if doc_name
    ]
    return "\n".join(doc_lines)

def deploy_vespa_application(
    index_name: str,
    embedding_dim: int,
    embedding_precision: str,
    vespa_schema_path: str ,
) -> None:
    """Deploy a Vespa application package with the specified index configuration."""
    deploy_url = f"{VESPA_APPLICATION_ENDPOINT}/tenant/default/prepareandactivate"
    logger.info(f"Deploying Vespa application package to {deploy_url}")

    # File paths for Vespa configuration templates
    schema_file = os.path.join(vespa_schema_path, "schemas", "celebrity_news.sd")
    services_file = os.path.join(vespa_schema_path, "services.xml")
    overrides_file = os.path.join(vespa_schema_path, "validation-overrides.xml")

    # Read template files
    with open(services_file, "r") as services_f:
        services_template = services_f.read()

    with open(schema_file, "r") as schema_f:
        schema_template = schema_f.read()

    with open(overrides_file, "r") as overrides_f:
        overrides_template = overrides_f.read()

    # Prepare services.xml with document definitions
    schema_names = [index_name]
    doc_lines = _create_document_xml_lines(schema_names)
    services = services_template.replace("<!-- DOCUMENTS -->", doc_lines)
    services = services.replace("<!-- NUM_SEARCHER_THREADS -->", "4")  # Default threads

    # Prepare schema with embedding settings
    schema = (
        schema_template
        .replace("EMBEDDING_PRECISION", embedding_precision)
        .replace("DANSWER_CHUNK", index_name)
        .replace("VESPA_DIM", str(embedding_dim))
    )

    # Set validation override date (7 days from now)
    now = datetime.now()
    date_in_7_days = now + timedelta(days=7)
    formatted_date = date_in_7_days.strftime("%Y-%m-%d")
    overrides = overrides_template.replace("DATE_REPLACEMENT", formatted_date)

    # Create ZIP file in memory
    zip_dict = {
        "services.xml": services.encode("utf-8"),
        "validation-overrides.xml": overrides.encode("utf-8"),
        f"schemas/{index_name}.sd": schema.encode("utf-8"),
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

# Example usage
if __name__ == "__main__":
    deploy_vespa_application(
        index_name="my_index",
        embedding_dim=384,
        embedding_precision="float",
        vespa_schema_path=VESPA_APPLICATION_SCHEMA_PATH  
    )

# Reference 
# https://github.com/onyx-dot-app/onyx/blob/main/backend/onyx/document_index/vespa