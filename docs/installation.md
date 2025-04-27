# Installation

This guide covers the different ways to install Voltar  in your Python environment.

## Requirements

Voltar  is designed to work with modern Python versions:

- Python 3.8 or higher
- No external dependencies for core functionality

## Installation Methods

### Using pip (Recommended)

The simplest way to install Voltar  is using pip:

```bash
pip install voltar -validator
```

To install the latest development version directly from GitHub:

```bash
pip install git+https://github.com/nexios/voltar .git
```

### Using Poetry

If you're using Poetry for dependency management:

```bash
poetry add voltar -validator
```

### Using pipenv

For Pipenv users:

```bash
pipenv install voltar -validator
```

## Optional Dependencies

Voltar 's core validation functionality has zero dependencies, but you can install optional packages for enhanced features:

### OpenAPI Support

For OpenAPI schema generation support:

```bash
pip install voltar -validator[openapi]
```

### Async Validation Performance

For enhanced async validation performance:

```bash
pip install voltar -validator[async]
```

### Web Framework Integration

For integration with web frameworks:

```bash
pip install voltar -validator[web]
```

### Install All Extensions

To install all optional dependencies:

```bash
pip install voltar -validator[all]
```

## Development Installation

If you want to contribute to Voltar  or install with development tools:

```bash
# Clone the repository
git clone https://github.com/nexios/voltar .git
cd voltar 

# Install in development mode with dev dependencies
pip install -e ".[dev]"
```

## Verifying Installation

After installation, you can verify that Voltar  is working correctly by running:

```python
from voltar  import String

# This should work without errors
validator = String()
result = validator.validate("Hello, Voltar !")
print(result)  # Should print: Hello, Voltar !
```

## Next Steps

Now that you have Voltar  installed, proceed to the [Quickstart](quickstart.md) guide to learn the basics of using Voltar  for data validation.

