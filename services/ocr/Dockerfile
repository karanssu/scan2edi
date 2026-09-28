FROM python:3.13-slim

WORKDIR /app

# PaddleOCR/PaddlePaddle need a few shared libraries that are not present in
# python:slim. Keep the list minimal because this service stays on-premise.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libgomp1 \
        libglib2.0-0 \
        libgl1 \
    && rm -rf /var/lib/apt/lists/*

# PaddleOCR-VL requires an inference engine. This is the official x64 CPU
# PaddlePaddle package documented for PaddleOCR-VL. A GPU image can replace
# this later without changing the Scan2EDI API contract.
RUN python -m pip install --no-cache-dir \
    paddlepaddle==3.2.1 \
    -i https://www.paddlepaddle.org.cn/packages/stable/cpu/

COPY requirements.txt .
RUN python -m pip install --no-cache-dir -r requirements.txt

COPY app ./app

EXPOSE 8080
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
