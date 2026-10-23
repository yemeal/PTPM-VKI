# AGENTS.md

General guidelines and engineering rules for autonomous agents working in this repository.

## Work and Approvals

- Prioritize clear, direct communication: report results first, followed by essential details. Provide a concise plan before starting complex or multi-step tasks (behavior, affected boundaries, steps, and verification).
- Before making changes, inspect local documentation, configuration files, and check Git status. Preserve existing and uncommitted changes; operate strictly within the agreed task scope.
- Direct instructions grant permission to make changes within their necessary scope. Make routine, reversible decisions autonomously; do not repeatedly ask for confirmation on already agreed decisions.
- Always obtain explicit approval before:
  - Altering public APIs, database schemas, or serialized contracts;
  - Introducing new dependencies or build/lint tools;
  - Deleting existing files, public interfaces, or architectural boundaries (unless explicitly requested in the task).
- Audits and investigations conclude with clear findings and an actionable plan; perform code refactoring or bug fixes only after alignment. Continue independent permitted work while waiting for responses.

## Git and Delivery

- **Commit, `git push`, and pull request creation/publishing are strictly forbidden unless explicitly requested by the user for that specific action.**
- Directives to "implement", "fix", or "finish", general approval of a plan, green test suites, or CI delivery checklists do NOT constitute a request to commit, push, or open a PR. A request to commit does not imply permission to push or open a PR. Without explicit instructions, leave changes verified and uncommitted in the working tree.
- Each feature or task belongs to a dedicated branch with an informative name (e.g., `feat/<short-description>` or standard repository conventions).
- Commits must be atomic, focused, and ordered logically: one responsibility per commit, only related files included, never mixing feature code with unrelated cleanup.
- Conventional Commits standard: `type(scope): description`. Use `feat`, `fix`, `refactor`, `test`, `docs`, `chore`, `build`, `ci`, `perf`. Breaking changes must be marked with `!` or `BREAKING CHANGE:`.
- Check staged diff before committing. Never commit secrets, tokens, credentials, or private keys, including in test fixtures. Never rewrite Git history or execute destructive Git commands without explicit permission.

## TDD and Test Inviolability

- For features and bug fixes, apply Test-Driven Development (TDD) principles. Align on the expected public behavior and boundaries before authoring tests (an approved plan or task specification is sufficient).
- Work in vertical increments: write one behavior-focused test → observe expected RED → write minimal implementation → achieve GREEN → refactor. Do not write a massive suite of speculative tests upfront.
- **Report any test failure immediately:** command executed, specific test identifier, expected vs. actual behavior, and suspected root cause or working hypothesis.
- **Expected RED of a new test** (failing strictly because the agreed behavior is not yet implemented): report it and proceed with implementation according to the plan without altering the test.
- **Unexpected failure** (or RED for an unintended reason): halt edits in the affected area, provide diagnostics, and seek guidance before modifying production code to mask the failure.
- **Never modify existing tests without explicit approval:** assertions, fixtures, conftest, helpers, snapshots, moves/deletions, and markers (`skip`, `xfail`). This rule applies equally to tests authored by the agent earlier in the session. Never weaken test checks to achieve GREEN; preserve intentional RED test cases.
- Test observable behavior through public interfaces: return values, domain exceptions, and state transitions. Derive assertions from specifications and real-world examples, not by duplicating internal implementation logic. Never couple tests to private methods or implementation details.

## DDD and Hexagonal Architecture

- Model domain concepts explicitly with a Rich Domain Model combining state and business rules; entities and aggregates enforce and protect their own invariants. The application layer coordinates use cases, orchestrates ports, and manages transactions; business logic must never leak into handlers, controllers, HTTP layers, or persistence adapters.
- Dependencies point inward: `entrypoints → application → domain`; `infrastructure` implements application-defined ports. Domain must never import application services, transport frameworks, ORM models, DI containers, settings, or external clients. The application layer must never depend on concrete infrastructure adapters.
- Use structural subtyping (duck typing) for ports via `typing.Protocol`. Adapters satisfy port contracts by matching method signatures without requiring explicit inheritance.
- Pydantic in the domain is a deliberate architectural choice. Domain entities, ORM models, transport schemas, and application DTOs serve distinct roles; perform explicit transformations across boundaries using mappers. Pure DTOs are acceptable; anemic domain entities are not.
- Aggregate roots govern changes within their consistency boundary. Input format validation (e.g. at the HTTP schema level) does not replace domain invariant validation.
- Queries must not mutate observable business state. Commands explicitly express intention to change state.

## Python and Domain Modeling

- Python 3.14+ syntax: use modern type hints `T | None`, `list[T]`, `dict[K, V]`, `tuple[T, ...]`, `Self`, `Annotated`. Do not use legacy `Optional`, `Union`, `List`, `Dict`. Maintain strict typing; never use `Any`, casts, or type ignores as a substitute for valid types and proper validation.
- Leverage the domain base hierarchy:
  - `DomainModel`: immutable base without identity (`frozen=True`, `extra="forbid"`, `revalidate_instances="always"`), used for Value Objects;
  - `Entity`: models with identity (`id`) and creation timestamp (`created_at: datetime` in UTC);
  - `MutableEntity`: adds `updated_at` and safe state mutation via `_apply_changes(now=..., **changes)`;
  - `VersionedMutableEntity`: adds optimistic concurrency control with auto-incrementing `version: int = 1`.
- **Always-valid state:** instantiation, factory methods, and domain operations must guarantee that entities satisfy all invariants at all times. Express multi-field invariants in `@model_validator(mode="after")`. Validators must be deterministic and free of I/O or side effects.
- Mutate entities strictly through explicit business methods using `_apply_changes(now=..., **changes)`. The method creates and validates a candidate state first; if changes are identical to current state, it returns `False` (no-op detection) without advancing `updated_at`. If invariant validation fails, the entity state remains untouched (atomic rollback).
- Immutability by default: Value Objects are immutable instances with `create` or `from_*` factories. Direct field assignment on entities is forbidden (`frozen=True`).
- Never bypass invariants through private fields (`_field`), reflection, monkey-patching, `__dict__`, or `object.__setattr__` outside of established base model infrastructure.
- Standard `model_construct()` and `model_copy(update=...)` bypass validation; do not use them to modify or reconstruct domain entities without validation.
- Declare Pydantic defaults exclusively via `Field(default=...)` or `Field(default_factory=...)` with `validate_default=True`.
- Time must always be timezone-aware UTC. Reject naive datetimes; normalize valid offsets to UTC at system boundaries. Pass `now: datetime` explicitly to business methods to ensure determinism; never fetch current wall-clock time inside invariant checks.

## Pytest Organization

- Organize tests cleanly by architectural layer:
  - `tests/unit/domain/`: unit tests for domain entities, invariants, and value objects;
  - `tests/unit/application/`: unit tests for use cases and command handlers using port fakes/mocks;
  - `tests/unit/infrastructure/`: tests for concrete adapters (repositories, parsers) using isolated resources (e.g. in-memory SQLite, local fixtures);
  - `tests/integration/`: end-to-end component interactions, DI resolution, and API transport testing.
- Domain unit tests must execute purely in memory without databases or network calls. Application unit tests must isolate use cases using lightweight fakes or mocks.
- Keep tests fast, isolated, and deterministic: control time and IDs via ports; never rely on execution order, shared external state, real sleeps, or random data.
- Place fixtures in the nearest `conftest.py` with minimal required scope (`function`, `package`, `session`) and clean teardown. Use `@pytest.mark.parametrize` for table-driven scenarios with readable IDs.

## Clean, Simple, and Readable Code

- Write code as clean, communicative prose: descriptive, pronounceable names; small functions with a single responsibility and a single level of abstraction (SLAP). Follow project style; do not split code artificially just to satisfy arbitrary line counts.
- KISS and YAGNI: implement the minimal design required for current behavior without speculative features, premature generalization, or unnecessary boilerplate.
- SOLID principles:
  - Single Responsibility: one reason to change;
  - Open/Closed: extensible through defined variation points;
  - Liskov Substitution: subtyping contracts strictly preserved;
  - Interface Segregation: narrow, focused protocols;
  - Dependency Inversion: depend on abstractions (protocols), not concrete implementations.
- Comments must explain business rationale, algorithmic trade-offs, or external constraints. Clear up ambiguous code through better naming and structure rather than explanatory comments. Maintain informative docstrings for public contracts.
- Boy Scout Rule applies within the task scope: clean up unused imports, dead code, and temporary debug snippets without expanding the agreed blast radius or altering existing tests.
- Explicitly handle expected domain and infrastructure exceptions. Preserve root cause context (`raise ... from err`) when translating exceptions across layers. Never swallow unexpected errors or disguise failures as success. Validate untrusted inputs at boundaries. Never log secrets or sensitive payloads.

## Verification and Completion

- Run targeted checks during implementation. Before finishing any code change, execute:
  1. Code formatting and linting: `uv run ruff check` and `uv run ruff format --check`;
  2. Static type checking: `uv run ty check --error-on-warning`;
  3. Pre-commit hooks: `uv run prek run --all-files`;
  4. Test suite: `uv run pytest`.
- Definition of Done for code: all mandatory checks pass; formatters, linters, and type checkers report zero errors and zero warnings; no protected tests were weakened or diagnostics suppressed.
- Conclude work with a clear summary: what was changed, which verification commands were executed with results, any failing/skipped checks, and any remaining questions or next steps.

## Command Reference

All commands are executed from the repository root:

```powershell
# Environment synchronization
uv sync

# Git hooks management & execution
uv run prek install
uv run prek run --all-files
uv run prek run --stage pre-push --all-files

# Quality & Type checking
uv run ruff check --force-exclude
uv run ruff format --check --force-exclude
uv run ty check --error-on-warning

# Test execution
uv run pytest -q
uv run pytest --cov=src/app
```
