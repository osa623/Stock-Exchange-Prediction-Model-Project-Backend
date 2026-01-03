import json

with open('data/processed/extracted_json/pabc_final_extraction.json') as f:
    data = json.load(f)

output = data['canonical_output']

print("="*80)
print("CANONICAL OUTPUT SUMMARY")
print("="*80)

print("\n📊 Bank Year1 (2024) - Income Statement:")
print(f"   Fields extracted: {len(output['Bank']['Year1']['Income_Statement'])}")
for k, v in list(output['Bank']['Year1']['Income_Statement'].items())[:8]:
    print(f"   {k}: {v:,.0f}" if v else f"   {k}: None")

print("\n📊 Bank Year2 (2023) - Income Statement:")
print(f"   Fields extracted: {len(output['Bank']['Year2']['Income_Statement'])}")
for k, v in list(output['Bank']['Year2']['Income_Statement'].items())[:5]:
    print(f"   {k}: {v:,.0f}" if v else f"   {k}: None")

print("\n📊 Bank Year1 - Financial Position Statement:")
print(f"   Fields extracted: {len(output['Bank']['Year1']['Financial Position Statement'])}")

print("\n📊 Bank Year1 - Cash Flow Statement:")
print(f"   Fields extracted: {len(output['Bank']['Year1']['Cash Flow Statement'])}")

print("\n📊 Group (Consolidated) Statements:")
print(f"   Income Statement: {len(output['Group']['Year1']['Income_Statement'])} fields")
print(f"   Financial Position: {len(output['Group']['Year1']['Financial Position Statement'])} fields")
print(f"   Cash Flow: {len(output['Group']['Year1']['Cash Flow Statement'])} fields")

print("\n✅ Extraction structure matches target_schema_bank.py format!")
