from fastapi import FastAPI, Path, Query, Body, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

# Import the llms-txt plugin
from fastapi_llms_txt import add_llms_txt

# Create FastAPI app
app = FastAPI(
    title="Bookstore API",
    description="A sample API for managing a bookstore",
    version="1.0.0"
)

# OAuth2 setup for auth examples
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


# Models
class Genre(str, Enum):
    FICTION = "fiction"
    NON_FICTION = "non-fiction"
    SCIENCE_FICTION = "sci-fi"
    MYSTERY = "mystery"
    BIOGRAPHY = "biography"


class Book(BaseModel):
    id: Optional[int] = None
    title: str = Field(..., description="The title of the book")
    author: str = Field(..., description="The author of the book")
    genre: Genre = Field(..., description="The genre of the book")
    year_published: int = Field(..., description="The year the book was published")
    price: float = Field(..., description="The price of the book in USD")

    class Config:
        schema_extra = {
            "example": {
                "title": "The Great Gatsby",
                "author": "F. Scott Fitzgerald",
                "genre": "fiction",
                "year_published": 1925,
                "price": 12.99
            }
        }


class BookUpdate(BaseModel):
    title: Optional[str] = Field(None, description="The title of the book")
    author: Optional[str] = Field(None, description="The author of the book")
    genre: Optional[Genre] = Field(None, description="The genre of the book")
    year_published: Optional[int] = Field(None, description="The year the book was published")
    price: Optional[float] = Field(None, description="The price of the book in USD")


# Mock database
books_db = [
    Book(id=1, title="To Kill a Mockingbird", author="Harper Lee", genre=Genre.FICTION, year_published=1960, price=14.99),
    Book(id=2, title="1984", author="George Orwell", genre=Genre.SCIENCE_FICTION, year_published=1949, price=11.99),
    Book(id=3, title="The Autobiography of Benjamin Franklin", author="Benjamin Franklin", genre=Genre.BIOGRAPHY, year_published=1793, price=17.50),
]


# Dependency to verify token
async def get_current_user(token: str = Depends(oauth2_scheme)):
    # This is a mock implementation - in a real app you'd validate the token
    return {"username": "testuser", "permissions": ["read", "write"]}


# Endpoints
@app.get("/", summary="Root endpoint", description="Returns a welcome message.")
async def root():
    """
    Root endpoint that returns a welcome message.
    """
    return {"message": "Welcome to the Bookstore API!"}


@app.get("/books", response_model=List[Book], summary="Get all books", description="Returns a list of all books in the database.")
async def get_books(
    genre: Optional[Genre] = Query(None, description="Filter books by genre"),
    min_price: Optional[float] = Query(None, description="Minimum price filter"),
    max_price: Optional[float] = Query(None, description="Maximum price filter")
):
    """
    Get all books with optional filtering by genre and price.
    
    This endpoint allows you to retrieve all books in the database and apply 
    filters based on genre, minimum price, and maximum price.
    """
    filtered_books = books_db
    
    if genre:
        filtered_books = [book for book in filtered_books if book.genre == genre]
    
    if min_price is not None:
        filtered_books = [book for book in filtered_books if book.price >= min_price]
    
    if max_price is not None:
        filtered_books = [book for book in filtered_books if book.price <= max_price]
    
    return filtered_books


@app.get("/books/{book_id}", response_model=Book, summary="Get a book by ID", description="Returns detailed information about a specific book.")
async def get_book(book_id: int = Path(..., description="The ID of the book to retrieve", gt=0)):
    """
    Get a specific book by its ID.
    
    Retrieves detailed information about a book using its unique identifier.
    Returns a 404 error if the book is not found.
    """
    for book in books_db:
        if book.id == book_id:
            return book
    
    raise HTTPException(status_code=404, detail="Book not found")


@app.post("/books", response_model=Book, status_code=status.HTTP_201_CREATED, summary="Create a new book", description="Adds a new book to the database.")
async def create_book(
    book: Book = Body(..., description="The book information to add"),
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new book in the database.
    
    Requires authentication. The book will be assigned a new unique ID.
    """
    # Find the highest existing ID and increment by 1
    max_id = max([book.id for book in books_db]) if books_db else 0
    new_book = book.copy(update={"id": max_id + 1})
    books_db.append(new_book)
    return new_book


@app.put("/books/{book_id}", response_model=Book, summary="Update a book", description="Updates an existing book's information.")
async def update_book(
    book_id: int = Path(..., description="The ID of the book to update", gt=0),
    book_update: BookUpdate = Body(..., description="The updated book information"),
    current_user: dict = Depends(get_current_user)
):
    """
    Update an existing book's information.
    
    Requires authentication. Only the fields provided will be updated.
    Returns a 404 error if the book is not found.
    """
    for i, book in enumerate(books_db):
        if book.id == book_id:
            update_data = book_update.dict(exclude_unset=True)
            updated_book = book.copy(update=update_data)
            books_db[i] = updated_book
            return updated_book
    
    raise HTTPException(status_code=404, detail="Book not found")


@app.delete("/books/{book_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a book", description="Removes a book from the database.")
async def delete_book(
    book_id: int = Path(..., description="The ID of the book to delete", gt=0),
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a book from the database.
    
    Requires authentication. Returns a 404 error if the book is not found.
    """
    for i, book in enumerate(books_db):
        if book.id == book_id:
            books_db.pop(i)
            return
    
    raise HTTPException(status_code=404, detail="Book not found")


@app.post("/token", summary="Login", description="Authenticate and get an access token.")
async def login(username: str = Body(...), password: str = Body(...)):
    """
    Authenticate user and return an access token.
    
    This is a mock implementation for demonstration purposes.
    """
    # In a real app, you would validate credentials here
    return {"access_token": "mock_token", "token_type": "bearer"}


# Add llms.txt endpoint
add_llms_txt(
    app,
    title="Bookstore API",
    summary="An API for managing a bookstore catalog with books, authors, and genres.",
    notes=[
        "This API requires authentication for all write operations.",
        "All prices are in USD.",
        "The database is reset when the server restarts."
    ],
    sections={
        "Documentation": [
            {"title": "API Documentation", "url": "https://example.com/bookstore-api/docs"},
            {"title": "OpenAPI Spec", "url": "https://example.com/bookstore-api/openapi.json"}
        ],
        "SDKs": [
            {"title": "Python SDK", "url": "https://github.com/example/bookstore-python-sdk"},
            {"title": "JavaScript SDK", "url": "https://github.com/example/bookstore-js-sdk"}
        ]
    }
)


# Run the application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)