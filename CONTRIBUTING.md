# Style Guide

It helps to read code if it is written in a consistent style. Contributors to Millennium Dawn should agree to and adhere to our stylization and keep files consistent.

Stylization and other clean up contributions are more than welcome if they fix inconsistencies. The Millennium Dawn team does run CWTools and pipeline formatters that keep stylization consistent for the team.

## Development Environment Setup

### Python Installation

Python is required for running pre-commit hooks and other development tools.

**Windows:**
1. Download Python from [python.org](https://www.python.org/downloads/)
2. During installation, check "Add Python to PATH"
3. Verify installation by opening Command Prompt and running:
   ```bash
   python --version
   ```

**macOS:**
1. Install using Homebrew (recommended):
   ```bash
   brew install python
   ```
2. Or download from [python.org](https://www.python.org/downloads/)
3. Verify installation:
   ```bash
   python3 --version
   ```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install python3 python3-pip
```

### Pre-commit Setup

Pre-commit helps automatically format code and catch issues before commits.

**Installation:**
```bash
# Install pre-commit
pip install pre-commit

# Navigate to your Millennium Dawn repository
cd /path/to/millennium-dawn

# Install the pre-commit hooks
pre-commit install
```

**Configuration:**
The repository should include a `.pre-commit-config.yaml` file. If it doesn't exist, create one with appropriate hooks for your file types.

**Usage:**
- Pre-commit will automatically run on each commit
- To manually run on all files: `pre-commit run --all-files`
- To update hooks: `pre-commit autoupdate`

## Code Style Guidelines

### Localization files (.yml)
- indent 1 space
- Remove all 0/1 after the : in string pairs

### Code/Script Files
- indent: 1 tab (4 spaces)
- Comments go above or below the code

### Changelog
- All changes should be documented in the changelog where applicable

### Resources
- Resources or useful PDFs can be stored in Modding Resources for all Millennium Dawn team members

## Contributing

When contributing to Millennium Dawn:

1. Ensure Python and pre-commit are installed
2. Follow the established code style guidelines
3. Run pre-commit hooks before submitting
4. Document changes in the changelog
5. Keep stylization consistent across files

For questions about style or setup, consult the team or refer to the Modding Resources.
