from __future__ import annotations

DEVELOPMENT_CI_TIMEOUT_MINUTES = 60


def render_development_ci(
    language: str,
    runtime: str,
    package_tool: str,
    build_command: str,
    test_command: str,
    *,
    efficiency_contract: bool = True,
) -> str:
    stack_text = " ".join([language, runtime, package_tool]).lower()
    uses_rust = "rust" in stack_text or "cargo" in stack_text

    if efficiency_contract:
        generated_intent_step = """      - name: Verify generated intent docs are in sync
        shell: bash
        run: |
          if [ -x ./scripts/render-intent-docs ] && [ -d .harness/commands ]; then
            mkdir -p .ci/generated-drift
            ./scripts/render-intent-docs
            if ! git diff --quiet -- .harness/commands/CONVERSATIONAL_MODE.md .harness/commands/COMMANDS.md; then
              echo "Generated intent docs are out of sync. Run ./scripts/render-intent-docs and commit the result."
              git diff --stat -- .harness/commands/CONVERSATIONAL_MODE.md .harness/commands/COMMANDS.md | tee .ci/generated-drift/summary.txt
              git diff --binary -- .harness/commands/CONVERSATIONAL_MODE.md .harness/commands/COMMANDS.md > .ci/generated-drift/generated-intent-docs.patch
              exit 1
            fi
          fi"""
    else:
        generated_intent_step = """      - name: Verify generated intent docs are in sync
        shell: bash
        run: |
          if [ -x ./scripts/render-intent-docs ] && [ -d .harness/commands ]; then
            ./scripts/render-intent-docs
            git diff --stat --exit-code || {
              echo "Generated intent docs are out of sync. Run ./scripts/render-intent-docs and commit the result."
              git diff -- .harness/commands/CONVERSATIONAL_MODE.md .harness/commands/COMMANDS.md
              exit 1
            }
          fi"""

    steps = [
        """      - name: Checkout
        uses: actions/checkout@v6""",
        '''      - name: Set up Python
        uses: actions/setup-python@v6
        with:
          python-version: "3.12"''',
        generated_intent_step,
    ]
    if efficiency_contract:
        steps.append(
            """      - name: Upload generated intent-doc drift
        if: failure()
        uses: actions/upload-artifact@v4
        with:
          name: generated-intent-doc-drift
          path: .ci/generated-drift
          if-no-files-found: ignore
          retention-days: 3"""
        )

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

    workflow_prefix = """name: CI

on:
  pull_request:
  push:
    branches:
      - main
  workflow_dispatch:
"""
    if efficiency_contract:
        workflow_prefix += """
concurrency:
  group: ${{ github.workflow }}-${{ github.event.pull_request.number || github.run_id }}
  cancel-in-progress: ${{ github.event_name == 'pull_request' }}
"""
    workflow_prefix += """
jobs:
  test-and-validate:
    runs-on: ubuntu-latest
"""
    if efficiency_contract:
        workflow_prefix += f"    timeout-minutes: {DEVELOPMENT_CI_TIMEOUT_MINUTES}\n"
    workflow_prefix += """    permissions:
      contents: read
    steps:
"""
    return workflow_prefix + "\n\n".join(steps) + "\n"


def _indented_run_block(command: str) -> str:
    return "\n".join(f"          {line}" if line.strip() else "" for line in command.splitlines())
