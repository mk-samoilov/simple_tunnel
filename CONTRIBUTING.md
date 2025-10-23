# Contributing to Easy Tunnel

Thank you for your interest in contributing to Easy Tunnel! This document provides guidelines for contributing to the project.

## How to Contribute

### Reporting Issues

If you find a bug or have a feature request:

1. Check if the issue already exists in the repository
2. Create a new issue with a clear title and description
3. Include steps to reproduce the problem (for bugs)
4. Specify your environment (OS, Python version)

### Submitting Changes

1. **Fork the repository** on GitHub
2. **Create a feature branch** from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make your changes** following the coding standards below
4. **Test your changes** thoroughly
5. **Commit your changes** with a clear commit message
6. **Push to your fork** and create a Pull Request

## Development Guidelines

### Code Style

- Follow PEP 8 Python style guidelines
- Use meaningful variable and function names
- Add comments for complex logic
- Keep functions focused and small

### Testing

- Test your changes with different scenarios
- Ensure the tunnel works with various local services
- Test connection handling and cleanup
- Verify error handling works correctly

### Security Considerations

Since this is a network tool, please consider:

- **Authentication**: Any security improvements are welcome
- **Encryption**: Consider adding TLS/SSL support
- **Input validation**: Ensure all inputs are properly validated
- **Error handling**: Don't expose sensitive information in error messages

## Areas for Improvement

### High Priority
- [ ] Add authentication mechanism
- [ ] Implement encryption (TLS/SSL)
- [ ] Add configuration file support [.ini]
- [ ] Improve error handling and logging
- [ ] Add connection timeout handling

### Medium Priority
- [ ] Add support for multiple concurrent tunnels
- [ ] Implement connection pooling
- [ ] Add metrics and monitoring
- [ ] Add systemd service files

### Low Priority
- [ ] Add GUI interface
- [ ] Create web-based management interface
- [ ] Add support for UDP tunneling
- [ ] Implement load balancing

## Pull Request Guidelines

### Before Submitting

1. **Test thoroughly**: Make sure your changes work as expected
2. **Update documentation**: Update README.md if needed
3. **Check compatibility**: Ensure changes work on different platforms
4. **Review your code**: Make sure it follows the project's style

### Pull Request Template

When creating a PR, please include:

- **Description**: What changes were made and why
- **Testing**: How you tested the changes
- **Breaking changes**: Any breaking changes and migration steps
- **Documentation**: Any documentation updates needed

### Commit Message Format

Use clear, descriptive commit messages:

```
feat: add authentication support
fix: handle connection timeout properly
docs: update installation instructions
refactor: improve error handling
```

## Development Setup

### Prerequisites

- Python 3.6 or higher
- Git

### Local Development

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/easy_tunnel.git
   cd easy_tunnel
   ```

2. Create a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies (if any are added in the future):
   ```bash
   pip install -r requirements.txt
   ```

### Testing Your Changes

1. **Test the server**:
   ```bash
   python3 et_serv.py --share-port 8080
   ```

2. **Test the client**:
   ```bash
   python3 client.py --serv-ip localhost --local-port 3000
   ```

3. **Test with a real service**:
   - Start a local web server on port 3000
   - Connect to localhost:8080 to verify tunneling works

## Code Review Process

1. **Automated checks**: All PRs will be checked for basic issues
2. **Manual review**: Maintainers will review the code
3. **Testing**: Changes will be tested in different environments
4. **Feedback**: Address any feedback from reviewers

## Community Guidelines

- Be respectful and constructive in discussions
- Help others learn and improve
- Follow the project's code of conduct
- Ask questions if you're unsure about anything

## Getting Help

If you need help:

1. Check existing issues and discussions
2. Create a new issue with the "question" label
3. Join our community discussions (if available)

## License

By contributing to Easy Tunnel, you agree that your contributions will be licensed under the GNU General Public License v3.0.

## Recognition

Contributors will be recognized in:
- CONTRIBUTORS.md file
- Release notes
- Project documentation

Thank you for contributing to Easy Tunnel! 🚀
