
### 4. docs/ARCHITECTURE.md

```markdown
# Workflow Architecture

## Processing Flow

1. **Webhook Reception**
   - Receives documents from Flask app
   - Splits document and template processing

2. **Document Type Detection**
   - PDFs: Processed via Mistral OCR
   - Images: Processed via Mistral Image Parser
   - Document type identified using Qdrant vector store

3. **Data Extraction**
   - AI agents extract structured data
   - Data is mapped to template format

4. **Output Generation**
   - Final JSON structure created
   - Results saved to file
   - Transaction status updated

## Key Components

- **Mistral AI**: For OCR and document analysis
- **Qdrant**: Vector store for document type matching
- **Custom Agents**: For structured data extraction
- **Flask Integration**: For transaction tracking
