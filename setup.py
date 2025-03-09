import os

from setuptools import find_packages, setup

# Read readme file using context manager
readme_path = "readme.md"
if os.path.exists(readme_path):
    with open(readme_path, "r", encoding="utf-8") as f:
        long_description = f.read()
else:
    long_description = ""

setup(
    name="fastapi-llms-txt",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.68.0",
        "pydantic>=1.8.0",
    ],
    author="Your Name",
    author_email="your.email@example.com",
    description="FastAPI plugin to dynamically generate an /llms.txt route",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/fastapi-llms-txt",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
)
