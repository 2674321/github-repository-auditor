# Security Policy

Repository Health Auditor is a read-only auditing tool. It should never require repository credentials to be committed to this repository.

## Reporting a vulnerability

Please report security issues privately to the maintainer through a private contact method available on the GitHub profile. Do not publish tokens, credentials, private repository contents, or exploit details in a public issue.

## Repository data

Tests and examples must use synthetic repository data. Do not commit:

- GitHub tokens, PATs, OAuth credentials, SSH private keys or service-account files;
- private repository exports or copied source trees;
- .env files containing credentials;
- reports containing secrets discovered in audited repositories.

The auditor itself is designed to inspect repository metadata and local working trees. Audit output should be treated according to the sensitivity of the repository being inspected.
