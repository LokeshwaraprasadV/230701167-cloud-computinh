import io
import os
import uuid
from urllib.request import Request, urlopen

from PIL import Image


def make_multipart(fields, files):
    boundary = "----Boundary" + uuid.uuid4().hex
    parts = []

    for name, value in fields.items():
        parts.append(f"--{boundary}\r\n".encode())
        parts.append(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode())
        parts.append(str(value).encode())
        parts.append(b"\r\n")

    for name, (filename, content_type, data) in files.items():
        parts.append(f"--{boundary}\r\n".encode())
        parts.append(
            f'Content-Disposition: form-data; name="{name}"; filename="{filename}"\r\n'.encode()
        )
        parts.append(f"Content-Type: {content_type}\r\n\r\n".encode())
        parts.append(data)
        parts.append(b"\r\n")

    parts.append(f"--{boundary}--\r\n".encode())
    body = b"".join(parts)
    return boundary, body


def main():
    img = Image.new("RGB", (512, 512), color=(20, 20, 20))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    img_bytes = buf.getvalue()

    fields = {
        "name": "Test Patient",
        "age": 45,
        "gender": "Male",
        "diabetes_duration": 8,
        "sugar_level": 180,
    }
    files = {"image": ("test.png", "image/png", img_bytes)}

    boundary, body = make_multipart(fields, files)

    base = os.getenv("API_BASE", "http://127.0.0.1:8000").rstrip("/")
    req = Request(f"{base}/predict", data=body, method="POST")
    req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
    req.add_header("Content-Length", str(len(body)))

    with urlopen(req) as resp:
        print(resp.read().decode("utf-8"))


if __name__ == "__main__":
    main()

