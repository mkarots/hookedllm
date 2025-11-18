# Architecture Guide

HookedLLM follows SOLID principles with full dependency injection support.

## Design Principles

- **SRP**: Each component has a single responsibility
- **OCP**: Open for extension, closed for modification
- **LSP**: Implementations are interchangeable
- **ISP**: Focused, minimal interfaces
- **DIP**: Depend on abstractions, not concretions

## Component Overview

```
HookedLLMContext (DI Container)
├── Registry (Protocol) → InMemoryRegistry
└── Executor (Protocol) → DefaultExecutor
```

## Execution Model

Hooks execute sequentially (not in parallel). Each hook is awaited before the next starts.

**Async benefits**: Non-blocking I/O, concurrent LLM calls, efficient resource usage.

## Scope Isolation

- Each scope maintains its own hook list
- Clients opt into scopes
- Global hooks run for all clients
- Scopes created on-demand

## Error Handling

Hook failures never break LLM calls. Exceptions are caught and logged.

## Thread Safety

- **Registry**: NOT thread-safe - register hooks at startup
- **Hook execution**: Safe for concurrent calls
- Each call has its own context

See [lifecycle.md](lifecycle.md) for details.

## Extension Points

- Custom executors (error handling, logging)
- Custom registries (persistent storage, thread-safe)
- Custom rules (conditional execution)

See [dependency-injection.md](dependency-injection.md) for customization.
