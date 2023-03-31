# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Support for multi-turn flows
- Generic matching of bot and user messages using "..."
- Basic interruption mechanism
- Support for priority flows and extension flows

### Changed
- Renaming from CoLLM to Colang flows
- Invoking LLM related code as actions, not as methods on the Runtime instance
- Refactored the LLM actions out of the runtime.

### Deprecated
- ...

### Removed
- ...

### Fixed
- ...

### Security
- ...

## [0.0.1] - 2023-03-22

### Added
- Implemented the basic working flow with canonical forms detection
- Integrated the Colang parser from the main colang repository
- Added example configs for passh-through configuration and sample Benefits Ambassador
- Added basic support for the `wolfram alpha request` pre-defined action
- Implemented first version of the CLI with support for the `colang chat` command
- Initial documentation with a getting started guide for alpha users.
