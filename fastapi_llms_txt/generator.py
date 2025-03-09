from typing import Any, Dict, List, Optional

from fastapi import FastAPI
from fastapi.routing import APIRoute

from fastapi_llms_txt.models import ProjectDescription

# Constants
SERVE_LLMS_TXT = "serve_llms_txt"
DEFAULT_HTTP_METHOD = "GET"


class LLMsTxtGenerator:
    """Generates llms.txt content from project description."""

    def __init__(
        self, project_description: ProjectDescription, app: Optional[FastAPI] = None
    ):
        self.project_description = project_description
        self.app = app

    def generate(self) -> str:
        """Generate llms.txt content in the specified format."""
        content = [
            f"# {self.project_description.title}",
            "",
            f"{self.project_description.summary}",
            "",
        ]

        # Add notes
        if self.project_description.notes:
            for note in self.project_description.notes:
                content.append(f"- {note}")
            content.append("")

        # Add API endpoints documentation if app is provided
        if self.app:
            api_docs = self._generate_api_docs()
            if api_docs:
                content.extend(api_docs)

        # Add sections
        for section_name, links in self.project_description.sections.items():
            content.append(f"## {section_name}")
            content.append("")
            for link in links:
                content.append(f"- [{link.title}]({link.url})")
            content.append("")

        return "\n".join(content)

    def _generate_api_docs(self) -> List[str]:
        """Generate documentation for API endpoints from FastAPI app."""
        if not self.app:
            return []

        content = ["## API Endpoints", ""]

        routes = self._get_all_routes()
        if not routes:
            return []

        has_routes_content = False

        for route in routes:
            if (
                getattr(route, "name", None) != "serve_llms_txt"
            ):  # Skip the llms.txt endpoint itself
                path = getattr(route, "path", "")
                methods = getattr(route, "methods", [])
                summary = getattr(route, "summary", "") or self._get_endpoint_name(
                    route
                )
                description = getattr(route, "description", "")

                if path:  # Only process routes with a path
                    has_routes_content = True

                    # Convert methods to string, using default if None or empty
                    methods_str = ", ".join(methods) if methods else DEFAULT_HTTP_METHOD
                    content.append(f"### {methods_str} {path}")
                    content.append("")

                    if summary:
                        content.append(f"{summary}")
                        content.append("")

                    if description:
                        content.append(f"{description}")
                        content.append("")

                    # Add parameters info if available
                    params = self._get_endpoint_params(route)
                    if params:
                        content.append("**Parameters:**")
                        content.append("")
                        for param in params:
                            required = (
                                "required"
                                if param.get("required", False)
                                else "optional"
                            )
                            param_type = param.get("type", "")
                            description = param.get("description", "")
                            content.append(
                                f"- `{param['name']}` ({param_type}, {required}): {description}"
                            )
                        content.append("")

        # Only return content if we actually added route information
        return content if has_routes_content else []

    def _get_all_routes(self) -> List[APIRoute]:
        """Get all routes from the FastAPI app."""
        if not self.app:
            return []

        # Use list comprehension for cleaner code
        return [
            route
            for route in self.app.routes
            if isinstance(route, APIRoute) and route.name != SERVE_LLMS_TXT
        ]

    def _get_endpoint_name(self, route: Any) -> str:
        """Get a human-readable name for an endpoint."""
        path = getattr(route, "path", "")
        func = getattr(route, "endpoint", None)

        # Check if this is the function that serves llms.txt
        func_name = getattr(func, "__name__", "") if func else ""

        # Skip llms.txt endpoints
        if func_name == SERVE_LLMS_TXT:
            return ""

        if func_name and func_name != SERVE_LLMS_TXT:
            return func_name.replace("_", " ").title()
        elif path:
            parts = [p for p in path.split("/") if p and not p.startswith("{")]
            if parts:
                return parts[-1].replace("_", " ").title()
        return ""

    def _get_endpoint_params(self, route: Any) -> List[Dict[str, Any]]:
        """Extract parameter information from an endpoint."""
        params = []
        param_names = set()

        # Extract path parameters from the path
        path_params = {}
        route_path = getattr(route, "path", "")
        if route_path and "{" in route_path:
            path_parts = route_path.split("/")
            for part in path_parts:
                if part.startswith("{") and part.endswith("}"):
                    param_name = part[1:-1]  # Remove the curly braces
                    path_params[param_name] = {
                        "name": param_name,
                        "required": True,  # Path parameters are always required
                        "type": "str",  # Default to string if we can't determine type
                        "description": f"Path parameter: {param_name}",
                    }

        # Process parameters from the route's dependant (these have more information)
        route_dependant = getattr(route, "dependant", None)
        dependant_params = (
            getattr(route_dependant, "params", []) if route_dependant else []
        )

        for param in dependant_params:
            # Get the parameter name or skip if not available
            param_name = getattr(param, "name", None)
            if not param_name:
                continue

            # Get type as string, handling different representations
            type_str = str(getattr(param, "type_", ""))
            # Clean up type string (remove typing. prefix, class wrapper, etc.)
            type_str = type_str.replace("typing.", "")
            type_str = type_str.replace("<class '", "").replace("'>", "")

            # Determine if the parameter is required
            required = getattr(param, "required", False)

            # Get field info and description
            field_info = getattr(param, "field_info", None)
            param_description = (
                getattr(field_info, "description", "") if field_info else ""
            )

            # If this is a path parameter and we don't have a description, use a generic one
            if param_name in path_params and not param_description:
                param_description = f"Path parameter: {param_name}"

            param_info = {
                "name": param_name,
                "required": required,
                "type": type_str,
                "description": param_description,
            }
            params.append(param_info)
            param_names.add(param_name)

        # Add any path parameters that weren't in the dependant params
        for name, param_info in path_params.items():
            if name not in param_names:
                params.append(param_info)

        # Try to enhance param descriptions from docstring if available
        endpoint = getattr(route, "endpoint", None)
        docstring = getattr(endpoint, "__doc__", "")
        if docstring:
            docstring = docstring.strip()
            # Here we could implement more sophisticated docstring parsing if needed

        return params
