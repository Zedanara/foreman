# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Project setup with uv, ruff and pre-commit (#1).
- GitHub Actions CI running ruff and pytest (#2).
- `python -m foreman.ask`: streams an answer from an OpenAI-compatible server,
  local Ollama by default (#3).
- ADR 0001: hand-written agent loop instead of a framework (#5).
- README and this changelog (#10).
