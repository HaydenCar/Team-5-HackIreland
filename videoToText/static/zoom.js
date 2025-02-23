let scale = 1;
const image = document.getElementById("zoomed-image");

// Zoom In
document.getElementById("zoomIn").addEventListener("click", () => {
    scale *= 1.2;
    image.style.transform = `scale(${scale})`;
});

// Zoom Out
document.getElementById("zoomOut").addEventListener("click", () => {
    scale /= 1.2;
    image.style.transform = `scale(${scale})`;
});

// Reset Zoom
document.getElementById("reset").addEventListener("click", () => {
    scale = 1;
    image.style.transform = `scale(${scale})`;
});
