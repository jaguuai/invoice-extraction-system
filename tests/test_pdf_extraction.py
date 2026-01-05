"""
Test PDF Text Extractor
"""
from src.services.pdf_text_extractor import get_pdf_text_extractor
from pathlib import Path

def test_text_extraction():
    """Test text extraction from uploaded PDF"""
    
    # Get extractor
    extractor = get_pdf_text_extractor()
    
    # Find a PDF in uploads directory
    from src.core.config import settings
    upload_dir = Path(settings.UPLOAD_DIR)
    
    # List PDFs
    pdfs = list(upload_dir.glob("*.pdf"))
    
    if not pdfs:
        print("❌ No PDFs found in uploads directory")
        return
    
    # Test with first PDF
    pdf_path = pdfs[0]
    print(f"📄 Testing with: {pdf_path.name}")
    print("="*70)
    
    # Extract full document
    result = extractor.extract(str(pdf_path))
    
    print(f"\n📊 RESULTS:")
    print(f"   Pages: {result.page_count}")
    print(f"   Total chars: {result.total_chars}")
    print(f"   Total words: {result.total_words}")
    
    print(f"\n📝 PER-PAGE:")
    for page in result.pages:
        print(f"   Page {page.page_number}: {page.word_count} words, {page.char_count} chars")
    
    print(f"\n📄 COMBINED TEXT (first 500 chars):")
    print("="*70)
    print(result.combined_text[:500])
    print("...")
    print("="*70)
    
    # Test single page
    print(f"\n📄 SINGLE PAGE TEST (Page 1):")
    print("="*70)
    page1 = extractor.extract_page(str(pdf_path), 1)
    print(page1.text[:300])
    print("...")
    print("="*70)
    
    # Metadata
    print(f"\n📋 METADATA:")
    metadata = extractor.extract_metadata(str(pdf_path))
    for key, value in metadata.items():
        if value:
            print(f"   {key}: {value}")

if __name__ == "__main__":
    test_text_extraction()
