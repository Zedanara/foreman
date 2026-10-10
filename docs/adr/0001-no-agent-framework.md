# ADR 0001: Hand-written agent loop instead of an agent framework

- Status: Accepted
- Date: 2026-10-10
- Issue: #5

## Context

Foreman is a personal multi-agent assistant in Telegram. It is also a learning
and portfolio project: the main goal is to understand how an agent works from
the inside, not only to get a working bot.

Constraints:

- The model runs locally through Ollama (`gpt-oss:20b`) behind an
  OpenAI-compatible API. Later it must switch to any OpenAI-compatible
  provider by changing configuration only.
- A local 20B model is slower and less reliable at tool calling than hosted
  frontier models, so we need full control over prompts, retries and limits.
- One developer, limited time. Every dependency must be understood and
  debuggable.

The agent loop itself is small: send messages and tool schemas to the model,
run the tool calls it returns, append the results, repeat until the model
answers or a step limit is reached.

## Considered options

### 1. Hermes Agent (Nous Research)

An open-source, ready-to-run agent with persistent memory, self-created
skills, many built-in tools and messaging gateways (Telegram included). It
supports many LLM providers.

- Good: a working Telegram assistant almost out of the box.
- Bad: it is a complete product, not a library. The interesting parts
  (the loop, memory, tool routing) are already written, so there is little
  left to learn or to show in a portfolio.
- Bad: large surface area; when something breaks with a local model, the
  problem is inside someone else's code.

### 2. LangGraph

A low-level orchestration library: agents as graphs of nodes and edges, with
checkpointing, durable execution, streaming and human-in-the-loop.

- Good: solid primitives for multi-agent workflows and persistence; a
  widely used skill on the job market.
- Bad: its own concepts (state graphs, reducers, checkpointers) have to be
  learned before the agent concepts themselves.
- Bad: extra layers between our code and the model make it harder to see
  what is actually sent to a small local model.

### 3. Own loop on top of the OpenAI-compatible API

A plain `while` loop with `AsyncOpenAI`, tool schemas as JSON and a registry
of Python functions.

- Good: every line is ours and explainable in an interview.
- Good: minimal dependencies (`openai` client only); works with Ollama and
  any OpenAI-compatible provider.
- Good: easy to log and test the exact messages and tool calls.
- Bad: we must build ourselves what frameworks give for free: step limits,
  retries, memory, persistence, tracing.

## Decision

Write our own agent loop (option 3). No agent framework.

## Consequences

- v0.2 implements the loop by hand: tool registry, JSON schema for tools,
  max-steps guard, error handling for bad tool calls.
- We own the bugs. Tests with a fake model client are required for the loop.
- Persistence, memory and tracing are built only when a milestone needs them.
- Revisit this decision if orchestration grows beyond a few agents with
  branching and resumable state; LangGraph is the first candidate then.
  Such a change needs a new ADR that supersedes this one.
