"""
Test PaddleOCR Service
"""
from src.services.paddle_ocr_service import get_paddle_ocr_service
from src.services.pdf_to_image_converter import get_pdf_to_image_converter
from pathlib import Path

def test_paddle_ocr():
    """Test PaddleOCR with converted images"""
    
    # Test file
    pdf_path = Path("tests/sample_image_only_scanned.pdf")
    
    if not pdf_path.exists():
        # Fallback to uploads
        from src.core.config import settings
        pdfs = list(Path(settings.UPLOAD_DIR).glob("*.pdf"))
        if pdfs:
            pdf_path = pdfs[0]
        else:
            print("❌ No PDF found")
            return
    
    print(f"📄 Testing with: {pdf_path.name}")
    print("="*70)
    
    # Step 1: Convert PDF to images
    print("\n🔄 Step 1: Converting PDF to images...")
    converter = get_pdf_to_image_converter()
    conversion_result = converter.convert(str(pdf_path))
    print(f"✅ Converted {conversion_result.page_count} pages")
    
    # Step 2: OCR with PaddleOCR
    print("\n🔄 Step 2: Running PaddleOCR...")
    ocr = get_paddle_ocr_service()
    ocr_result = ocr.extract_from_images(conversion_result.images)
    
    print(f"\n📊 OCR RESULTS:")
    print(f"   Characters: {ocr_result.char_count}")
    print(f"   Words: {ocr_result.word_count}")
    print(f"   Lines: {ocr_result.line_count}")
    print(f"   Confidence: {ocr_result.confidence:.2%}")
    
    print(f"\n📝 EXTRACTED TEXT:")
    print("="*70)
    print(ocr_result.text[:500])
    print("...")
    print("="*70)

if __name__ == "__main__":
    test_paddle_ocr()
