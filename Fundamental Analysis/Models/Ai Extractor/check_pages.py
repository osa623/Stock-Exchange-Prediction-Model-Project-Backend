import pdfplumber

pdf = pdfplumber.open('data/raw/commercial/Commerical.pdf')

for page_num in [297, 298, 300]:
    page = pdf.pages[page_num]
    text = page.extract_text() or ""
    
    print(f"\n{'=' * 80}")
    print(f"PAGE {page_num} (display {page_num+1})")
    print('=' * 80)
    print(f"Has '2024': {'2024' in text}")
    print(f"Has '2023': {'2023' in text}")
    print(f"Has both years: {'2024' in text and '2023' in text}")
    print(f"Has rs marker: {'rs' in text.lower() and '000' in text}")
    print(f"Has 'gross income': {'gross income' in text.lower()}")
    print(f"Has 'interest income': {'interest income' in text.lower()}")
    print(f"Has 'assets': {'assets' in text.lower()}")
    
    print(f"\nFirst 400 chars:")
    print(text[:400])
