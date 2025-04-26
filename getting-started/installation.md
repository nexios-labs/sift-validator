# Installation

This guide covers the different ways to install Sift in your Python environment.

## Requirements

Sift is designed to work with modern Python versions:

- Python 3.8 or higher
- No external dependencies for core functionality

## Installation Methods

### Using pip (Recommended)

The simplest way to install Sift is using pip:

```bash
pip install sift-validator
```

To install the latest development version directly from GitHub:

```bash
pip install git+https://github.com/nexios/sift.git
```

### Using Poetry

If you're using Poetry for dependency management:

```bash
poetry add sift-validator
```

### Using pipenv

For Pipenv users:

```bash
pipenv install sift-validator
```

## Optional Dependencies

Sift's core validation functionality has zero dependencies, but you can install optional packages for enhanced features:

### OpenAPI Support

For OpenAPI schema generation support:

```bash
pip install sift-validator[openapi]
```

### Async Validation Performance

For enhanced async validation performance:

```bash
pip install sift-validator[async]
```

### Web Framework Integration

For integration with web frameworks:

```bash
pip install sift-validator[web]
```

### Install All Extensions

To install all optional dependencies:

```bash
pip install sift-validator[all]
```

## Development Installation

If you want to contribute to Sift or install with development tools:

```bash
# Clone the repository
git clone https://github.com/nexios/sift.git
cd sift

# Install in development mode with dev dependencies
pip install -e ".[dev]"
```

## Verifying Installation

After installation, you can verify that Sift is working correctly by running:

```python
from sift import String

# This should work without errors
validator = String()
result = validator.validate("Hello, Sift!")
print(result)  # Should print: Hello, Sift!
```

## Next Steps

Now that you have Sift installed, proceed to the [Quickstart](quickstart.md) guide to learn the basics of using Sift for data validation.

