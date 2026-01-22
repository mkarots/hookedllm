# Security Policy

## Supported Versions

We actively support the following versions with security updates:

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability, please **do not** open a public issue. Instead, please report it privately to maintainers via email or through a private security advisory.

### What to Report

Please report:
- Security vulnerabilities that could affect users
- Issues that could lead to data exposure or unauthorized access
- Problems with dependency management that introduce security risks

### What NOT to Report

Please do not report:
- Issues that require physical access to the system
- Issues that require social engineering
- Issues that require already compromised credentials
- Denial of service attacks (unless they expose a vulnerability)

### Response Timeline

- **Initial Response**: Within 48 hours
- **Status Update**: Within 7 days
- **Fix Timeline**: Depends on severity, but we aim for:
  - Critical: As soon as possible (typically within 7 days)
  - High: Within 30 days
  - Medium/Low: Next planned release

### Disclosure Policy

We follow responsible disclosure:
1. Reporter privately reports the vulnerability
2. Maintainers confirm and assess the issue
3. A fix is developed and tested
4. A security advisory is published with the fix
5. Credit is given to the reporter (if desired)

## Security Best Practices

When using HookedLLM:

1. **Never commit API keys or secrets**: Always use environment variables
2. **Keep dependencies updated**: Regularly update HookedLLM and its dependencies
3. **Review hook code**: Ensure custom hooks don't expose sensitive data
4. **Use scopes appropriately**: Isolate hooks to prevent unintended data access
5. **Validate inputs**: Don't trust data from hooks without validation

## Dependencies

HookedLLM has minimal dependencies by design. The core package has zero dependencies. Optional dependencies are clearly documented and can be reviewed in `pyproject.toml`.

We regularly review and update dependencies for security patches.

## Thank You

Thank you for helping keep HookedLLM and its users safe!

