# Contributing to pyCycle

Thanks for contributing to pyCycle! This guide explains how to propose changes and the review process.

## Development Workflow
1. Create a feature branch.
2. Make changes with tests and documentation updates as needed.
3. Run local checks via the Makefile (see below).
4. Open a pull request with a clear description and rationale.

## Local Checks (uv)
Use the provided Makefile targets (all based on `uv run`):
- `make test`
- `make lint`
- `make format`
- `make docs`
- `make coverage`

## Review Requirements
- At least one maintainer approval is required before merge.
- CI checks must pass (tests + linting where applicable).
- Public API changes should include documentation updates.

## Code Ownership
Code ownership rules are defined in [`.github/CODEOWNERS`](.github/CODEOWNERS:1).

## Regression Data Updates
If changes impact element outputs, update regression data per [`docs/REGRESSION_DATA.md`](docs/REGRESSION_DATA.md:1).
