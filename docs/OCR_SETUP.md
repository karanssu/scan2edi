# Local OCR / AI setup

Scan2EDI uses two local stages:

1. PaddleOCR-VL parses the invoice document/image into machine-readable content.
2. A local Ollama model converts that content to the strict Scan2EDI invoice schema.

No cloud API is required.

## PaddleOCR-VL

Use Python 3.13 or another version supported by your chosen PaddleOCR deployment. Install the hardware-appropriate PaddlePaddle package first, then:

```bash
python -m pip install -U "paddleocr[doc-parser]"
```

For production NVIDIA deployments, prefer PaddleOCR's official local/offline Docker images and inference-service guidance rather than installing GPU libraries into the lightweight Scan2EDI OCR image.

## Ollama

Install Ollama on the on-premise server, download the model while the machine is allowed internet access, then configure:

```env
OLLAMA_BASE_URL=http://host.docker.internal:11434
OLLAMA_MODEL=qwen2.5:7b
```

The extractor sends a JSON Schema through Ollama's `format` field with temperature 0. The prompt explicitly forbids UPC invention and distinguishes product discounts from general invoice-level discounts.

## Offline production

Before isolating the server:

- Pull all Docker images.
- Download/import PaddleOCR model assets or use its offline image.
- Download the Ollama model.
- Verify processing while outbound networking is still disabled at the application layer.
- Then enforce outbound egress blocking at the host/firewall level.
