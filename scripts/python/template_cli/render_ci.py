from __future__ import annotations


def render_development_ci(
    language: str,
    runtime: str,
    package_tool: str,
    build_command: str,
    test_command: str,
) -> str:
    stack_text = " ".join([language, runtime, package_tool]).lower()
    uses_rust = "rust" in stack_text or "cargo" in stack_text

    steps = [
        """      - name: Checkout
        uses: actions/checkout@v6""",
        '''      - name: Set up Python
        uses: actions/setup-python@v6
        with:
          python-version: "3.12"''',
        """      - name: Verify generated intent docs are in sync
        shell: bash
        run: |
          if [ -x ./scripts/render-intent-docs ] && [ -d harness_commands ]; then
            ./scripts/render-intent-docs
            git diff --stat --exit-code || {
              echo "Generated intent docs are out of sync. Run ./scripts/render-intent-docs and commit the result."
              git diff -- harness_commands/CONVERSATIONAL_MODE.md harness_commands/COMMANDS.md
              exit 1
            }
          fi""",
    ]

    if uses_rust:
        steps.append(
            """      - name: Check Rust formatting
        shell: bash
        run: cargo fmt --check"""
        )

    steps.extend(
        [
            f"""      - name: Build project
        shell: bash
        run: |
{_indented_run_block(build_command)}""",
            f"""      - name: Test project
        shell: bash
        run: |
{_indented_run_block(test_command)}""",
            """      - name: Run governance validation
        shell: bash
        run: ./scripts/validate-governance""",
            """      - name: Run development validation
        shell: bash
        run: ./scripts/validate-development""",
        ]
    )

    return (
        """name: CI

on:
  pull_request:
  push:
    branches:
      - main
  workflow_dispatch:

jobs:
  test-and-validate:
    runs-on: ubuntu-latest
    permissions:
      contents: read
    steps:
"""
        + "\n\n".join(steps)
        + "\n"
    )


def _indented_run_block(command: str) -> str:
    return "\n".join(f"          {line}" if line.strip() else "" for line in command.splitlines())
