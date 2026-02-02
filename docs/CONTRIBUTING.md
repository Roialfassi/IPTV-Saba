# Contributing to IPTV-Saba

Thank you for your interest in contributing to IPTV-Saba! This guide will help you get started.

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help others learn and grow

## How to Contribute

### Reporting Bugs

1. Check existing issues first
2. Create a new issue with:
   - Clear title
   - Steps to reproduce
   - Expected vs actual behavior
   - System information (OS, Python version, VLC version)
   - Log output if available

### Suggesting Features

1. Check existing feature requests
2. Create a new issue with:
   - Clear description of the feature
   - Use case / motivation
   - Possible implementation approach
   - Mockups if applicable

### Submitting Code

#### 1. Fork and Clone

```bash
git clone https://github.com/YOUR-USERNAME/IPTV-Saba.git
cd IPTV-Saba
```

#### 2. Create Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/bug-description
```

#### 3. Make Changes

- Follow the coding style (see CLAUDE.md)
- Add tests if applicable
- Update documentation
- Keep commits focused

#### 4. Test

```bash
cd src
python iptv_app.py
python ../test_simple.py
```

#### 5. Commit

Use conventional commit messages:

```
feat: add channel thumbnail support
fix: resolve fullscreen black screen
refactor: extract styles to utility module
docs: update API reference
test: add unit tests for ProfileManager
```

#### 6. Push and Create PR

```bash
git push -u origin feature/your-feature-name
```

Create a Pull Request with:
- Clear title
- Description of changes
- Related issue numbers
- Screenshots if UI changes

## Coding Guidelines

### Python Style

- PEP 8 compliant
- 4 spaces indentation
- Max 100 characters per line
- Type hints for functions

### Documentation

- Docstrings for all public methods
- Update relevant docs/ files
- Comment complex logic

### Testing

- Test new features manually
- Add unit tests when possible
- Don't break existing functionality

## Architecture Guidelines

### MVC Pattern

- **Models** (`src/model/`): Data structures only
- **Views** (`src/view/`): UI components, no business logic
- **Controller** (`src/controller/`): Business logic, coordinates model and view

### Signal/Slot Pattern

- Views emit signals
- Controller handles signals
- Avoid direct method calls from view to model

### Thread Safety

- Use locks for shared data
- Use signals for cross-thread communication
- Use worker threads for heavy operations

## Pull Request Checklist

- [ ] Code follows style guide
- [ ] Self-review completed
- [ ] Tests pass
- [ ] Documentation updated
- [ ] No merge conflicts
- [ ] Commit messages are clear

## Review Process

1. Maintainer reviews code
2. Feedback addressed
3. Tests pass
4. Documentation complete
5. Merge approved

## Getting Help

- Create an issue for questions
- Check existing documentation
- Review CLAUDE.md for detailed guidelines

## Recognition

Contributors will be acknowledged in:
- README.md
- Release notes
- GitHub contributors page

Thank you for contributing!
