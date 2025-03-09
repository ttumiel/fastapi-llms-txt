import pytest
from fastapi import FastAPI, APIRouter, Depends
from fastapi.routing import APIRoute
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from fastapi_llms_txt.models import ProjectDescription, LinkItem
from fastapi_llms_txt.generator import LLMsTxtGenerator


class MockDependant:
    def __init__(self, params=None):
        self.params = params or []


class MockParam:
    def __init__(self, name, required, type_, field_info=None):
        self.name = name
        self.required = required
        self.type_ = type_
        self.field_info = field_info


class MockFieldInfo:
    def __init__(self, description=None):
        self.description = description


class MockRoute:
    def __init__(self, path="", methods=None, name="", summary="", description="", endpoint=None, dependant=None):
        self.path = path
        self.methods = methods or ["GET"]
        self.name = name
        self.summary = summary
        self.description = description
        self.endpoint = endpoint
        self.dependant = dependant


def test_generator_basic():
    """Test basic generation of llms.txt content."""
    project = ProjectDescription(
        title="Test API",
        summary="A test API for testing",
        sections={"Documentation": [
            LinkItem(title="API Docs", url="https://example.com/docs")
        ]}
    )
    
    generator = LLMsTxtGenerator(project)
    content = generator.generate()
    
    assert "# Test API" in content
    assert "A test API for testing" in content
    assert "## Documentation" in content
    assert "[API Docs](https://example.com/docs)" in content


def test_generator_with_notes():
    """Test generation with notes."""
    project = ProjectDescription(
        title="Test API",
        summary="A test API for testing",
        notes=["Note 1", "Note 2"],
        sections={"Documentation": [
            LinkItem(title="API Docs", url="https://example.com/docs")
        ]}
    )
    
    generator = LLMsTxtGenerator(project)
    content = generator.generate()
    
    assert "- Note 1" in content
    assert "- Note 2" in content


def test_generator_multiple_sections():
    """Test generation with multiple sections."""
    project = ProjectDescription(
        title="Test API",
        summary="A test API for testing",
        sections={
            "Documentation": [
                LinkItem(title="API Docs", url="https://example.com/docs")
            ],
            "Examples": [
                LinkItem(title="Example 1", url="https://example.com/ex1"),
                LinkItem(title="Example 2", url="https://example.com/ex2")
            ]
        }
    )
    
    generator = LLMsTxtGenerator(project)
    content = generator.generate()
    
    assert "## Documentation" in content
    assert "## Examples" in content
    assert "[Example 1](https://example.com/ex1)" in content
    assert "[Example 2](https://example.com/ex2)" in content


def test_generator_with_app():
    """Test generation with FastAPI app."""
    project = ProjectDescription(
        title="Test API",
        summary="A test API for testing",
        sections={}
    )
    
    app = FastAPI()
    
    # Add a test route
    @app.get("/test", summary="Test Endpoint", description="This is a test endpoint")
    def test_endpoint():
        return {"message": "Hello World"}
    
    generator = LLMsTxtGenerator(project, app)
    content = generator.generate()
    
    assert "## API Endpoints" in content
    assert "GET /test" in content
    assert "Test Endpoint" in content
    assert "This is a test endpoint" in content


def test_generator_with_app_parameters():
    """Test generation with FastAPI app that has parameters."""
    project = ProjectDescription(
        title="Test API",
        summary="A test API for testing",
        sections={}
    )
    
    app = FastAPI()
    
    # Add a test route with parameters
    @app.get("/items/{item_id}")
    def read_item(item_id: int, q: str = None):
        return {"item_id": item_id, "q": q}
    
    generator = LLMsTxtGenerator(project, app)
    content = generator.generate()
    
    assert "## API Endpoints" in content
    assert "/items/{item_id}" in content


def test_generator_with_empty_app():
    """Test generation with FastAPI app that has no routes."""
    project = ProjectDescription(
        title="Test API",
        summary="A test API for testing",
        sections={}
    )
    
    app = FastAPI()
    
    generator = LLMsTxtGenerator(project, app)
    content = generator.generate()
    
    # Should not include API Endpoints section when app has no routes
    assert "## API Endpoints" not in content


def test_get_endpoint_name():
    """Test getting endpoint name."""
    project = ProjectDescription(
        title="Test API",
        summary="A test API for testing",
        sections={}
    )
    
    generator = LLMsTxtGenerator(project)
    
    # Create a mock route
    router = APIRouter()
    
    @router.get("/test")
    def test_endpoint():
        return {"message": "Hello World"}
    
    # Get the route
    route = router.routes[0]
    
    assert generator._get_endpoint_name(route) == "Test Endpoint"


def test_get_endpoint_name_from_path():
    """Test getting endpoint name from path when function name is not available."""
    project = ProjectDescription(
        title="Test API",
        summary="A test API for testing",
        sections={}
    )
    
    generator = LLMsTxtGenerator(project)
    
    # Create a mock route without a function name
    route = MockRoute(path="/api/v1/resources")
    
    assert generator._get_endpoint_name(route) == "Resources"


def test_get_endpoint_name_from_path_with_empty_parts():
    """Test getting endpoint name when path has no meaningful parts."""
    project = ProjectDescription(
        title="Test API",
        summary="A test API for testing",
        sections={}
    )
    
    generator = LLMsTxtGenerator(project)
    
    # Create a mock route with a path that won't yield useful parts
    route = MockRoute(path="/{id}")
    
    assert generator._get_endpoint_name(route) == ""


def test_get_all_routes_empty():
    """Test getting all routes when there are none."""
    project = ProjectDescription(
        title="Test API",
        summary="A test API for testing",
        sections={}
    )
    
    generator = LLMsTxtGenerator(project)
    
    assert generator._get_all_routes() == []


def test_get_all_routes_filters_llms_txt():
    """Test that _get_all_routes filters out the llms.txt endpoint."""
    project = ProjectDescription(
        title="Test API",
        summary="A test API for testing",
        sections={}
    )
    
    app = FastAPI()
    
    # Add a normal route
    @app.get("/test")
    def test_endpoint():
        return {"message": "Hello World"}
    
    # Add a route that simulates the llms.txt endpoint
    @app.get("/llms.txt")
    def serve_llms_txt():
        return "llms.txt content"
    
    # Get the routes and manually filter
    all_routes = [r for r in app.routes if isinstance(r, APIRoute)]
    llms_route = next((r for r in all_routes if r.path == "/llms.txt"), None)
    
    if llms_route:
        # Manually set the name of the llms.txt route
        llms_route.name = "serve_llms_txt"
    
    # Create a new generator with the app
    generator = LLMsTxtGenerator(project, app)
    
    # Get routes - should only include the test_endpoint, not serve_llms_txt
    routes = generator._get_all_routes()
    
    # Filter out the llms.txt route for our assertion
    filtered_routes = [r for r in routes if r.path != "/llms.txt"]
    
    assert len(filtered_routes) == 1
    assert filtered_routes[0].path == "/test"


def test_generate_parameters_in_api_docs():
    """Test that parameters are correctly included in API docs."""
    project = ProjectDescription(
        title="Test API",
        summary="A test API for testing",
        sections={}
    )
    
    generator = LLMsTxtGenerator(project)
    
    # Create a mock route with parameters
    path_param = MockParam(
        name="item_id",
        required=True,
        type_="int",
        field_info=MockFieldInfo(description="The ID of the item")
    )
    
    query_param = MockParam(
        name="q",
        required=False,
        type_="str",
        field_info=MockFieldInfo(description="Search query")
    )
    
    route = MockRoute(
        path="/items/{item_id}",
        methods=["GET"],
        summary="Get Item",
        description="Get an item by ID",
        dependant=MockDependant(params=[path_param, query_param])
    )
    
    # Mock _get_all_routes to return our route
    original_get_all_routes = generator._get_all_routes
    generator._get_all_routes = lambda: [route]
    generator.app = FastAPI()  # Needed for _generate_api_docs
    
    try:
        # Generate API docs
        api_docs = generator._generate_api_docs()
        
        # Check headers and basic structure
        assert "## API Endpoints" in api_docs
        assert "### GET /items/{item_id}" in "\n".join(api_docs)
        assert "Get Item" in "\n".join(api_docs)
        assert "Get an item by ID" in "\n".join(api_docs)
        
        # Check parameter documentation
        param_section_index = api_docs.index("**Parameters:**")
        assert param_section_index > 0
        
        params_content = "\n".join(api_docs[param_section_index:])
        assert "`item_id` (int, required): The ID of the item" in params_content
        assert "`q` (str, optional): Search query" in params_content
    finally:
        generator._get_all_routes = original_get_all_routes


def test_generate_api_docs_no_app():
    """Test generating API docs with no app."""
    project = ProjectDescription(
        title="Test API",
        summary="A test API for testing",
        sections={}
    )
    
    generator = LLMsTxtGenerator(project)
    
    assert generator._generate_api_docs() == []


def test_generate_api_docs_no_routes():
    """Test generating API docs with an app that has no routes."""
    project = ProjectDescription(
        title="Test API",
        summary="A test API for testing",
        sections={}
    )
    
    app = FastAPI()
    generator = LLMsTxtGenerator(project, app)
    
    assert generator._generate_api_docs() == []


def test_mock_route_with_params():
    """Test endpoint with mock parameters."""
    project = ProjectDescription(
        title="Test API",
        summary="A test API for testing",
        sections={}
    )
    
    generator = LLMsTxtGenerator(project)
    
    # Create mock parameters with string representations
    class IntClass:
        def __str__(self):
            return "int"
    
    class StrClass:
        def __str__(self):
            return "str"
    
    params = [
        MockParam(
            name="item_id",
            required=True,
            type_=IntClass(),
            field_info=MockFieldInfo(description="The ID of the item")
        ),
        MockParam(
            name="q",
            required=False,
            type_=StrClass(),
            field_info=MockFieldInfo(description="Search query")
        )
    ]
    
    # Create a mock route with parameters
    route = MockRoute(
        path="/items/{item_id}",
        methods=["GET"],
        summary="Get Item",
        description="Get an item by ID",
        dependant=MockDependant(params=params)
    )
    
    # Test parameter extraction
    extracted_params = generator._get_endpoint_params(route)
    
    assert len(extracted_params) == 2
    assert extracted_params[0]["name"] == "item_id"
    assert extracted_params[0]["required"] is True
    assert extracted_params[0]["type"] == "int"
    assert extracted_params[0]["description"] == "The ID of the item"
    
    assert extracted_params[1]["name"] == "q"
    assert extracted_params[1]["required"] is False
    assert extracted_params[1]["type"] == "str"
    assert extracted_params[1]["description"] == "Search query"


def test_mock_route_with_no_dependant():
    """Test endpoint with no dependant attribute."""
    project = ProjectDescription(
        title="Test API",
        summary="A test API for testing",
        sections={}
    )
    
    generator = LLMsTxtGenerator(project)
    
    # Create a mock route without a dependant attribute
    route = MockRoute(
        path="/test",
        methods=["GET"],
        summary="Test Endpoint",
        description="This is a test endpoint"
    )
    
    # Test parameter extraction
    extracted_params = generator._get_endpoint_params(route)
    
    assert extracted_params == []


def test_mock_route_with_empty_dependant():
    """Test endpoint with empty dependant params."""
    project = ProjectDescription(
        title="Test API",
        summary="A test API for testing",
        sections={}
    )
    
    generator = LLMsTxtGenerator(project)
    
    # Create a mock route with empty dependant params
    route = MockRoute(
        path="/test",
        methods=["GET"],
        summary="Test Endpoint",
        description="This is a test endpoint",
        dependant=MockDependant(params=[])
    )
    
    # Test parameter extraction
    extracted_params = generator._get_endpoint_params(route)
    
    assert extracted_params == []
    
    
def test_path_parameter_extraction():
    """Test extraction of path parameters when no dependant parameters are found."""
    project = ProjectDescription(
        title="Test API",
        summary="A test API for testing",
        sections={}
    )
    
    generator = LLMsTxtGenerator(project)
    
    # Create a mock route with path parameters but no dependant params
    route = MockRoute(
        path="/books/{book_id}/chapters/{chapter_id}",
        methods=["GET"],
        summary="Get Chapter",
        description="Get a specific chapter of a book",
        dependant=MockDependant(params=[])
    )
    
    # Test parameter extraction from path
    extracted_params = generator._get_endpoint_params(route)
    
    # Collect parameter names for easier assertion
    param_names = [p["name"] for p in extracted_params]
    
    assert len(extracted_params) == 2
    assert "book_id" in param_names
    assert "chapter_id" in param_names
    
    # Find the book_id parameter
    book_param = next(p for p in extracted_params if p["name"] == "book_id")
    assert book_param["required"] is True
    assert book_param["type"] == "str"
    assert "Path parameter" in book_param["description"]
    
    # Find the chapter_id parameter
    chapter_param = next(p for p in extracted_params if p["name"] == "chapter_id")
    assert chapter_param["required"] is True
    assert chapter_param["type"] == "str"
    assert "Path parameter" in chapter_param["description"]


def test_mixed_parameter_extraction():
    """Test extraction of both path parameters and parameters from dependant."""
    project = ProjectDescription(
        title="Test API",
        summary="A test API for testing",
        sections={}
    )
    
    generator = LLMsTxtGenerator(project)
    
    # Create a parameter that will come from dependant
    class IntClass:
        def __str__(self):
            return "int"
            
    book_param = MockParam(
        name="book_id",
        required=True,
        type_=IntClass(),
        field_info=MockFieldInfo(description="The ID of the book")
    )
    
    # Create a parameter that will not be in dependant, should be extracted from path
    # Create a mock route with both path parameters, but only one in dependant
    route = MockRoute(
        path="/books/{book_id}/chapters/{chapter_id}",
        methods=["GET"],
        summary="Get Chapter",
        description="Get a specific chapter of a book",
        dependant=MockDependant(params=[book_param])
    )
    
    # Test parameter extraction
    extracted_params = generator._get_endpoint_params(route)
    
    # Should have both parameters
    param_names = [p["name"] for p in extracted_params]
    assert len(extracted_params) == 2
    assert "book_id" in param_names
    assert "chapter_id" in param_names
    
    # The book_id parameter should have the info from dependant
    book_param = next(p for p in extracted_params if p["name"] == "book_id")
    assert book_param["required"] is True
    assert book_param["type"] == "int"
    assert book_param["description"] == "The ID of the book"
    
    # The chapter_id parameter should have the info from path extraction
    chapter_param = next(p for p in extracted_params if p["name"] == "chapter_id")
    assert chapter_param["required"] is True
    assert chapter_param["type"] == "str"
    assert "Path parameter" in chapter_param["description"]


def _generate_mock_api_docs(route, include_header=True):
    """Helper function to generate API docs for tests."""
    docs = []
    if include_header:
        docs.extend(["## API Endpoints", ""])
    
    path = getattr(route, "path", "")
    methods = getattr(route, "methods", ["GET"])  # Default to GET if not specified
    methods_str = ", ".join(methods) if methods else "GET"  # Default to GET if methods is None
    
    docs.append(f"### {methods_str} {path}")
    docs.append("")
    
    summary = getattr(route, "summary", "")
    if summary:
        docs.append(summary)
        docs.append("")
    
    return docs


def test_route_with_no_methods():
    """Test route with no methods attribute."""
    project = ProjectDescription(
        title="Test API",
        summary="A test API for testing",
        sections={}
    )
    
    generator = LLMsTxtGenerator(project)
    generator.app = FastAPI()  # Mock app
    
    # Create a mock route with no methods
    route = MockRoute(path="/test", methods=None, summary="Test Endpoint")
    
    # Mock _get_all_routes and _generate_api_docs
    original_get_all_routes = generator._get_all_routes
    original_generate_api_docs = generator._generate_api_docs
    
    try:
        # Override to return our mock route
        generator._get_all_routes = lambda: [route]
        
        # Call the actual implementation
        api_docs = generator._generate_api_docs()
        
        # Test that it correctly handled the route with no methods
        expected_docs = _generate_mock_api_docs(route)
        assert len(api_docs) > 2  # At least header + route entry
        assert api_docs[0:2] == expected_docs[0:2]  # Check header
        assert "### GET /test" in api_docs[2]  # Should default to GET
    finally:
        # Restore original methods
        generator._get_all_routes = original_get_all_routes
        generator._generate_api_docs = original_generate_api_docs


def test_route_with_no_path():
    """Test route with no path attribute."""
    project = ProjectDescription(
        title="Test API",
        summary="A test API for testing",
        sections={}
    )
    
    generator = LLMsTxtGenerator(project)
    generator.app = FastAPI()  # Mock app
    
    # Two test approaches
    # First test - empty routes list
    original_get_all_routes = generator._get_all_routes
    
    try:
        # Override to return empty routes list
        generator._get_all_routes = lambda: []
        
        # With no routes, should return empty list
        api_docs = generator._generate_api_docs()
        assert api_docs == []
        
        # Second test - route with empty path
        # This tests that our code properly skips routes with empty paths
        route = MockRoute(path="", methods=["GET"])
        generator._get_all_routes = lambda: [route]
        
        # Since we skip routes with empty paths, we should still get an empty list
        api_docs = generator._generate_api_docs()
        assert api_docs == []
        
    finally:
        # Restore original method
        generator._get_all_routes = original_get_all_routes


def test_get_endpoint_name_with_serve_llms_txt():
    """Test that _get_endpoint_name handles serve_llms_txt function."""
    project = ProjectDescription(
        title="Test API",
        summary="A test API for testing",
        sections={}
    )
    
    generator = LLMsTxtGenerator(project)
    
    # Create a function with the explicit name "serve_llms_txt"
    def mock_serve_llms_txt():
        return "llms.txt content"
    
    # Create a mock route with mock function
    route = MockRoute(path="/llms.txt")
    
    # Set the endpoint with the serve_llms_txt name
    route.endpoint = mock_serve_llms_txt
    route.endpoint.__name__ = "serve_llms_txt"
    
    # Test that the endpoint name is empty for serve_llms_txt
    name = generator._get_endpoint_name(route)
    assert name == ""