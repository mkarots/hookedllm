LLM Hooks — MVP Technical Spec (Async, Minimal LOC)
1) Objectives (non-negotiables)

Intercept every LLM call (prompt+params → response) with before/after/error/finally hooks.

Async-first, zero external deps, deterministic order, never let a hook break the call.

Provider-agnostic via a tiny AsyncLLMProvider protocol.

DX: one constructor + one chat() method. Everything else is optional.

Simplicity & Clarity: single, obvious way to do things; minimal public surface.

2) Public API (what devs touch)

HookedLLM(provider, hooks) → await .chat(call_in)

AsyncHookManager → register_before/after/error/finally

AsyncLLMProvider → must implement async def chat(call_in, ctx) -> CallOutput

3) Data Model (stable types)

Message{role, content}

CallInput{model, messages, params, metadata}

CallOutput{text, raw, usage, finish_reason}

CallContext{call_id, provider, route, tags, started_at}

CallResult{input, output, context, error, ended_at, elapsed_ms}

4) Execution Semantics (precise)

For a single call:

before hooks run in registration order.

Provider executes.

If success → after hooks (order preserved).

If error or cancellation → error hooks (order preserved), then re-raise.

In all cases → finally hooks receive CallResult.

Hook failures are caught and ignored (logged if you wire logging); they never affect the core result.

5) Laws / Invariants

Ordering: if h_i registered before h_j, then h_i executes before h_j within the same phase.

Isolation: hook exceptions do not escape; provider result semantics preserved.

Totality of finally: finally runs on success, error, and CancelledError.

Idempotent API: registering no hooks == a direct provider call.

6) Minimal Reference Implementation (single file)

Copy-paste as llmhooks.py. Split later if desired. No external deps.

# llmhooks.py
from __future__ import annotations
import asyncio, time
from typing import Any, Dict, List, Optional, Sequence, Protocol, Callable, Awaitable
from dataclasses import dataclass, field
from uuid import uuid4
from datetime import datetime, timezone

# ---------- Data types ----------
@dataclass(frozen=True)
class Message:
    role: str
    content: Any

@dataclass
class CallInput:
    model: str
    messages: Sequence[Message]
    params: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class CallOutput:
    text: Optional[str]
    raw: Any
    usage: Optional[Dict[str, Any]] = None
    finish_reason: Optional[str] = None

@dataclass
class CallContext:
    call_id: str = field(default_factory=lambda: str(uuid4()))
    parent_id: Optional[str] = None
    provider: str = ""
    route: str = "chat"
    tags: List[str] = field(default_factory=list)
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

@dataclass
class CallResult:
    input: CallInput
    output: Optional[CallOutput]
    context: CallContext
    error: Optional[BaseException]
    ended_at: datetime
    elapsed_ms: float

# ---------- Hook protocols ----------
class BeforeHook(Protocol):
    async def __call__(self, call_in: CallInput, ctx: CallContext) -> None: ...

class AfterHook(Protocol):
    async def __call__(self, call_in: CallInput, out: CallOutput, ctx: CallContext) -> None: ...

class ErrorHook(Protocol):
    async def __call__(self, call_in: CallInput, err: BaseException, ctx: CallContext) -> None: ...

class FinallyHook(Protocol):
    async def __call__(self, result: CallResult) -> None: ...

HookPredicate = Callable[[CallInput, CallContext], bool]

# ---------- Hook manager ----------
class AsyncHookManager:
    def __init__(self) -> None:
        self._before: List[tuple[BeforeHook, Optional[HookPredicate]]] = []
        self._after:  List[tuple[AfterHook, Optional[HookPredicate]]] = []
        self._error:  List[tuple[ErrorHook, Optional[HookPredicate]]] = []
        self._finally: List[FinallyHook] = []

    def register_before(self, h: BeforeHook, *, when: Optional[HookPredicate]=None) -> None:
        self._before.append((h, when))

    def register_after(self, h: AfterHook, *, when: Optional[HookPredicate]=None) -> None:
        self._after.append((h, when))

    def register_error(self, h: ErrorHook, *, when: Optional[HookPredicate]=None) -> None:
        self._error.append((h, when))

    def register_finally(self, h: FinallyHook) -> None:
        self._finally.append(h)

    async def run_before(self, call_in: CallInput, ctx: CallContext) -> None:
        for h, pred in self._before:
            if pred is None or pred(call_in, ctx):
                try: await h(call_in, ctx)
                except Exception: pass

    async def run_after(self, call_in: CallInput, out: CallOutput, ctx: CallContext) -> None:
        for h, pred in self._after:
            if pred is None or pred(call_in, ctx):
                try: await h(call_in, out, ctx)
                except Exception: pass

    async def run_error(self, call_in: CallInput, err: BaseException, ctx: CallContext) -> None:
        for h, pred in self._error:
            if pred is None or pred(call_in, ctx):
                try: await h(call_in, err, ctx)
                except Exception: pass

    async def run_finally(self, result: CallResult) -> None:
        for h in self._finally:
            try: await h(result)
            except Exception: pass

# ---------- Provider protocol ----------
class AsyncLLMProvider(Protocol):
    provider_name: str
    async def chat(self, call_in: CallInput, ctx: CallContext) -> CallOutput: ...

# ---------- Hooked client ----------
class HookedLLM:
    def __init__(self, provider: AsyncLLMProvider, hooks: AsyncHookManager, *,
                 default_timeout_s: Optional[float]=None) -> None:
        self.provider = provider
        self.hooks = hooks
        self.default_timeout_s = default_timeout_s

    async def chat(self, call_in: CallInput, *, ctx: Optional[CallContext]=None,
                   timeout_s: Optional[float]=None) -> CallOutput:
        ctx = ctx or CallContext(provider=getattr(self.provider, "provider_name", "unknown"))
        t0 = time.perf_counter()
        out: Optional[CallOutput] = None
        err: Optional[BaseException] = None
        try:
            await self.hooks.run_before(call_in, ctx)
            coro = self.provider.chat(call_in, ctx)
            timeout = timeout_s if timeout_s is not None else self.default_timeout_s
            out = await (asyncio.wait_for(coro, timeout) if timeout else coro)
            await self.hooks.run_after(call_in, out, ctx)
            return out
        except BaseException as e:
            err = e
            try: await self.hooks.run_error(call_in, e, ctx)
            finally: raise
        finally:
            elapsed = (time.perf_counter() - t0) * 1000.0
            result = CallResult(
                input=call_in, output=out, context=ctx, error=err,
                ended_at=datetime.now(timezone.utc), elapsed_ms=elapsed
            )
            await self.hooks.run_finally(result)

# providers_openai_async.py (illustrative sketch)
class OpenAIAsyncProvider:
    provider_name = "openai"
    def __init__(self, client): self.client = client

    async def chat(self, call_in: CallInput, ctx: CallContext) -> CallOutput:
        resp = await self.client.chat.completions.create(
            model=call_in.model,
            messages=[m.__dict__ for m in call_in.messages],
            **call_in.params
        )
        text = getattr(resp.choices[0].message, "content", None)
        usage = getattr(resp, "usage", None)
        finish = getattr(resp.choices[0], "finish_reason", None)
        return CallOutput(text=text, raw=resp, usage=usage, finish_reason=finish)

# A simple metrics hook (after)
class UsageMetrics:
    def __init__(self, counter: Dict[str,int]): self.counter = counter
    async def __call__(self, call_in: CallInput, out: CallOutput, ctx: CallContext) -> None:
        t = (out.usage or {}).get("total_tokens", 0)
        self.counter["tokens"] = self.counter.get("tokens", 0) + int(t)

# HTTP forwarder (finally) – stubbed without deps
class StdoutForwarder:
    async def __call__(self, result: CallResult) -> None:
        print({
            "call_id": result.context.call_id,
            "provider": result.context.provider,
            "model": result.input.model,
            "elapsed_ms": result.elapsed_ms,
            "error": type(result.error).__name__ if result.error else None
        })

# app.py
hooks = AsyncHookManager()
hooks.register_after(UsageMetrics(counter := {}))
hooks.register_finally(StdoutForwarder())

provider = OpenAIAsyncProvider(client=openai_async_client)
llm = HookedLLM(provider, hooks, default_timeout_s=30)

out = await llm.chat(
    CallInput(
        model="gpt-4o-mini",
        messages=[Message(role="user", content="Hi!")],
        params={"temperature": 0.2},
        metadata={"user_id": "u-1"}
    )
)
print(out.text)

