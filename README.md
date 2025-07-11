# CogniScan Processor

An intelligent document processing workflow built with n8n that automatically extracts, analyzes, and structures data from various document types using AI-powered OCR and document classification.

## 🚀 Features

- **Multi-format Support**: Processes PDFs and images (PNG, JPG, JPEG, BMP)
- **AI-Powered OCR**: Uses Mistral's OCR capabilities for accurate text extraction
- **Intelligent Document Classification**: Automatically identifies document types using RAG (Retrieval-Augmented Generation)
- **Flexible Output Formatting**: Structures data according to custom templates
- **Real-time Processing**: Webhook-based integration with external applications
- **Transaction Tracking**: Complete audit trail with status updates

## 🏗️ Architecture

The workflow consists of five main processing stages:

1. **Input Processing**: Webhook receiver with file type detection
2. **OCR Extraction**: Mistral-powered text extraction for PDFs and images
3. **Document Analysis**: AI agent identifies document type and extracts relevant fields
4. **Output Structuring**: Formats data according to provided templates
5. **Storage & Notification**: Saves results and updates transaction status

## 📋 Prerequisites

- n8n instance (self-hosted or cloud)
- Mistral AI API account
- Qdrant vector database
- Flask web application (for webhook integration)

## 🔧 Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/cogniscan-processor.git
cd cogniscan-processor
```

### 2. Configure Environment Variables

Create a `.env` file in your project root:

```bash
cp .env.example .env
```

Edit the `.env` file with your credentials:

```env
MISTRAL_API_KEY=your_mistral_api_key_here
QDRANT_API_KEY=your_qdrant_api_key_here
QDRANT_URL=your_qdrant_instance_url
FLASK_APP_URL=http://your-flask-app:5000
```

### 3. Import the Workflow

1. Open your n8n instance
2. Go to **Workflows** > **Import from File**
3. Select the `workflow/CogniScan_Processor.json` file
4. Configure the credentials as described in the [Credentials Setup](#credentials-setup) section

### 4. Set up Qdrant Collection

Ensure your Qdrant instance has a collection named "CogniScan" with the appropriate document templates for classification.

## 🔐 Credentials Setup

The workflow requires the following credentials to be configured in n8n:

### Mistral AI API
- **Name**: `Mistral Cloud account`
- **API Key**: Your Mistral AI API key

### Qdrant API
- **Name**: `QdrantApi account`
- **API Key**: Your Qdrant API key
- **URL**: Your Qdrant instance URL

## 📡 API Integration

### Webhook Endpoint

The workflow exposes a webhook endpoint that accepts:

```json
{
  "transaction_id": "unique_transaction_id",
  "files": "binary_file_data",
  "template": "output_template_json"
}
```

### Response Format

The processed data is saved as JSON files and the Flask application is notified with:

```json
{
  "transaction_id": "unique_transaction_id",
  "status": "Completed",
  "document_type": "Invoice",
  "processed_file_name": "transaction_id.json",
  "processed_at": "2024-01-01T00:00:00Z",
  "results": "Completed"
}
```

## 📊 Supported Document Types

The system can identify and process various document types including:

- Invoices
- Contracts
- Forms
- Receipts
- Generic documents

## 🛠️ Customization

### Adding New Document Types

1. Update the Qdrant knowledge base with new document templates
2. Modify the document classification agent prompts if needed
3. Add new output templates for the document types

### Modifying OCR Settings

The OCR settings can be adjusted in the respective HTTP request nodes:
- PDF OCR: `Get Mistral OCR Output` node
- Image OCR: `Mistral Image Parser` node

## 🔍 Monitoring

The workflow includes comprehensive logging and error handling:

- Transaction status tracking
- File processing confirmation
- Error propagation to the Flask application
- Structured output validation

## 🚨 Troubleshooting

### Common Issues

1. **OCR Failures**: Check Mistral API quotas and file format compatibility
2. **Classification Errors**: Verify Qdrant collection setup and embeddings
3. **Output Format Issues**: Validate JSON template structure
4. **Webhook Timeouts**: Adjust processing timeouts for large files

### Debug Mode

Enable debug mode by checking the workflow execution logs in n8n's execution history.

## 📈 Performance Optimization

- **File Size Limits**: Optimize for files under 10MB for better processing speed
- **Batch Processing**: Consider implementing batch processing for multiple files
- **Caching**: Implement caching for frequently processed document types

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 💬 Support

For support and questions:
- Create an issue in this repository
- Check the [troubleshooting guide](#troubleshooting)
- Review n8n documentation for workflow-specific questions

## 🔄 Version History

- **v1.0.0**: Initial release with basic OCR and classification features
- **v1.1.0**: Added support for multiple file formats
- **v1.2.0**: Improved document classification accuracy with RAG

---

**Note**: This workflow is designed to work with sensitive documents. Ensure proper security measures are in place when deploying in production environments.
