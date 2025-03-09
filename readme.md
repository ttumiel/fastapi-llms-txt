# fastapi-llms-txt

FastAPI plugin to easily serve `/llms.txt` files, following the [llms.txt specification](https://llmstxt.org/). This plugin automatically generates documentation for your API that is helpful for Large Language Models to understand your API's capabilities.

## Installation

```bash
pip install .
```

## Usage

```python
from fastapi import FastAPI
from fastapi_llms_txt import add_llms_txt

app = FastAPI()

# Define your API routes
@app.get("/items/{item_id}")
def read_item(item_id: int, q: str = None):
    """
    Get an item by ID.

    Parameters:
    - item_id: The ID of the item to retrieve
    - q: Optional query parameter
    """
    return {"item_id": item_id, "q": q}

# Add llms.txt endpoint
add_llms_txt(
    app,
    title="My API",
    summary="A simple API to demonstrate llms.txt",
    notes=["Note about API", "Another important note"],
    sections={
        "Docs": [
            {"title": "API Reference", "url": "https://api.example.com/docs.md"},
        ],
        "Optional": [
            {"title": "Extended Info", "url": "https://api.example.com/extended_info.md"}
        ]
    }
)
```

Now your API automatically serves an llms.txt endpoint at:

```
GET /llms.txt
```

### Output Format

The generated llms.txt file follows this format:

```markdown
# API Title

Short description of what your API does

- Important note 1
- Important note 2

## API Endpoints

### GET /endpoint

Endpoint description

**Parameters:**

- `param_name` (type, required/optional): Parameter description

## Documentation

- [API Docs](https://example.com/docs)
```

## Tests

Run tests:

```bash
pytest
```

For test coverage:

```bash
pytest --cov=fastapi_llms_txt
```

## Example API

An example API implementation is provided in `example_api.py`. To run it:

```bash
# Install requirements
pip install -r requirements_example.txt

# Run the example
python example_api.py
```

Then access:
- API documentation: http://127.0.0.1:8000/docs
- llms.txt endpoint: http://127.0.0.1:8000/llms.txt

## License

This project is licensed under the MIT License.
