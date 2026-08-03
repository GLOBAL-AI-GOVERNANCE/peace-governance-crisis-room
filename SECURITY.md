# Security Policy

## Scope

This repository contains a fictional offline simulation. It does not contain a live AI agent, external-action executor, authentication service, production backend, or real incident feed.

Report sensitive repository-integrity, unsafe-content, secret-exposure, supply-chain, or release-artifact concerns through GitHub private vulnerability reporting when enabled. Do not include real classified, controlled, personal, or incident-sensitive information in reports.

## Supported version

Only the latest tagged release candidate is supported for source-integrity review. Runtime support begins only after a separately documented tested build exists.

## Evidence boundary

The in-memory audit chain detects alteration within an exported record. It is not signed, independently timestamped, remotely anchored, or access-controlled, and it does not independently prove who made the decision or when.
