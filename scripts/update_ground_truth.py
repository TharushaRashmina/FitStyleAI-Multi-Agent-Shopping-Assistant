import csv
import json

CANDIDATES_FILE = "evaluation/ground_truth_candidates.csv"
QUERIES_FILE = "evaluation/ground_truth_queries.json"

# Load candidates
with open(CANDIDATES_FILE, "r", encoding="utf-8-sig") as f:
    rows = list(csv.DictReader(f))

# Collect relevant product IDs
relevant_by_query = {}

for row in rows:
    if row["relevant"].strip() == "1":
        query_id = row["query_id"].strip()
        product_id = row["product_id"].strip()

        relevant_by_query.setdefault(
            query_id, []
        ).append(product_id)

# Load queries
with open(QUERIES_FILE, "r", encoding="utf-8") as f:
    queries = json.load(f)

# Update IDs
for query in queries:
    query_id = query["query_id"]

    query["relevant_product_ids"] = (
        relevant_by_query.get(query_id, [])
    )

# Save
with open(QUERIES_FILE, "w", encoding="utf-8") as f:
    json.dump(
        queries,
        f,
        ensure_ascii=False,
        indent=2
    )

print("\n--- GROUND TRUTH UPDATED ---")

for query in queries:
    print(
        query["query_id"],
        "Relevant products:",
        len(query["relevant_product_ids"])
    )

print("\nUpdated:", QUERIES_FILE)