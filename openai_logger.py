"""
OpenAI Request/Response Logger

This module provides comprehensive logging of all OpenAI API interactions.
It logs both requests (prompts/messages) and responses (completions).

Usage:
    from openai_logger import setup_openai_logging
    setup_openai_logging()  # Call before making any OpenAI calls

The logs are written to:
    - Console (formatted output)
    - openai_requests.log (file for later analysis)
"""

import json
import logging
import os
from datetime import datetime
from functools import wraps
from typing import Any

# Create a dedicated logger for OpenAI interactions
logger = logging.getLogger("openai_traffic")
logger.setLevel(logging.DEBUG)

# File handler - logs everything to a file
LOG_FILE = os.getenv("OPENAI_LOG_FILE", "openai_requests.log")
file_handler = logging.FileHandler(LOG_FILE, mode='a', encoding='utf-8')
file_handler.setLevel(logging.DEBUG)
file_formatter = logging.Formatter(
    '%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

# Console handler - formatted output
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
logger.addHandler(console_handler)


def format_messages(messages: list) -> str:
    """Format chat messages for logging."""
    formatted = []
    for msg in messages:
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        # Truncate very long content for console
        if len(str(content)) > 1000:
            display_content = str(content)[:1000] + "... [truncated]"
        else:
            display_content = content
        formatted.append(f"  [{role.upper()}]: {display_content}")
    return "\n".join(formatted)


def log_openai_request(
    endpoint: str,
    model: str,
    messages: list = None,
    prompt: str = None,
    **kwargs
):
    """Log an OpenAI API request."""
    timestamp = datetime.now().isoformat()
    
    # Console output
    print(f"\n{'='*70}")
    print(f"📤 OPENAI REQUEST | {timestamp}")
    print(f"{'='*70}")
    print(f"Endpoint: {endpoint}")
    print(f"Model: {model}")
    
    if messages:
        print(f"Messages ({len(messages)} total):")
        print(format_messages(messages))
    elif prompt:
        print(f"Prompt: {prompt[:500]}{'...' if len(prompt) > 500 else ''}")
    
    # Log additional parameters
    important_params = ['temperature', 'max_tokens', 'top_p', 'stream', 'tools', 'functions']
    extra_params = {k: v for k, v in kwargs.items() if k in important_params and v is not None}
    if extra_params:
        print(f"Parameters: {json.dumps(extra_params, indent=2)}")
    
    print(f"{'='*70}\n")
    
    # File logging (full content)
    logger.info(f"REQUEST | endpoint={endpoint} | model={model}")
    if messages:
        logger.debug(f"MESSAGES: {json.dumps(messages, ensure_ascii=False)}")
    if prompt:
        logger.debug(f"PROMPT: {prompt}")
    logger.debug(f"PARAMS: {json.dumps(kwargs, default=str)}")


def log_openai_response(
    endpoint: str,
    response: Any,
    duration_ms: float = None
):
    """Log an OpenAI API response."""
    timestamp = datetime.now().isoformat()
    
    print(f"\n{'='*70}")
    print(f"📥 OPENAI RESPONSE | {timestamp}")
    if duration_ms:
        print(f"Duration: {duration_ms:.0f}ms")
    print(f"{'='*70}")
    
    # Handle different response types
    if hasattr(response, 'choices') and response.choices:
        for i, choice in enumerate(response.choices):
            print(f"Choice {i}:")
            if hasattr(choice, 'message'):
                msg = choice.message
                print(f"  Role: {msg.role}")
                content = getattr(msg, 'content', None)
                if content:
                    if len(content) > 1500:
                        print(f"  Content: {content[:1500]}... [truncated]")
                    else:
                        print(f"  Content: {content}")
                
                # Log tool/function calls
                if hasattr(msg, 'tool_calls') and msg.tool_calls:
                    print(f"  Tool Calls:")
                    for tc in msg.tool_calls:
                        print(f"    - {tc.function.name}: {tc.function.arguments}")
                        
            elif hasattr(choice, 'text'):
                print(f"  Text: {choice.text[:1500]}{'...' if len(choice.text) > 1500 else ''}")
    
    # Log usage stats
    if hasattr(response, 'usage') and response.usage:
        print(f"Usage: prompt_tokens={response.usage.prompt_tokens}, "
              f"completion_tokens={response.usage.completion_tokens}, "
              f"total_tokens={response.usage.total_tokens}")
    
    print(f"{'='*70}\n")
    
    # File logging (full response)
    try:
        if hasattr(response, 'model_dump'):
            response_dict = response.model_dump()
        elif hasattr(response, 'to_dict'):
            response_dict = response.to_dict()
        else:
            response_dict = str(response)
        logger.info(f"RESPONSE | endpoint={endpoint} | duration_ms={duration_ms}")
        logger.debug(f"RESPONSE_BODY: {json.dumps(response_dict, default=str, ensure_ascii=False)}")
    except Exception as e:
        logger.error(f"Failed to serialize response: {e}")


def setup_openai_logging():
    """
    Set up comprehensive OpenAI logging by monkey-patching the client.
    Call this before making any OpenAI API calls.
    """
    import time
    
    try:
        import openai
        from openai import OpenAI, AsyncOpenAI
        
        # Store original methods
        original_create = None
        original_async_create = None
        
        # Patch sync chat completions
        if hasattr(openai, 'resources') and hasattr(openai.resources, 'chat'):
            original_create = openai.resources.chat.completions.Completions.create
            
            @wraps(original_create)
            def logged_create(self, *args, **kwargs):
                model = kwargs.get('model', 'unknown')
                messages = kwargs.get('messages', [])
                
                log_openai_request(
                    endpoint='chat/completions',
                    model=model,
                    messages=messages,
                    **{k: v for k, v in kwargs.items() if k not in ['model', 'messages']}
                )
                
                start_time = time.time()
                response = original_create(self, *args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                
                log_openai_response(
                    endpoint='chat/completions',
                    response=response,
                    duration_ms=duration_ms
                )
                
                return response
            
            openai.resources.chat.completions.Completions.create = logged_create
        
        # Patch async chat completions
        if hasattr(openai, 'resources') and hasattr(openai.resources, 'chat'):
            original_async_create = openai.resources.chat.completions.AsyncCompletions.create
            
            @wraps(original_async_create)
            async def logged_async_create(self, *args, **kwargs):
                model = kwargs.get('model', 'unknown')
                messages = kwargs.get('messages', [])
                
                log_openai_request(
                    endpoint='chat/completions',
                    model=model,
                    messages=messages,
                    **{k: v for k, v in kwargs.items() if k not in ['model', 'messages']}
                )
                
                start_time = time.time()
                response = await original_async_create(self, *args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                
                log_openai_response(
                    endpoint='chat/completions',
                    response=response,
                    duration_ms=duration_ms
                )
                
                return response
            
            openai.resources.chat.completions.AsyncCompletions.create = logged_async_create
        
        print("✅ OpenAI logging enabled - all requests/responses will be logged")
        print(f"📁 Logs also saved to: {LOG_FILE}")
        return True
        
    except ImportError:
        print("⚠️  OpenAI package not installed, logging not enabled")
        return False
    except Exception as e:
        print(f"⚠️  Failed to setup OpenAI logging: {e}")
        return False


if __name__ == "__main__":
    # Test the logging setup
    setup_openai_logging()
    print("OpenAI logger module loaded successfully")
