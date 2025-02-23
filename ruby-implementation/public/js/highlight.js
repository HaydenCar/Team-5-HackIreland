let isHighlighting = false;
let startX, startY, endX, endY;

const image = document.getElementById('uploaded-image');
const canvas = document.createElement('canvas');
const ctx = canvas.getContext('2d');
canvas.width = image.width;
canvas.height = image.height;
canvas.style.position = 'absolute';
canvas.style.left = image.offsetLeft + 'px';
canvas.style.top = image.offsetTop + 'px';
canvas.style.pointerEvents = 'none';
image.parentElement.appendChild(canvas);

image.addEventListener('mousedown', (e) => {
  if (!isHighlighting) return;
  startX = e.offsetX;
  startY = e.offsetY;
});

image.addEventListener('mousemove', (e) => {
  if (!isHighlighting || !startX || !startY) return;
  endX = e.offsetX;
  endY = e.offsetY;
  drawRectangle();
});

image.addEventListener('mouseup', () => {
  if (!isHighlighting) return;
  extractTextFromHighlight();
  isHighlighting = false;
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  startX = startY = endX = endY = null;
});

document.getElementById('highlight-button').addEventListener('click', () => {
  isHighlighting = true;
  alert('Click and drag on the image to highlight an area.');
});

function drawRectangle() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.strokeStyle = 'red';
  ctx.lineWidth = 2;
  ctx.strokeRect(startX, startY, endX - startX, endY - startY);
}

async function extractTextFromHighlight() {
  const formData = new FormData();
  formData.append('image', await getHighlightedImage());
  formData.append('x', startX);
  formData.append('y', startY);
  formData.append('width', endX - startX);
  formData.append('height', endY - startY);

  const response = await fetch('/highlight', {
    method: 'POST',
    body: formData,
  });

  const result = await response.text();
  alert('Extracted Text: ' + result);
}

function getHighlightedImage() {
  return new Promise((resolve) => {
    const tempCanvas = document.createElement('canvas');
    const tempCtx = tempCanvas.getContext('2d');
    tempCanvas.width = endX - startX;
    tempCanvas.height = endY - startY;
    tempCtx.drawImage(
      image,
      startX, startY, endX - startX, endY - startY,
      0, 0, endX - startX, endY - startY
    );
    tempCanvas.toBlob(resolve, 'image/jpeg');
  });
}