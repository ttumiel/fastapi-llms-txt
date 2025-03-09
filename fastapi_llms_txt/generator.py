from typing import List, Dict, Optional, Any
from fastapi import FastAPI
from fastapi.routing import APIRoute
from .models import ProjectDescription


class LLMsTxtGenerator:
    """Generates llms.txt content from project description."""

    def __init__(self, project_description: ProjectDescription, app: Optional[FastAPI] = None):
        self.project_description = project_description
        self.app = app

    def generate(self) -> str:
        """Generate llms.txt content in the specified format."""
        content = [
            f"# {self.project_description.title}",
            "",
            f"{self.project_description.summary}",
            ""
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
            if getattr(route, "name", None) != "serve_llms_txt":  # Skip the llms.txt endpoint itself
                path = getattr(route, "path", "")
                methods = getattr(route, "methods", [])
                summary = getattr(route, "summary", "") or self._get_endpoint_name(route)
                description = getattr(route, "description", "")
                
                if path:  # Only process routes with a path
                    has_routes_content = True
                    
                    # Convert methods to string, default to GET if None or empty
                    methods_str = ", ".join(methods) if methods else "GET"
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
                            required = "required" if param.get("required", False) else "optional"
                            param_type = param.get("type", "")
                            description = param.get("description", "")
                            content.append(f"- `{param['name']}` ({param_type}, {required}): {description}")
                        content.append("")
        
        # Only return content if we actually added route information
        return content if has_routes_content else []
    
    def _get_all_routes(self) -> List[APIRoute]:
        """Get all routes from the FastAPI app."""
        if not self.app:
            return []
        
        routes = []
        for route in self.app.routes:
            if isinstance(route, APIRoute) and route.name != "serve_llms_txt":
                routes.append(route)
        return routes
    
    def _get_endpoint_name(self, route: Any) -> str:
        """Get a human-readable name for an endpoint."""
        path = getattr(route, "path", "")
        func = getattr(route, "endpoint", None)
        
        # Skip llms.txt endpoints
        if func and hasattr(func, "__name__") and func.__name__ == "serve_llms_txt":
            return ""
            
        if func and hasattr(func, "__name__") and func.__name__ != "serve_llms_txt":
            return func.__name__.replace("_", " ").title()
        elif path:
            parts = [p for p in path.split("/") if p and not p.startswith("{")]
            if parts:
                return parts[-1].replace("_", " ").title()
        return ""
    
    def _get_endpoint_params(self, route: Any) -> List[Dict[str, Any]]:
        """Extract parameter information from an endpoint."""
        params = []
        if hasattr(route, "dependant") and hasattr(route.dependant, "params"):
            for param in route.dependant.params:
                # Get type as string, handling different representations
                type_str = str(param.type_)
                # Clean up type string (remove typing. prefix, class wrapper, etc.)
                type_str = type_str.replace("typing.", "")
                type_str = type_str.replace("<class '", "").replace("'>", "")
                
                param_info = {
                    "name": param.name,
                    "required": param.required,
                    "type": type_str,
                    "description": getattr(param.field_info, "description", "")
                }
                params.append(param_info)
        return params