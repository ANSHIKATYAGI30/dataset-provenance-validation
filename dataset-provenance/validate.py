
import csv
import hashlib
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def load_manifest():
    manifest_path = ROOT / "manifest.json"

    with manifest_path.open("r", encoding="utf-8") as file:
        return json.load(file)


def sha256_file(path):
    digest = hashlib.sha256()

    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(8192), b""):
            digest.update(chunk)

    return digest.hexdigest()


def validate(
    input_path,
    manifest,
    label="SOURCE",
    strict_duplicates=False,
    check_source_integrity=True,
    error_codes=None
):
    errors = []
    warnings = []

    def error(message, code="validation_error"):
        errors.append(message)
        if error_codes is not None:
            error_codes.append(code)
        print(f"FAIL [{label}] {message}")

    def warning(message):
        warnings.append(message)
        print(f"WARN [{label}] {message}")

    print(f"\n--- Validating {label}: {input_path} ---")

    if not input_path.is_file():
        error("Input file does not exist.")
        print(f"RESULT: FAIL — {len(errors)} error(s).")
        return False

    input_config = manifest["input"]
    schema = manifest["schema"]

    # Verify the original source file's integrity.
    if check_source_integrity:
        actual_hash = sha256_file(input_path)
        expected_hash = input_config["sha256"]

        if actual_hash != expected_hash:
            error(
                f"SHA-256 mismatch: expected {expected_hash}, "
                f"got {actual_hash}"
            )
        else:
            print("PASS: SHA-256 matches manifest.")

        actual_size = input_path.stat().st_size
        expected_size = input_config["expected_size_bytes"]

        if actual_size != expected_size:
            error(
                f"File size mismatch: expected {expected_size}, "
                f"got {actual_size}"
            )
        else:
            print("PASS: File size matches manifest.")

    # Read the file without modifying or repairing its contents.
    try:
        with input_path.open(
            "r",
            encoding=input_config.get("encoding", "utf-8"),
            newline=""
        ) as file:
            reader = csv.reader(file)
            records = []

            for line_number, row in enumerate(reader, start=1):
                # Ignore genuinely empty lines.
                # Rows containing empty fields are still validated.
                if not row:
                    continue

                records.append((line_number, row))

    except (UnicodeDecodeError, OSError, csv.Error) as exc:
        error(f"Cannot read input: {exc}")
        print(f"RESULT: FAIL — {len(errors)} error(s).")
        return False

    # Verify record count only for the original source.
    if check_source_integrity:
        expected_count = input_config["expected_records"]

        if len(records) != expected_count:
            error(
                f"Record count mismatch: expected {expected_count}, "
                f"got {len(records)}"
            )
        else:
            print(f"PASS: Record count is {len(records)}.")

    seen = defaultdict(list)

    # Validate field counts, missing values, and data types.
    for line_number, row in records:
        if len(row) != len(schema):
            error(
                f"Line {line_number}: expected {len(schema)} fields, "
                f"got {len(row)}."
            )
            continue

        normalized = []

        for index, field in enumerate(schema):
            value = row[index].strip()

            if field["required"] and not value:
                error(
                    f"Line {line_number}: required field "
                    f"'{field['name']}' is missing.",
                    code="missing_required"
                )

            if not value:
                normalized.append("")
                continue

            if field["type"] == "float":
                try:
                    number = float(value)

                    if not math.isfinite(number):
                        raise ValueError("Non-finite number")

                except ValueError:
                    error(
                        f"Line {line_number}: field "
                        f"'{field['name']}' must be a finite number."
                    )

            normalized.append(value)

        # Group exact matches across all five field values.
        # Never delete or modify duplicate records.
        seen[tuple(normalized)].append(line_number)

    duplicate_groups = [
        lines
        for lines in seen.values()
        if len(lines) > 1
    ]

    if duplicate_groups:
        for lines in duplicate_groups:
            message = f"Exact duplicate records at source lines {lines}."

            if strict_duplicates:
                error(message, code="duplicate_records")
            else:
                warning(message)
    else:
        print("PASS: No exact duplicate records found.")

    if errors:
        print(
            f"RESULT: FAIL — {len(errors)} error(s), "
            f"{len(warnings)} warning(s)."
        )
        return False

    print(
        f"RESULT: PASS — {len(warnings)} warning(s)."
    )
    return True


def main():
    try:
        manifest = load_manifest()
    except (OSError, json.JSONDecodeError) as exc:
        print(f"FAIL: Cannot load manifest: {exc}")
        return 2

    source_path = ROOT / manifest["input"]["path"]

    # Test 1: Validate the original dataset.
    source_ok = validate(
        source_path,
        manifest,
        label="SOURCE"
    )

    # Negative fixtures must fail for their intended defects.
    missing_codes = []
    duplicate_codes = []

    # Test 2: A required value is deliberately missing.
    missing_ok = validate(
        ROOT / "fixtures" / "missing.csv",
        manifest,
        label="MISSING FIXTURE",
        check_source_integrity=False,
        error_codes=missing_codes
    )

    # Test 3: An identical record is deliberately duplicated.
    duplicate_ok = validate(
        ROOT / "fixtures" / "duplicate.csv",
        manifest,
        label="DUPLICATE FIXTURE",
        strict_duplicates=True,
        check_source_integrity=False,
        error_codes=duplicate_codes
    )

    missing_rejected_as_expected = (
        not missing_ok and bool(missing_codes)
        and set(missing_codes) == {"missing_required"}
    )
    duplicate_rejected_as_expected = (
        not duplicate_ok and bool(duplicate_codes)
        and set(duplicate_codes) == {"duplicate_records"}
    )

    print("\n========== TEST SUMMARY ==========")
    print(f"Source dataset passes: {source_ok}")
    print(f"Missing fixture rejected for missing values: {missing_rejected_as_expected}")
    print(f"Duplicate fixture rejected for duplicates: {duplicate_rejected_as_expected}")

    if source_ok and missing_rejected_as_expected and duplicate_rejected_as_expected:
        print("\nALL VALIDATION TESTS PASSED")
        return 0

    print("\nVALIDATION TEST SUITE FAILED")
    return 1


if __name__ == "__main__":
    sys.exit(main())
