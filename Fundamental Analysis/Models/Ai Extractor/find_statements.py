"""Find where financial statements actually are in the PDF."""
import pdfplumber

pdf_path = "data/raw/hnb/HNBannual.pdf"

print("="*80)
print("SCANNING ENTIRE PDF FOR FINANCIAL STATEMENTS")
print("="*80)

keywords = {
    'Income/Comprehensive Income': ['statement of profit or loss', 'comprehensive income', 'income statement'],
    'Financial Position': ['statement of financial position', 'balance sheet as at'],
    'Cash Flows': ['statement of cash flows', 'cash flows for the year']
}

with pdfplumber.open(pdf_path) as pdf:
    print(f"\nTotal pages: {len(pdf.pages)}\n")
    
    for stmt_name, kw_list in keywords.items():
        print(f"\n{stmt_name}:")
        print("-"*80)
        found = False
        
        for page_num in range(len(pdf.pages)):
            page = pdf.pages[page_num]
            text = page.extract_text()
            
            if text:
                text_lower = text.lower()
                for keyword in kw_list:
                    if keyword in text_lower:
                        # Check if it has "bank" and "group" columns
                        has_bank = 'bank' in text_lower
                        has_group = 'group' in text_lower
                        has_years = '2024' in text or '2023' in text
                        
                        # Extract tables to see structure
                        tables = page.extract_tables()
                        
                        print(f"  Page {page_num + 1}:")
                        print(f"    Keyword: '{keyword}'")
                        print(f"    Has 'Bank': {has_bank}, 'Group': {has_group}, Years: {has_years}")
                        print(f"    Tables found: {len(tables)}")
                        
                        # Show first few lines
                        lines = text.split('\n')[:5]
                        print(f"    First lines: {' | '.join([l.strip()[:50] for l in lines if l.strip()])}")
                        
                        if tables:
                            for i, table in enumerate(tables[:2]):
                                if table and len(table) > 2:
                                    print(f"    Table {i+1}: {len(table)} rows × {len(table[0]) if table else 0} cols")
                                    print(f"      Headers: {table[0] if table else 'N/A'}")
                        
                        found = True
                        print()
                        break
        
        if not found:
            print(f"  NOT FOUND in any page!")

print("\n" + "="*80)
print("SCAN COMPLETE")
print("="*80)
