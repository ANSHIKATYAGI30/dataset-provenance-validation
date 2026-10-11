
from pathlib import Path
import hashlib

DATA_DIR = Path("data")

for filename in ["iris.data", "bezdekIris.data", "iris.names", "Index"]:
    path = DATA_DIR / filename

    print(f"\n--- {filename} ---")

    if not path.exists():
        print("File not found")
        continue

    content = path.read_bytes()
    checksum = hashlib.sha256(content).hexdigest()

    print("Size:", len(content), "bytes")
    print("SHA-256:", checksum)

    if path.suffix == ".data":
        rows = [
            line.strip()
            for line in content.decode("utf-8-sig").splitlines()
            if line.strip()
        ]

        print("Record count:", len(rows))

        malformed = [
            (i, row)
            for i, row in enumerate(rows, start=1)
            if len(row.split(",")) != 5
        ]

        print("Malformed rows:", len(malformed))
        print("First record:", rows[0] if rows else "Empty")