# Millennium Dawn Developer Guide

Welcome to the comprehensive development guide for Millennium Dawn, a modern-era Hearts of Iron IV modification that brings the complexities of contemporary geopolitics to your gaming experience.

- [Millennium Dawn Developer Guide](#millennium-dawn-developer-guide)
  - [About Millennium Dawn](#about-millennium-dawn)
  - [Quick Start](#quick-start)
    - [Essential Resources](#essential-resources)
    - [Development Environment Setup](#development-environment-setup)
      - [Python Installation](#python-installation)
      - [Pre-commit Setup](#pre-commit-setup)
  - [Development Standards](#development-standards)
    - [Code Style Guidelines](#code-style-guidelines)
    - [Quality Assurance](#quality-assurance)
  - [Community Contribution](#community-contribution)
    - [Open Development Philosophy](#open-development-philosophy)
    - [Getting Your Contributions Merged](#getting-your-contributions-merged)
  - [Access Levels and Responsibilities](#access-levels-and-responsibilities)
    - [Developer Access](#developer-access)
    - [Playtester Access](#playtester-access)
    - [Maintainer Privileges](#maintainer-privileges)
  - [Contributing Guidelines](#contributing-guidelines)
    - [For All Contributors](#for-all-contributors)
    - [Contribution Workflow](#contribution-workflow)
  - [Resources and Support](#resources-and-support)
    - [Development Resources](#development-resources)
    - [Getting Help](#getting-help)
  - [Acknowledgments](#acknowledgments)

## About Millennium Dawn

Millennium Dawn is an ambitious mod project spanning from the year 2000 to the present day and beyond. Our mod transforms Hearts of Iron IV with:

- **Modern Geopolitical Systems**: Experience realistic economic frameworks, political dynamics, and international relations
- **Advanced Mechanics**: National taxation systems, debt management, internal political factions, and influence networks
- **Rich Content**: Unique technology trees, focus trees, events, and decision paths tailored for the modern era
- **Enhanced Experience**: Original 3D models, custom soundtrack, and immersive gameplay elements

## Quick Start

### Essential Resources

- **[Discord Community](http://discord.gg/millenniumdawn)** - The Discord for the Millennium Dawn mod
- **[MD Git Instructions](https://docs.google.com/document/d/1V8DLowqEOSmlgazlHeC-hLZzLki5e6cWhQO_ZK6HVYs)** - Git Instructions for installing and setting up the repository
- **[Contribution Policies](./CONTRIBUTING.md)**

### Development Environment Setup

#### Python Installation

Python is required for running pre-commit hooks and other development tools. It is not required for developing Hearts of Iron IV scripts and/or fixing bugs or issues in the mod.

Please follow the [Python installation guides on the Python website](https://www.python.org/downloads/)

#### Pre-commit Setup

Pre-commit ensures code quality and consistency across contributions.

```bash
# Install pre-commit
pip install pre-commit

# Navigate to repository and install hooks
cd millennium-dawn
pre-commit install
```

## Development Standards

### Code Style Guidelines

**Localization Files (.yml):**

- Use 1-space indentation
- Remove trailing 0/1 after colons in string pairs
- Maintain consistent key formatting

**Script Files:**

- Use 1 tab indentation (equivalent to 4 spaces)
- Place comments above or below relevant code blocks
- Follow existing naming conventions

**Documentation:**

- Document all significant changes in the changelog
- Use clear, descriptive commit messages
- Include relevant context for complex changes

### Quality Assurance

Our development pipeline includes:

- **CWTools Integration**: Automated syntax checking and validation.
- **Pipeline Formatters**: Consistent code formatting across the project.
- **Python Script Validations**: Python script validators that are run in GitHub Actions or locally on a per user basis.
- **Pre-commit Hooks**: Automatic style enforcement and issue detection

## Community Contribution

### Open Development Philosophy

Millennium Dawn embraces community-driven development. We encourage:

- **Forking and Branching**: Create custom versions for experimentation
- **Submod Development**: Build extensions and specialized content
- **Feature Contributions**: Submit improvements via pull requests
- **Collaborative Development**: Work with our team on major features

### Getting Your Contributions Merged

1. **Fork the Repository**: Create your own development branch
2. **Follow Style Guidelines**: Ensure code meets our standards
3. **Test Thoroughly**: Verify functionality before submission
4. **Submit Pull Request**: Include detailed description of changes
5. **Engage with Reviews**: Respond to feedback and iterate as needed

## Access Levels and Responsibilities

### Developer Access

**New Developer Onboarding:**

- Initial access period: 2 months from join date
- Role-based permissions system
- Regular activity expected across all contribution types
- Access reviewed based on Discord engagement and contribution frequency

### Playtester Access

**Requirements:**

- Complete initial playtest within 48 hours of access
- Minimum one playtest monthly thereafter
- Provide detailed feedback reports with substantive analysis
- Document bugs, balance issues, and gameplay observations

### Maintainer Privileges

**Responsibilities:**

- Master branch push/pull access
- Merge request approval authority
- Code review and quality assurance
- Community guidance and mentorship

**Process:**
Contact council members via Discord for merge request reviews and approval workflows.

## Contributing Guidelines

### For All Contributors

1. **Add Yourself**: Include your information in [`AUTHORS.md`](./docs/misc/authors.md)
2. **Document Changes**: Update [`Changelog.txt`](./Changelog.txt) with your modifications
3. **Follow Conventions**: Adhere to established coding and documentation standards
4. **Stay Engaged**: Participate in community discussions and development planning

For details on our [AI Policy](./CONTRIBUTING.md#ai-policy)

### Contribution Workflow

```bash
# Fork repository and create feature branch
git checkout -b feature/your-feature-name

# Make changes following style guidelines
# Run pre-commit hooks
pre-commit run --all-files

# Commit with descriptive messages
git commit -m "feat: add modern economic indicators system"

# Push and create pull request
git push origin feature/your-feature-name
```

## Resources and Support

### Development Resources

- **Modding Resources**: Shared documentation and assets for team members
- **Style Guide**: This document and coding standards
- **Community Forums**: Discord channels for technical discussions
- **Documentation**: Comprehensive guides in the repository wiki

### Getting Help

- **Discord Community**: Active support channels for development questions
- **Mentorship Program**: Experienced developers available for guidance
- **Code Reviews**: Collaborative improvement process for all contributions
- **Documentation**: Extensive guides and examples in our resource library

---

## Acknowledgments

Millennium Dawn thrives because of our dedicated community of developers, playtesters, and contributors. Whether you're fixing a typo, implementing major features, or providing crucial feedback, every contribution matters.

Thank you for helping us create the definitive modern-era Hearts of Iron IV experience.

**— The Millennium Dawn Development Team**
