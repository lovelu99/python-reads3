from flask import Flask, render_template_string, jsonify
import boto3
import os
import base64

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>S3 Gallery</title>
  <link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Sans:wght@300;400;500&display=swap" rel="stylesheet"/>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    :root {
      --bg: #0a0a0a;
      --surface: #111;
      --accent: #e8ff47;
      --text: #f0f0f0;
      --muted: #555;
      --radius: 4px;
    }

    body {
      background: var(--bg);
      color: var(--text);
      font-family: 'DM Sans', sans-serif;
      min-height: 100vh;
    }

    header {
      padding: 2.5rem 3rem 1.5rem;
      border-bottom: 1px solid #1e1e1e;
      display: flex;
      align-items: flex-end;
      gap: 1.5rem;
    }

    header h1 {
      font-family: 'Bebas Neue', sans-serif;
      font-size: clamp(2.5rem, 6vw, 5rem);
      letter-spacing: 0.04em;
      line-height: 1;
      color: var(--accent);
    }

    header span {
      font-size: 0.85rem;
      color: var(--muted);
      padding-bottom: 0.4rem;
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }

    #status {
      padding: 1rem 3rem;
      font-size: 0.8rem;
      color: var(--muted);
      letter-spacing: 0.06em;
      text-transform: uppercase;
      min-height: 2.5rem;
    }

    #status.error { color: #ff5555; }
    #status.success { color: var(--accent); }

    .gallery {
      padding: 1rem 3rem 4rem;
      columns: 4 280px;
      column-gap: 12px;
    }

    .card {
      break-inside: avoid;
      margin-bottom: 12px;
      position: relative;
      overflow: hidden;
      border-radius: var(--radius);
      background: var(--surface);
      cursor: pointer;
      opacity: 0;
      transform: translateY(20px);
      transition: opacity 0.4s ease, transform 0.4s ease, box-shadow 0.3s ease;
    }

    .card.visible {
      opacity: 1;
      transform: translateY(0);
    }

    .card:hover { box-shadow: 0 0 0 2px var(--accent); }

    .card img {
      width: 100%;
      display: block;
      object-fit: cover;
    }

    .card .label {
      position: absolute;
      bottom: 0; left: 0; right: 0;
      padding: 0.6rem 0.8rem;
      background: linear-gradient(transparent, rgba(0,0,0,0.85));
      font-size: 0.72rem;
      color: #ccc;
      letter-spacing: 0.04em;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      opacity: 0;
      transition: opacity 0.2s ease;
    }

    .card:hover .label { opacity: 1; }

    /* Lightbox */
    #lightbox {
      display: none;
      position: fixed;
      inset: 0;
      background: rgba(0,0,0,0.92);
      z-index: 100;
      align-items: center;
      justify-content: center;
      flex-direction: column;
      gap: 1rem;
      padding: 2rem;
    }

    #lightbox.open { display: flex; }

    #lightbox img {
      max-width: 90vw;
      max-height: 80vh;
      object-fit: contain;
      border-radius: var(--radius);
      box-shadow: 0 0 60px rgba(232,255,71,0.1);
    }

    #lightbox-name {
      font-size: 0.8rem;
      color: var(--muted);
      letter-spacing: 0.08em;
    }

    #lightbox-close {
      position: fixed;
      top: 1.5rem; right: 2rem;
      background: none;
      border: 1px solid var(--muted);
      color: var(--text);
      font-size: 1rem;
      padding: 0.3rem 0.8rem;
      cursor: pointer;
      border-radius: var(--radius);
      letter-spacing: 0.06em;
      transition: border-color 0.2s, color 0.2s;
    }

    #lightbox-close:hover { border-color: var(--accent); color: var(--accent); }

    .empty {
      padding: 4rem 3rem;
      color: var(--muted);
      font-size: 0.9rem;
      letter-spacing: 0.06em;
    }

    .loader {
      display: inline-block;
      width: 14px; height: 14px;
      border: 2px solid var(--muted);
      border-top-color: var(--accent);
      border-radius: 50%;
      animation: spin 0.7s linear infinite;
      vertical-align: middle;
      margin-right: 8px;
    }

    @keyframes spin { to { transform: rotate(360deg); } }
  </style>
</head>
<body>

<header>
  <h1>S3 Gallery</h1>
  <span id="bucket-name">{{ bucket }}</span>
</header>

<div id="status"><span class="loader"></span> Loading images...</div>

<div class="gallery" id="gallery"></div>
<div class="empty" id="empty" style="display:none">No images found in bucket.</div>

<div id="lightbox">
  <button id="lightbox-close" onclick="closeLightbox()">✕ CLOSE</button>
  <img id="lightbox-img" src="" alt=""/>
  <div id="lightbox-name"></div>
</div>

<script>
  async function loadImages() {
    const status = document.getElementById('status');
    const gallery = document.getElementById('gallery');
    const empty = document.getElementById('empty');

    try {
      const res = await fetch('/images');
      const data = await res.json();

      if (data.error) {
        status.textContent = '⚠ ' + data.error;
        status.className = 'error';
        return;
      }

      if (data.images.length === 0) {
        status.textContent = '';
        empty.style.display = 'block';
        return;
      }

      status.textContent = `${data.images.length} image${data.images.length > 1 ? 's' : ''} found`;
      status.className = 'success';

      data.images.forEach((img, i) => {
        const card = document.createElement('div');
        card.className = 'card';
        card.innerHTML = `
          <img src="data:image/${img.ext};base64,${img.data}" alt="${img.name}" loading="lazy"/>
          <div class="label">${img.name}</div>
        `;
        card.onclick = () => openLightbox(`data:image/${img.ext};base64,${img.data}`, img.name);
        gallery.appendChild(card);

        setTimeout(() => card.classList.add('visible'), i * 60);
      });

    } catch (e) {
      status.textContent = '⚠ Failed to connect to server';
      status.className = 'error';
    }
  }

  function openLightbox(src, name) {
    document.getElementById('lightbox-img').src = src;
    document.getElementById('lightbox-name').textContent = name;
    document.getElementById('lightbox').classList.add('open');
  }

  function closeLightbox() {
    document.getElementById('lightbox').classList.remove('open');
  }

  document.getElementById('lightbox').addEventListener('click', function(e) {
    if (e.target === this) closeLightbox();
  });

  document.addEventListener('keydown', e => { if (e.key === 'Escape') closeLightbox(); });

  loadImages();
</script>
</body>
</html>
"""

def get_image_ext(key):
    ext = key.lower().split('.')[-1]
    return 'jpeg' if ext == 'jpg' else ext

@app.route('/')
def index():
    bucket = os.getenv('S3_BUCKET_NAME', 'my-app-bucket')
    return render_template_string(HTML, bucket=bucket)

@app.route('/images')
def images():
    bucket = os.getenv('S3_BUCKET_NAME', 'my-app-bucket')
    region = os.getenv('AWS_REGION', 'us-east-2')

    IMAGE_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp', 'svg'}

    try:
        s3 = boto3.client('s3', region_name=region)

        paginator = s3.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=bucket)

        results = []
        for page in pages:
            if 'Contents' not in page:
                continue
            for obj in page['Contents']:
                key = obj['Key']
                ext = key.lower().split('.')[-1]

                if ext not in IMAGE_EXTENSIONS:
                    continue

                # Read image and encode to base64
                response = s3.get_object(Bucket=bucket, Key=key)
                image_data = base64.b64encode(response['Body'].read()).decode('utf-8')

                results.append({
                    'name': key.split('/')[-1],
                    'key': key,
                    'ext': get_image_ext(key),
                    'data': image_data
                })

        return jsonify({'images': results})

    except Exception as e:
        return jsonify({'error': str(e), 'images': []})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
