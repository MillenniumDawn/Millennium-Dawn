# Millennium Dawn's Contribution Guide

More details can be found under the `docs` directory or via the [team website](https://millenniumdawn.github.io/Millennium-Dawn/)

It helps to read code if it is written in a consistent style. Contributors to Millennium Dawn should agree to and adhere to our stylization and keep files consistent.

Stylization and other clean up contributions are more than welcome if they fix inconsistencies. The Millennium Dawn team does run CWTools and pipeline formatters that keep stylization consistent for the team. There are several other tools available under the the directory `tools/validation` for validating and linting more codebase.

## Table of Contents

- [Millennium Dawn's Contribution Guide](#millennium-dawns-contribution-guide)
  - [Table of Contents](#table-of-contents)
  - [Development Environment Setup](#development-environment-setup)
    - [Python Installation](#python-installation)
    - [Pre-commit Setup](#pre-commit-setup)
  - [Code Style Guidelines](#code-style-guidelines)
    - [Localization files (.yml)](#localization-files-yml)
    - [Code/Script Files](#codescript-files)
    - [Changelog](#changelog)
    - [Resources](#resources)
  - [Contributing](#contributing)
- [AI Policy](#ai-policy)
  - [AI Art Policy](#ai-art-policy)

## Development Environment Setup

### Python Installation

Python is required for running pre-commit hooks and other development tools. It is not required for developing Hearts of Iron IV scripts and/or fixing bugs or issues in the mod.

Please follow the [Python installation guides on the Python website](https://www.python.org/downloads/)

### Pre-commit Setup

Pre-commit helps automatically format code and catch issues before commits. It also ensures proper file hygiene while also integrating properly with other validations and scripts within the core repository.

**Installation:**

```bash
# Install pre-commit
pip install pre-commit

# Navigate to your Millennium Dawn repository
cd /path/to/millennium-dawn

# Install the pre-commit hooks
pre-commit install
```

**Usage:**

- Pre-commit will automatically run on each commit
- To manually run on all files: `pre-commit run --all-files`
- To update hooks: `pre-commit autoupdate`

## Code Style Guidelines

### Localization files (.yml)

- Indentation 1 space
- Remove all 0/1 after the : in string pairs. They break the formatting in various IDEs.

### Code/Script Files

- Indentation: 1 tab (4 spaces)
- Comments go above or below the code.
  - After will cause issues with several of the linters we have withing the team

### Changelog

All changes should be documented in the Changelog where applicable.

Changelog entries should follow the following standards:

- Full sentences describing the change
- No code language or references such as ENG that is not accessible to the common player

Jokes are allowed in the Changelog just try to ensure they are in good taste.

### Resources

- Resources or useful PDFs can be stored in the `resources` directory for all Millennium Dawn team members and other outside contributors.

## Contributing

When contributing to Millennium Dawn:

1. Ensure Python and pre-commit are installed
2. Follow the established code style guidelines
3. Run pre-commit hooks before submitting
4. Document changes in the changelog
5. Keep stylization consistent across files

For questions about style or setup, consult the team or refer to the `resources` or `docs` directories for more specific information.

# AI Policy

The Millennium Dawn team allows the use of AI-generated code and use of AI-generated localization for the correction of typos, grammar and other generation.
All work submitted via pull requests from forks or internal efforts must be your own work and cannot be generated content purely without review or any personal stylization.

## AI Art Policy

The Millennium Dawn team does not under any circumstance allow pure AI-generated imagery or artwork in the mod. All contributions must be your own work full stop.
Special circumstances such as generating side imageries for vehicles or futuristic components are possible, but are not intended to replace human work on the mod.
Any AI generations must be stylized, converted, and used by the artist to ensure quality and consistent standards across the assets within the mod.
