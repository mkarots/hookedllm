"""
Basic tests for hookedllm core functionality.

These tests demonstrate that the core system works without requiring
actual LLM API calls.
"""

import pytest
from unittest.mock import Mock, AsyncMock
from hookedllm.core.types import CallInput, CallOutput, CallContext, CallResult, Message
from hookedllm.core.rules import ModelRule, TagRule, CompositeRule
from hookedllm.core.scopes import InMemoryScopeHookStore, InMemoryScopeRegistry
from hookedllm.core.executor import DefaultHookExecutor


class TestTypes:
    """Test core data types."""
    
    def test_message_creation(self):
        """Test creating a Message."""
        msg = Message(role="user", content="Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"
    
    def test_call_input_creation(self):
        """Test creating CallInput."""
        call_input = CallInput(
            model="gpt-4",
            messages=[Message(role="user", content="Hello")],
            params={"temperature": 0.7},
            metadata={"user_id": "123"}
        )
        assert call_input.model == "gpt-4"
        assert len(call_input.messages) == 1
        assert call_input.params["temperature"] == 0.7
        assert call_input.metadata["user_id"] == "123"


class TestRules:
    """Test rule system."""
    
    def test_model_rule_matches(self):
        """Test ModelRule matching."""
        rule = ModelRule(["gpt-4", "gpt-4-turbo"])
        
        call_input = CallInput(
            model="gpt-4",
            messages=[Message(role="user", content="test")]
        )
        context = CallContext()
        
        assert rule.matches(call_input, context) is True
    
    def test_model_rule_no_match(self):
        """Test ModelRule when it doesn't match."""
        rule = ModelRule(["gpt-4"])
        
        call_input = CallInput(
            model="gpt-3.5-turbo",
            messages=[Message(role="user", content="test")]
        )
        context = CallContext()
        
        assert rule.matches(call_input, context) is False
    
    def test_tag_rule_matches(self):
        """Test TagRule matching."""
        rule = TagRule(["production"])
        
        call_input = CallInput(
            model="gpt-4",
            messages=[Message(role="user", content="test")]
        )
        context = CallContext(tags=["production", "critical"])
        
        assert rule.matches(call_input, context) is True
    
    def test_composite_rule_and(self):
        """Test AND composition of rules."""
        rule = ModelRule(["gpt-4"]) & TagRule(["production"])
        
        call_input = CallInput(
            model="gpt-4",
            messages=[Message(role="user", content="test")]
        )
        context = CallContext(tags=["production"])
        
        assert rule.matches(call_input, context) is True
    
    def test_composite_rule_or(self):
        """Test OR composition of rules."""
        rule = ModelRule(["gpt-4"]) | ModelRule(["gpt-3.5-turbo"])
        
        call_input = CallInput(
            model="gpt-3.5-turbo",
            messages=[Message(role="user", content="test")]
        )
        context = CallContext()
        
        assert rule.matches(call_input, context) is True
    
    def test_rule_negation(self):
        """Test NOT operator on rules."""
        rule = ~TagRule(["test"])
        
        call_input = CallInput(
            model="gpt-4",
            messages=[Message(role="user", content="test")]
        )
        context = CallContext(tags=["production"])
        
        assert rule.matches(call_input, context) is True


class TestScopes:
    """Test scope system."""
    
    def test_scope_hook_store_creation(self):
        """Test creating a scope hook store."""
        store = InMemoryScopeHookStore("test")
        assert store.name == "test"
    
    def test_add_and_get_hooks(self):
        """Test adding and retrieving hooks."""
        store = InMemoryScopeHookStore("test")
        
        async def my_hook(call_input, call_output, context):
            pass
        
        store.add_after(my_hook)
        hooks = store.get_after_hooks()
        
        assert len(hooks) == 1
        assert hooks[0][0] == my_hook
        assert hooks[0][1] is None  # No rule
    
    def test_scope_registry(self):
        """Test scope registry."""
        registry = InMemoryScopeRegistry()
        
        scope1 = registry.get_scope("test")
        scope2 = registry.get_scope("test")
        
        # Should return same instance
        assert scope1 is scope2
    
    def test_get_scopes_for_client(self):
        """Test getting scopes for a client."""
        registry = InMemoryScopeRegistry()
        
        # Get global + one scope
        scopes = registry.get_scopes_for_client(["test"])
        
        # Should have global + test
        assert len(scopes) == 2
    
    def test_get_scopes_for_client_multiple(self):
        """Test getting multiple scopes for a client."""
        registry = InMemoryScopeRegistry()
        
        scopes = registry.get_scopes_for_client(["test1", "test2"])
        
        # Should have global + test1 + test2
        assert len(scopes) == 3


@pytest.mark.asyncio
class TestExecutor:
    """Test hook executor."""
    
    async def test_execute_after_hook(self):
        """Test executing after hooks."""
        executor = DefaultHookExecutor()
        
        called = []
        
        async def my_hook(call_input, call_output, context):
            called.append(True)
        
        call_input = CallInput(
            model="gpt-4",
            messages=[Message(role="user", content="test")]
        )
        call_output = CallOutput(text="response", raw=None)
        context = CallContext()
        
        await executor.execute_after(
            [(my_hook, None)],
            call_input,
            call_output,
            context
        )
        
        assert len(called) == 1
    
    async def test_execute_hook_with_rule(self):
        """Test executing hook with matching rule."""
        executor = DefaultHookExecutor()
        
        called = []
        
        async def my_hook(call_input, call_output, context):
            called.append(True)
        
        rule = ModelRule(["gpt-4"])
        
        call_input = CallInput(
            model="gpt-4",
            messages=[Message(role="user", content="test")]
        )
        call_output = CallOutput(text="response", raw=None)
        context = CallContext()
        
        await executor.execute_after(
            [(my_hook, rule)],
            call_input,
            call_output,
            context
        )
        
        assert len(called) == 1
    
    async def test_hook_not_executed_when_rule_doesnt_match(self):
        """Test hook is not executed when rule doesn't match."""
        executor = DefaultHookExecutor()
        
        called = []
        
        async def my_hook(call_input, call_output, context):
            called.append(True)
        
        rule = ModelRule(["gpt-3.5-turbo"])
        
        call_input = CallInput(
            model="gpt-4",
            messages=[Message(role="user", content="test")]
        )
        call_output = CallOutput(text="response", raw=None)
        context = CallContext()
        
        await executor.execute_after(
            [(my_hook, rule)],
            call_input,
            call_output,
            context
        )
        
        assert len(called) == 0
    
    async def test_hook_failure_is_isolated(self):
        """Test that hook failures don't break execution."""
        executor = DefaultHookExecutor()
        
        async def failing_hook(call_input, call_output, context):
            raise ValueError("Hook failed!")
        
        async def working_hook(call_input, call_output, context):
            pass
        
        call_input = CallInput(
            model="gpt-4",
            messages=[Message(role="user", content="test")]
        )
        call_output = CallOutput(text="response", raw=None)
        context = CallContext()
        
        # Should not raise despite failing_hook raising
        await executor.execute_after(
            [(failing_hook, None), (working_hook, None)],
            call_input,
            call_output,
            context
        )


class TestIntegration:
    """Integration tests."""
    
    def test_full_flow_concept(self):
        """Test the conceptual flow of the system."""
        # This test demonstrates the flow without actual LLM calls
        
        # 1. Create registry and executor
        registry = InMemoryScopeRegistry()
        executor = DefaultHookExecutor()
        
        # 2. Register hook to a scope
        async def my_hook(call_input, call_output, context):
            pass
        
        eval_scope = registry.get_scope("evaluation")
        eval_scope.add_after(my_hook)
        
        # 3. Get scopes for a client
        scopes = registry.get_scopes_for_client(["evaluation"])
        
        # 4. Verify we have hooks
        all_hooks = []
        for scope in scopes:
            all_hooks.extend(scope.get_after_hooks())
        
        assert len(all_hooks) >= 1  # At least our hook