"""Find the actual Income Statement page in Commercial Bank PDF."""
import pdfplumber

pdf_path = "data/raw/commercial/Commerical.pdf"

print("Searching for Income Statement in Commercial Bank PDF...")
print("=" * 80)

with pdfplumber.open(pdf_path) as pdf:
    # Check pages around 297-305
    for page_num in range(295, 310):
        if page_num >= len(pdf.pages):
            break
        
        page = pdf.pages[page_num]
        text = page.extract_text() or ""
        
        # Check if this page has "Income Statement" AND numerical data
        has_income_statement = "income" in text.lower() and "statement" in text.lower()
        has_numbers = any(keyword in text for keyword in ["Rs '000", "Rs. '000", "2024", "2023"])
        has_data_labels = any(label in text for label in ["Gross income", "Interest income", "Net interest"])
        
        if has_income_statement and (has_numbers or has_data_labels):
            print(f"\n📄 Page {page_num} (display: {page_num+1}):")
            print(f"   Has Income Statement: {has_income_statement}")
            print(f"   Has Numbers: {has_numbers}")
            print(f"   Has Data Labels: {has_data_labels}")
            
            # Show first 500 characters
            lines = text.split('\n')[:15]
            print(f"   First 15 lines:")
            for line in lines:
                if line.strip():
                    print(f"     {line[:80]}")

print("\n" + "=" * 80)
print("Searching for Financial Position Statement...")
print("=" * 80)

with pdfplumber.open(pdf_path) as pdf:
    for page_num in range(295, 310):
        if page_num >= len(pdf.pages):
            break
        
        page = pdf.pages[page_num]
        text = page.extract_text() or ""
        
        has_position = "financial position" in text.lower() or "balance sheet" in text.lower()
        has_numbers = any(keyword in text for keyword in ["Rs '000", "Rs. '000", "2024", "2023"])
        has_data_labels = any(label in text for label in ["Assets", "Cash", "Deposits", "Liabilities"])
        
        if has_position and (has_numbers or has_data_labels):
            print(f"\n📄 Page {page_num} (display: {page_num+1}):")
            lines = text.split('\n')[:15]
            print(f"   First 15 lines:")
            for line in lines:
                if line.strip():
                    print(f"     {line[:80]}")
