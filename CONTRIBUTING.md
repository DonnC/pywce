# Contributing to PyWCE

Thank you for considering contributing to PyWCE! 

By contributing, you're helping improve a robust tool designed for building WhatsApp chatbots and using WhatsApp Cloud APIs effortlessly.

---

## Getting Started

### Prerequisites
Ensure you have the following installed before contributing:
- Python 3.10+
- pip (Python package manager)
- An active [TEST] WhatsApp Cloud API setup with the necessary tokens and configurations.

### Setting Up the Project
1. Fork the repository on GitHub.
2. Clone your forked repository locally:
   ```bash
   git clone https://github.com/DonnC/pywce.git
   cd pywce
   ```
3. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
4. Install dependencies:
   ```bash
   # engine dependencies
   pip install -r requirements.txt
   
   # example dependencies
   cd example
   pip install -r requirements.txt
   ```

5. (Optional) Run tests to ensure your environment is working:
   ```bash
   pytest
   ```

---

## Contribution Workflow

### 1. Reporting Issues
If you encounter any bugs, feature requests, or documentation issues, please [open an issue](https://github.com/DonnC/pywce/issues).

### 2. Suggesting Features
Feel free to suggest new features or improvements to both:
- The **WhatsApp client library** (`pywce.whatsapp`) for direct interaction with the API.
- The **engine** for building chatbots using YAML-defined templates.

### 3. Making Changes
- Before you start coding, create a new branch for your changes:
  ```bash
  git checkout -b feature/my-new-feature
  ```
- Keep your changes modular and adhere to the existing coding style. 
- Ensure you add comments where necessary.

### 4. Running Tests
Write tests for your contributions in the `tests` folder. Use `pytest` to validate your changes:
```bash
pytest
```

### 5. Submitting Your Changes
- Commit your changes with meaningful messages:
  ```bash
  git commit -m "Add feature: Support for multiple template triggers"
  ```
- Push your branch to your forked repository:
  ```bash
  git push origin feature/my-new-feature
  ```
- Open a pull request from your branch to the `main` branch of the original repository.

---

## Code Style and Standards

### Python Code Style
This project uses **PEP8** standards. Use `flake8` or `black` to check code style:
```bash
pip install flake8 black
flake8 . && black .
```

### Writing Tests
All new features and bug fixes should include test coverage. 
Place your tests in the `tests/` directory. 
Use meaningful names for test files and functions.

---

## Special Contributions for PyWCE

### Extending the WhatsApp Client Library
The `pywce.whatsapp` module provides direct API integration. If you'd like to add more features:
- Use the `WhatsApp` class in `pywce/modules/whatsapp/__init__.py` as your base.
- Add well-documented methods for new API endpoints.

### Adding New Engine Features
The engine processes chatbot logic via YAML templates. When adding new engine capabilities:
- Add corresponding engine logic in corresponding folder under `pywce/src/`.
- Document new template options or hooks clearly in `README`.

---

## Getting Help
If you're stuck or have any questions, don't hesitate to open a discussion on the [GitHub Discussions page](https://github.com/DonnC/pywce/discussions).

Thank you for contributing to PyWCE!
```