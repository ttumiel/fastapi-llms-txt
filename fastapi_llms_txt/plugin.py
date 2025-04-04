from typing import Any, Dict, List, Optional

from fastapi import APIRouter, FastAPI
from fastapi.responses import PlainTextResponse

from fastapi_llms_txt.generator import LLMsTxtGenerator
from fastapi_llms_txt.models import LinkItem, ProjectDescription

# Constants
LLMS_TXT_TAG = "LLMs.txt"
LLMS_TXT_ENDPOINT = "/llms.txt"


def add_llms_txt(
    app: FastAPI,
    title: str,
    summary: str,
    notes: Optional[List[str]] = None,
    sections: Dict[str, List[Dict[str, Any]]] = None,
    include_api_docs: bool = True,
) -> None:
    """
    Add an /llms.txt endpoint to a FastAPI application.

    Args:
        app: The FastAPI application.
        title: Title of the project.
        summary: Summary of the project.
        notes: Optional list of notes.
        sections: Dictionary of sections with lists of link items.
        include_api_docs: Whether to include API documentation in the llms.txt file.
    """
    if sections is None:
        sections = {}

    # Convert dict links to LinkItem objects with validation
    processed_sections = {}
    for section_name, links in sections.items():
        section_items = []
        for link in links:
            try:
                # Check that required keys exist
                if "title" not in link or "url" not in link:
                    raise ValueError(f"Link must have 'title' and 'url' keys: {link}")
                section_items.append(LinkItem(title=link["title"], url=link["url"]))
            except Exception as e:
                # Log the error but continue processing other links
                print(f"Error processing link in section '{section_name}': {e}")
                continue
        processed_sections[section_name] = section_items

    project_description = ProjectDescription(
        title=title, summary=summary, notes=notes, sections=processed_sections
    )

    generator = LLMsTxtGenerator(
        project_description=project_description, app=app if include_api_docs else None
    )

    router = APIRouter(tags=[LLMS_TXT_TAG])

    @router.get(
        LLMS_TXT_ENDPOINT,
        response_class=PlainTextResponse,
        summary="Get llms.txt contents",
        description=(
            "Returns a plain text llms.txt file that adheres to the llms.txt specification. "
            "This endpoint provides information about the API that is helpful for Large Language Models "
            "to understand the purpose and capabilities of this API."
        ),
        responses={
            200: {
                "content": {"text/plain": {}},
                "description": "A plain text llms.txt file describing the API.",
            }
        },
    )
    async def serve_llms_txt():
        """
        Serves the llms.txt file content.

        Returns:
            A plain text representation of the llms.txt file with information about the API
            that is helpful for Large Language Models.
        """
        content = generator.generate()
        return content

    # Use FastAPI's route description to document in OpenAPI schema
    if app.openapi_tags is None:
        app.openapi_tags = []

    # Add LLMs.txt tag description if it doesn't exist
    llms_tag_exists = any(tag.get("name") == LLMS_TXT_TAG for tag in app.openapi_tags)
    if not llms_tag_exists:
        app.openapi_tags.append(
            {
                "name": LLMS_TXT_TAG,
                "description": (
                    "Endpoints related to the llms.txt specification, "
                    "which provides information for Large Language Models "
                    "about the purpose and capabilities of this API."
                ),
            }
        )

    app.include_router(router)
