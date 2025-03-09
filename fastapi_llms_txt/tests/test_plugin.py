import pytest
from fastapi import FastAPI, APIRouter, Query, Path, Body
from fastapi.testclient import TestClient
from fastapi_llms_txt import add_llms_txt


def test_add_llms_txt_endpoint():
    """Test that the /llms.txt endpoint is added to the app."""
    app = FastAPI()
    add_llms_txt(
        app,
        title="Test API",
        summary="A test API for testing",
        sections={
            "Documentation": [
                {"title": "API Docs", "url": "https://example.com/docs"}
            ]
        }
    )
    
    client = TestClient(app)
    response = client.get("/llms.txt")
    
    assert response.status_code == 200
    assert "# Test API" in response.text
    assert "A test API for testing" in response.text
    assert "## Documentation" in response.text
    assert "[API Docs](https://example.com/docs)" in response.text


def test_add_llms_txt_with_notes():
    """Test the endpoint with notes."""
    app = FastAPI()
    add_llms_txt(
        app,
        title="Test API",
        summary="A test API for testing",
        notes=["Note 1", "Note 2"],
        sections={
            "Documentation": [
                {"title": "API Docs", "url": "https://example.com/docs"}
            ]
        }
    )
    
    client = TestClient(app)
    response = client.get("/llms.txt")
    
    assert response.status_code == 200
    assert "- Note 1" in response.text
    assert "- Note 2" in response.text


def test_add_llms_txt_empty_sections():
    """Test the endpoint with empty sections."""
    app = FastAPI()
    add_llms_txt(
        app,
        title="Test API",
        summary="A test API for testing"
    )
    
    client = TestClient(app)
    response = client.get("/llms.txt")
    
    assert response.status_code == 200
    assert "# Test API" in response.text
    assert "A test API for testing" in response.text


def test_add_llms_txt_content_type():
    """Test that the content type is plain text."""
    app = FastAPI()
    add_llms_txt(
        app,
        title="Test API",
        summary="A test API for testing"
    )
    
    client = TestClient(app)
    response = client.get("/llms.txt")
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/plain; charset=utf-8"


def test_add_llms_txt_with_api_docs():
    """Test that API docs are included in the llms.txt file."""
    app = FastAPI()
    
    # Add a test endpoint
    @app.get("/users/{user_id}", summary="Get User", description="Get user by ID")
    def get_user(user_id: int = Path(..., description="The ID of the user")):
        return {"user_id": user_id}
    
    add_llms_txt(
        app,
        title="Test API",
        summary="A test API for testing",
        include_api_docs=True
    )
    
    client = TestClient(app)
    response = client.get("/llms.txt")
    
    assert response.status_code == 200
    assert "## API Endpoints" in response.text
    assert "GET /users/{user_id}" in response.text
    assert "Get User" in response.text
    assert "Get user by ID" in response.text


def test_add_llms_txt_without_api_docs():
    """Test that API docs are not included when disabled."""
    app = FastAPI()
    
    # Add a test endpoint
    @app.get("/users/{user_id}")
    def get_user(user_id: int):
        return {"user_id": user_id}
    
    add_llms_txt(
        app,
        title="Test API",
        summary="A test API for testing",
        include_api_docs=False
    )
    
    client = TestClient(app)
    response = client.get("/llms.txt")
    
    assert response.status_code == 200
    assert "## API Endpoints" not in response.text
    assert "/users/{user_id}" not in response.text


def test_add_llms_txt_with_complex_api():
    """Test with a more complex API structure."""
    app = FastAPI(title="Complex API", description="A complex API with multiple routes")
    
    # Add router
    router = APIRouter(prefix="/api/v1", tags=["items"])
    
    @router.get("/items", summary="List Items", description="Get a list of all items")
    def list_items(
        skip: int = Query(0, description="Number of items to skip"),
        limit: int = Query(100, description="Max number of items to return")
    ):
        return {"skip": skip, "limit": limit}
    
    @router.post("/items", summary="Create Item", description="Create a new item")
    def create_item(name: str = Body(..., description="The name of the item")):
        return {"name": name}
    
    app.include_router(router)
    
    add_llms_txt(
        app,
        title="Complex API Test",
        summary="Testing a complex API structure"
    )
    
    client = TestClient(app)
    response = client.get("/llms.txt")
    
    assert response.status_code == 200
    assert "List Items" in response.text
    assert "Create Item" in response.text
    assert "/api/v1/items" in response.text


def test_add_llms_txt_with_existing_openapi_tags():
    """Test adding llms.txt to an app with existing openapi_tags."""
    app = FastAPI()
    
    # Set existing openapi_tags
    app.openapi_tags = [
        {"name": "Existing Tag", "description": "Description for existing tag"}
    ]
    
    add_llms_txt(
        app,
        title="Test API",
        summary="A test API for testing"
    )
    
    # Check that the LLMs.txt tag was added but existing tags preserved
    assert len(app.openapi_tags) == 2
    assert app.openapi_tags[0]["name"] == "Existing Tag"
    assert app.openapi_tags[1]["name"] == "LLMs.txt"


def test_add_llms_txt_with_existing_llms_tag():
    """Test adding llms.txt to an app that already has an LLMs.txt tag."""
    app = FastAPI()
    
    # Set existing LLMs.txt tag
    app.openapi_tags = [
        {"name": "LLMs.txt", "description": "Custom description for LLMs.txt"}
    ]
    
    add_llms_txt(
        app,
        title="Test API",
        summary="A test API for testing"
    )
    
    # Check that the tag wasn't duplicated
    assert len(app.openapi_tags) == 1
    assert app.openapi_tags[0]["name"] == "LLMs.txt"
    assert app.openapi_tags[0]["description"] == "Custom description for LLMs.txt"


def test_add_llms_txt_default_sections():
    """Test that default empty sections work correctly."""
    app = FastAPI()
    
    # Don't provide sections parameter (should default to {})
    add_llms_txt(
        app,
        title="Test API",
        summary="A test API for testing"
    )
    
    client = TestClient(app)
    response = client.get("/llms.txt")
    
    assert response.status_code == 200
    assert "# Test API" in response.text
    assert "A test API for testing" in response.text


def test_add_llms_txt_no_openapi_tags():
    """Test adding llms.txt to an app with no openapi_tags attribute."""
    app = FastAPI()
    
    # Explicitly set openapi_tags to None
    app.openapi_tags = None
    
    add_llms_txt(
        app,
        title="Test API",
        summary="A test API for testing"
    )
    
    # Check that the tag was added
    assert len(app.openapi_tags) == 1
    assert app.openapi_tags[0]["name"] == "LLMs.txt"