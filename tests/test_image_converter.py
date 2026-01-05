"""
Test PDF to Image Converter with Scanned PDF
"""
from src.services.pdf_to_image_converter import get_pdf_to_image_converter
from pathlib import Path

def test_pdf_to_image():
    """Test PDF to image conversion with scanned PDF"""
    
    # Specific test file
    pdf_path = Path("tests/sample_image_only_scanned.pdf")
    
    if not pdf_path.exists():
        print(f"❌ Test file not found: {pdf_path}")
        print(f"   Current directory: {Path.cwd()}")
        return
    
    print(f"📄 Testing with: {pdf_path.name}")
    print(f"   Path: {pdf_path.absolute()}")
    print("="*70)
    
    # Get converter
    converter = get_pdf_to_image_converter()
    
    # Convert to images
    print("\n🔄 Converting PDF to images...")
    result = converter.convert(str(pdf_path))
    
    print(f"\n📊 CONVERSION RESULTS:")
    print(f"   PDF: {Path(result.pdf_path).name}")
    print(f"   Pages: {result.page_count}")
    print(f"   DPI: {result.dpi}")
    print(f"   Format: {result.format}")
    
    print(f"\n🖼️  IMAGE INFO:")
    for i, image in enumerate(result.images, 1):
        info = converter.get_image_info(image)
        print(f"   Page {i}: {info['width']}x{info['height']} ({info['mode']})")
        print(f"           Size: {image.size}")
    
    # Save images to temp directory
    from src.core.config import settings
    print(f"\n💾 SAVING IMAGES:")
    temp_dir = Path(settings.TEMP_DIR) / "scanned_images"
    saved_paths = converter.save_images(
        result.images, 
        str(temp_dir),
        base_name="scanned_page"
    )
    
    for path in saved_paths:
        size = Path(path).stat().st_size / 1024  # KB
        print(f"   ✅ {Path(path).name} ({size:.1f} KB)")
    
    print(f"\n✅ Images saved to: {temp_dir}")
    print("="*70)
    
    # Also test single page conversion
    if result.page_count > 0:
        print(f"\n📄 SINGLE PAGE TEST:")
        print("="*70)
        single_image = converter.convert_single_page(str(pdf_path), 1)
        info = converter.get_image_info(single_image)
        print(f"   Page 1: {info['width']}x{info['height']}")
        print(f"   Mode: {info['mode']}")
        print("="*70)

if __name__ == "__main__":
    test_pdf_to_image()
