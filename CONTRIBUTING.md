# Contributing to DDA Toolkit

Thank you for considering contributing to the Database Development Assistant (DDA) toolkit!

## How to Contribute

### Reporting Bugs

If you find a bug, please open an issue with:
- Clear description of the bug
- Steps to reproduce
- Expected vs actual behavior
- Your environment (OS, Python version, MySQL version)

### Suggesting Features

Feature suggestions are welcome! Please open an issue describing:
- The feature and its benefits
- Use cases
- Proposed implementation (optional)

### Code Contributions

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```

3. **Make your changes**
   - Follow PEP 8 style guidelines
   - Add tests for new functionality
   - Update documentation as needed

4. **Run tests**
   ```bash
   pytest tests/
   ```

5. **Commit your changes**
   ```bash
   git commit -m "Add amazing feature"
   ```

6. **Push to your fork**
   ```bash
   git push origin feature/amazing-feature
   ```

7. **Open a Pull Request**

## Development Setup

```bash
# Clone your fork
git clone https://github.com/yourusername/dda-toolkit.git
cd dda-toolkit

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/
```

## Code Style

- Follow PEP 8
- Use type hints where appropriate
- Write docstrings for functions and classes
- Keep functions focused and small

## Testing

- Write tests for all new features
- Maintain or improve code coverage
- Use pytest for testing

## Documentation

- Update README.md for user-facing changes
- Update docstrings for code changes
- Add examples for new features

## Questions?

Feel free to open an issue for any questions about contributing.

Thank you for contributing!
