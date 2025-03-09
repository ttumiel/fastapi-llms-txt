from fastapi import APIRouter, Body, FastAPI, Path, Query
from fastapi.testclient import TestClient

from fastapi_llms_txt import add_llms_txt
from fastapi_llms_txt.plugin import LLMS_TXT_ENDPOINT, LLMS_TXT_TAG


def test_add_llms_txt_endpoint():
    """Test that the /llms.txt endpoint is added to the app."""
    app = FastAPI()
    add_llms_txt(
        app,
        title="Test API",
        summary="A test API for testing",
        sections={
            "Documentation": [{"title": "API Docs", "url": "https://example.com/docs"}]
        },
    )

    client = TestClient(app)
    response = client.get(LLMS_TXT_ENDPOINT)

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
            "Documentation": [{"title": "API Docs", "url": "https://example.com/docs"}]
        },
    )

    client = TestClient(app)
    response = client.get(LLMS_TXT_ENDPOINT)

    assert response.status_code == 200
    assert "- Note 1" in response.text
    assert "- Note 2" in response.text


def test_add_llms_txt_empty_sections():
    """Test the endpoint with empty sections."""
    app = FastAPI()
    add_llms_txt(app, title="Test API", summary="A test API for testing")

    client = TestClient(app)
    response = client.get(LLMS_TXT_ENDPOINT)

    assert response.status_code == 200
    assert "# Test API" in response.text
    assert "A test API for testing" in response.text


def test_add_llms_txt_content_type():
    """Test that the content type is plain text."""
    app = FastAPI()
    add_llms_txt(app, title="Test API", summary="A test API for testing")

    client = TestClient(app)
    response = client.get(LLMS_TXT_ENDPOINT)

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/plain; charset=utf-8"


def test_add_llms_txt_with_api_docs():
    """Test that API docs are included in the llms.txt file."""
    app = FastAPI()

    # Add a test endpoint
    @app.get("/users/{user_id}", summary="Get User", description="Get user by ID")
    def get_user(user_id: int = Path(..., description="The ID of the user")):
        """Get user information by user ID.

        This docstring should be processed for additional information.
        """
        # Test the function directly
        result = {"user_id": user_id}
        return result

    add_llms_txt(
        app, title="Test API", summary="A test API for testing", include_api_docs=True
    )

    client = TestClient(app)
    response = client.get(LLMS_TXT_ENDPOINT)

    assert response.status_code == 200
    assert "## API Endpoints" in response.text
    assert "GET /users/{user_id}" in response.text
    assert "Get User" in response.text
    assert "Get user by ID" in response.text
    assert "**Parameters:**" in response.text
    # The parameter might be extracted either as path parameter or from dependant
    param_line = response.text.split("**Parameters:**")[1]
    assert "`user_id`" in param_line
    assert "required" in param_line


def test_add_llms_txt_without_api_docs():
    """Test that API docs are not included when disabled."""
    app = FastAPI()

    # Add a test endpoint
    @app.get("/users/{user_id}")
    def get_user(user_id: int):
        """Get a user by ID."""
        return {"user_id": user_id}

    add_llms_txt(
        app, title="Test API", summary="A test API for testing", include_api_docs=False
    )

    client = TestClient(app)
    response = client.get(LLMS_TXT_ENDPOINT)

    assert response.status_code == 200
    assert "## API Endpoints" not in response.text
    assert "/users/{user_id}" not in response.text

    # Also test that endpoint is actually callable
    test_response = client.get("/users/123")
    assert test_response.status_code == 200
    assert test_response.json() == {"user_id": 123}


def test_add_llms_txt_with_invalid_links():
    """Test that the plugin handles invalid link objects gracefully."""
    app = FastAPI()

    # Create a section with an invalid link (missing url)
    invalid_links = {
        "Documentation": [
            {"title": "Valid Link", "url": "https://example.com/docs"},
            {"title": "Invalid Link - No URL"},  # Missing url key
            {"random_key": "Invalid Link - Wrong Keys"},  # No title or url
            None,  # Completely invalid object
        ]
    }

    # Should not raise any exceptions
    add_llms_txt(
        app, title="Test API", summary="A test API for testing", sections=invalid_links
    )

    # Create test client and make request
    client = TestClient(app)
    response = client.get(LLMS_TXT_ENDPOINT)

    # Verify response exists
    assert response is not None

    # Should still include the valid link
    assert response.status_code == 200
    assert "# Test API" in response.text
    assert "## Documentation" in response.text
    assert "[Valid Link](https://example.com/docs)" in response.text

    # Invalid links should be skipped
    assert "Invalid Link" not in response.text


def test_add_llms_txt_with_complex_api():
    """Test with a more complex API structure."""
    app = FastAPI(title="Complex API", description="A complex API with multiple routes")

    # Add router
    router = APIRouter(prefix="/api/v1", tags=["items"])

    @router.get("/items", summary="List Items", description="Get a list of all items")
    def list_items(
        skip: int = Query(0, description="Number of items to skip"),
        limit: int = Query(100, description="Max number of items to return"),
    ):
        """List all items with pagination.

        Returns a paginated list of items.
        """
        return {"skip": skip, "limit": limit}

    @router.post("/items", summary="Create Item", description="Create a new item")
    def create_item(name: str = Body(..., description="The name of the item")):
        """Create a new item.

        Creates a new item with the provided name.
        """
        return {"name": name}

    app.include_router(router)

    add_llms_txt(
        app, title="Complex API Test", summary="Testing a complex API structure"
    )

    client = TestClient(app)
    response = client.get(LLMS_TXT_ENDPOINT)

    assert response.status_code == 200
    assert "List Items" in response.text
    assert "Create Item" in response.text
    assert "/api/v1/items" in response.text

    # Also test that endpoints are callable
    test_response = client.get("/api/v1/items")
    assert test_response.status_code == 200
    assert test_response.json() == {"skip": 0, "limit": 100}


def test_add_llms_txt_with_existing_openapi_tags():
    """Test adding llms.txt to an app with existing openapi_tags."""
    app = FastAPI()

    # Set existing openapi_tags
    app.openapi_tags = [
        {"name": "Existing Tag", "description": "Description for existing tag"}
    ]

    add_llms_txt(app, title="Test API", summary="A test API for testing")

    # Check that the LLMs.txt tag was added but existing tags preserved
    assert len(app.openapi_tags) == 2
    assert app.openapi_tags[0]["name"] == "Existing Tag"
    assert app.openapi_tags[1]["name"] == LLMS_TXT_TAG


def test_add_llms_txt_with_existing_llms_tag():
    """Test adding llms.txt to an app that already has an LLMs.txt tag."""
    app = FastAPI()

    # Set existing LLMs.txt tag
    custom_tag = {
        "name": LLMS_TXT_TAG,
        "description": "Custom description for LLMs.txt",
    }
    app.openapi_tags = [custom_tag]

    # Verify the tag was set correctly
    assert app.openapi_tags[0] == custom_tag

    add_llms_txt(app, title="Test API", summary="A test API for testing")

    # Check that the tag wasn't duplicated
    assert len(app.openapi_tags) == 1
    assert app.openapi_tags[0]["name"] == LLMS_TXT_TAG
    assert app.openapi_tags[0]["description"] == "Custom description for LLMs.txt"


def test_add_llms_txt_default_sections():
    """Test that default empty sections work correctly."""
    app = FastAPI()

    # Don't provide sections parameter (should default to {})
    add_llms_txt(app, title="Test API", summary="A test API for testing")

    client = TestClient(app)
    response = client.get("/llms.txt")

    assert response.status_code == 200
    assert "# Test API" in response.text
    assert "A test API for testing" in response.text


def test_path_parameter_documentation():
    """Test that path parameters are correctly documented in llms.txt."""
    app = FastAPI()

    # Add a test endpoint with path parameters but no explicit type annotations
    @app.get("/books/{book_id}/chapters/{chapter_id}")
    def get_chapter(book_id, chapter_id):
        return {"book_id": book_id, "chapter_id": chapter_id}

    add_llms_txt(app, title="Test API", summary="A test API for testing")

    client = TestClient(app)
    response = client.get("/llms.txt")

    assert response.status_code == 200
    assert "GET /books/{book_id}/chapters/{chapter_id}" in response.text
    assert "**Parameters:**" in response.text
    assert "`book_id`" in response.text
    assert "`chapter_id`" in response.text


def test_add_llms_txt_no_openapi_tags():
    """Test adding llms.txt to an app with no openapi_tags attribute."""
    app = FastAPI()

    # Explicitly set openapi_tags to None
    app.openapi_tags = None

    add_llms_txt(app, title="Test API", summary="A test API for testing")

    # Check that the tag was added
    assert len(app.openapi_tags) == 1
    assert app.openapi_tags[0]["name"] == LLMS_TXT_TAG
