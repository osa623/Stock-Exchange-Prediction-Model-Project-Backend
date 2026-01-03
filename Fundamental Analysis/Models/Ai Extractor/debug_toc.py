import pdfplumber
from src.locator.toc_detector import TOCDetector

pdf = pdfplumber.open('data/raw/commercial/Commerical.pdf')

# Get first 20 pages to find TOC
contents_text = ""
for page_num in range(min(20, len(pdf.pages))):
    text = pdf.pages[page_num].extract_text() or ""
    if 'content' in text.lower():
        print(f"Found Contents on page {page_num}")
        contents_text += text + "\n"

# Look for Income Statement mention
if 'income statement' in contents_text.lower():
    idx = contents_text.lower().find('income statement')
    context = contents_text[idx-100:idx+100]
    print("\n" + "=" * 80)
    print("CONTEXT AROUND 'Income Statement':")
    print("=" * 80)
    print(context)

# Now run detector
toc = TOCDetector()
results = toc.get_statement_pages_from_toc(pdf)

print("\n" + "=" * 80)
print("TOC DETECTOR RESULTS:")
print("=" * 80)

if results['Income_Statement']:
    print(f"Income Statement: {results['Income_Statement'][0]}")
if results['Financial Position Statement']:
    print(f"Financial Position: {results['Financial Position Statement'][0]}")
if results['Cash Flow Statement']:
    print(f"Cash Flow: {results['Cash Flow Statement'][0]}")
