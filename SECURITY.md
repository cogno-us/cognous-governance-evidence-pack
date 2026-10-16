# Security Policy

## Scope

Agent Governance Evidence Pack is a schema definition, validator, and markdown renderer. It processes JSON input files and produces markdown output. It does not:

- Enforce runtime access control
- Connect to external services
- Store or transmit data
- Execute agent actions
- Certify compliance with any regulatory framework

It is a documentation and formatting tool.

## Security properties

- **No external calls** — the renderer and validator make no network requests.
- **No credential handling** — this package does not handle secrets, API keys, or authentication tokens. Do not put credentials in evidence pack files.
- **No code execution** — evidence pack files are declarative JSON. They are not executed.
- **Input admission and parsing** — JSON files are read under a byte budget, and duplicate keys, nonfinite numbers and excessive nesting are rejected. Pydantic v2 then parses the result into the Python models and raises errors for missing required fields and values it cannot convert.
- **Model parsing is not schema conformance** — the Python models are more permissive than the published JSON schemas. They ignore unknown fields, including misspelled field names, and coerce compatible scalars, for example the string `"true"` to a boolean. A document that loads and passes `agep validate` may still not conform to the published schemas. Validate against the schemas separately if you need that.
- **Hand-authored fields are caller assertions** — review status, review decisions, `signed`, `redacted`, validation status, validation counts and redaction/export records in a hand-authored pack are recorded as supplied. Semantic validation checks only their internal consistency (for example, that an approved status has a matching review record). It does not authenticate reviewers, verify signatures, check redaction or re-run validation. The renderer labels these fields "(asserted, unverified)".

## Recommended use

This tool should be combined with:

- Runtime policy gates and application authorization controls
- Audit logging and monitoring for agent actions
- Operational security controls for systems the agent accesses
- Legal review for regulatory compliance requirements
- Compliance review by qualified professionals

This tool does not replace any of the above.

## Reporting a vulnerability

If you discover a security vulnerability in this repository, please open a GitHub issue or contact the maintainers directly. Do not include exploit details in public issues.

For vulnerabilities in dependencies, please check the GitHub Advisory Database and open a pull request updating the affected dependency.
