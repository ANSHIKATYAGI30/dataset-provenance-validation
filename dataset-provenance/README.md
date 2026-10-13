
# Iris Dataset Provenance and Validation

## Purpose

A compact, reproducible validation package for a public dataset.
It records the input's provenance and checks file integrity, schema,
required values, numeric types, and duplicate records.

## Dataset

- Name: Iris
- Source: https://archive.ics.uci.edu/dataset/53/iris
- Creator: R. A. Fisher
- Citation: Fisher, R. (1936). Iris. UCI Machine Learning Repository.
- DOI: 10.24432/C56C76
- License: CC BY 4.0
- Version: Unversioned local source snapshot
- Input: `data/iris.data`
- Expected records: 150
- Expected fields: 5
- Encoding: UTF-8
- Header: None

Check out `manifest.json` for the source checksum, schema, row identity, duplicate policy, and missing-data policy.

## Requirements

Python 3.10 or newer is recommended.
No third-party packages are required.

## Run validation

From the project root:

```bash
python validate.py
```

The command validates the source dataset and both test fixtures.

Expected behavior:

- Source: passes integrity and schema checks, with duplicate warnings.
- Missing fixture: fails because a required value is empty.
- Duplicate fixture: fails because identical records are present.
- Overall test suite: passes only when the source passes and both
  deliberately invalid fixtures are rejected.

## Test fixtures

- `fixtures/missing.csv`: contains a missing required measurement.
- `fixtures/duplicate.csv`: contains two identical records.

These fixtures are separate from the original dataset and are not
part of the source checksum or record count.

## Data handling

The source file is never silently repaired or deduplicated.
Missing required values are reported.
Exact duplicate records are reported without being removed.

Row identity uses the one-based record position in the verified
source snapshot. This identity is not stable across row reordering.

Exact duplicates are grouped by their five parsed field values.
This does not establish whether records represent the same real-world
entity.

## Known limitations

- The source's published dataset page does not provide a version
  identifier for this local snapshot.
- The recorded SHA-256 identifies the exact local file bytes.
- Related samples cannot be grouped by subject unless the source
  provides a reliable grouping identifier.
- Validation checks required values and basic field types, but does
  not establish scientific correctness or validate every possible
  domain constraint.

## Reproducibility

Use the original input file and the checksum recorded in
`manifest.json`. If the file, checksum, schema, or expected record
count differs, investigate the discrepancy instead of silently
modifying the input.

## Implementation Summary

Implemented a dataset provenance and validation workflow using the UCI Iris dataset.

- Added a metadata manifest containing source attribution, license, SHA-256 checksum, file size, and schema information.
- Implemented source-integrity checks and record-level validation.
- Added exact-duplicate detection that reports duplicate records without silently removing them.
- Created negative test fixtures for missing values and duplicate records.
- Verified the workflow using automated validation checks.

## Validation Results

- Source dataset: **PASS** — checksum, file size, and 150-record count verified.
- Missing-value fixture: **PASS** — invalid input correctly rejected.
- Duplicate-record fixture: **PASS** — duplicate input correctly rejected.

The source dataset contains exact duplicate records, which are reported as warnings rather than automatically removed.

## Scope and Split Policy

This package is **unsplit and validation-only**. It validates the provenance and structure of the source dataset and checks deliberately invalid test fixtures. It does not create training, validation, or test partitions, and it does not train or evaluate a model.

The source dataset is retained in its original order. Exact duplicate records are reported and are not silently removed or modified.

If a research split is introduced in a future revision, the assignment rule and proportions should be defined in advance, and exact-duplicate groups should remain within the same partition.

**Limitation:** Exact-duplicate grouping alone cannot rule out broader related-sample leakage. The dataset does not provide subject identifiers that would establish whether different-looking records are related. This package does not claim to guarantee a leakage-free research split.
