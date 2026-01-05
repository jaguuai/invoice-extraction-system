"""Test PDF Text Extractor"""
from src.services.pdf_text_extractor import get_pdf_text_extractor

extractor = get_pdf_text_extractor()

# Test
pdf_path = 'C:\Users\alice\Desktop\invoice-extraction-system\tests\QIT_AI_Engineer_Assessment_Task.pdf'

# Extract all
result = extractor.extract(pdf_path)
print(f'Pages: {result.page_count}')
print(f'Words: {result.total_words}')
print(f'Text preview:')
print(result.combined_text[:200])
print('...')

# Extract metadata
metadata = extractor.extract_metadata(pdf_path)
print(f'\nMetadata:')
for key, value in metadata.items():
    if value:
        print(f'  {key}: {value}')
