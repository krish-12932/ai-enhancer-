const translations = {
    en: {
        title: "4K AI Upscaler",
        subtitle: "Convert your images to ultra-high resolution instantly.",
        uploadText: "Drag & Drop or Click to Upload",
        upscaleBtn: "Upscale to 4K",
        processingText: "Enhancing your image with AI...",
        timerText: "Your download will be ready in ",
        successTitle: "Processing Complete!",
        downloadBtn: "Download 4K Image",
        resetBtn: "Upscale Another",
        langBtn: "हिन्दी"
    },
    hi: {
        title: "4K एआई अपस्केलर",
        subtitle: "अपनी छवियों को तुरंत अल्ट्रा-हाई रिज़ॉल्यूशन में बदलें।",
        uploadText: "खींचें और छोड़ें या अपलोड करने के लिए क्लिक करें",
        upscaleBtn: "4K में अपस्केल करें",
        processingText: "एआई के साथ आपकी छवि को बेहतर बना रहा है...",
        timerText: "आपका डाउनलोड तैयार होगा ",
        successTitle: "प्रक्रिया पूर्ण!",
        downloadBtn: "4K छवि डाउनलोड करें",
        resetBtn: "दूसरी छवि अपस्केल करें",
        langBtn: "English"
    }
};

let currentLang = 'en';
let selectedFile = null;

const uploadArea = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');
const upscaleBtn = document.getElementById('upscale-btn');
const langBtn = document.getElementById('lang-btn');

// Sections
const sections = {
    upload: document.getElementById('upload-section'),
    processing: document.getElementById('processing-section'),
    ad: document.getElementById('ad-section'),
    download: document.getElementById('download-section')
};

function switchSection(name) {
    Object.values(sections).forEach(el => el.classList.remove('active'));
    sections[name].classList.add('active');
}

function toggleLanguage() {
    currentLang = currentLang === 'en' ? 'hi' : 'en';
    const t = translations[currentLang];

    document.getElementById('title').textContent = t.title;
    document.getElementById('subtitle').textContent = t.subtitle;
    document.getElementById('upload-text').textContent = t.uploadText;
    document.getElementById('upscale-btn').textContent = t.upscaleBtn;
    document.getElementById('processing-text').textContent = t.processingText;
    // For timer-text, we only update the static part if it's currently visible or just rely on startAdTimer's interval
    // But since startAdTimer overwrites innerHTML, we don't strictly need to update it here unless the ad section is active without the timer running (unlikely).
    // Let's just update the static text part if we were to support it, but for now, the interval handles the text.

    document.getElementById('success-title').textContent = t.successTitle;
    document.getElementById('download-link').textContent = t.downloadBtn;
    document.getElementById('reset-btn').textContent = t.resetBtn;
    document.getElementById('lang-btn').textContent = t.langBtn;
}

// File Handling
uploadArea.addEventListener('click', () => fileInput.click());

fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        handleFile(e.target.files[0]);
    }
});

uploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadArea.classList.add('dragover');
});

uploadArea.addEventListener('dragleave', () => {
    uploadArea.classList.remove('dragover');
});

uploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadArea.classList.remove('dragover');
    if (e.dataTransfer.files.length > 0) {
        handleFile(e.dataTransfer.files[0]);
    }
});

function handleFile(file) {
    if (!file.type.match('image.*')) {
        alert("Please upload an image file (PNG, JPG)");
        return;
    }
    selectedFile = file;
    document.getElementById('upload-text').textContent = file.name;
    upscaleBtn.disabled = false;
}

// Upscale Logic
upscaleBtn.addEventListener('click', async () => {
    if (!selectedFile) return;

    switchSection('processing');

    const formData = new FormData();
    formData.append('image', selectedFile);

    try {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.success) {
            startAdTimer(data.filename, data.width, data.height);
        } else {
            alert('Error: ' + data.error);
            switchSection('upload');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('An error occurred during upload.');
        switchSection('upload');
    }
});

function startAdTimer(filename, width, height) {
    switchSection('ad');
    let timeLeft = 5;
    const timerSpan = document.getElementById('timer');
    const timerTextP = document.getElementById('timer-text');

    const updateText = () => {
        const t = translations[currentLang];
        timerTextP.innerHTML = `${t.timerText} <span id="timer">${timeLeft}</span>s`;
    };

    updateText(); // Initial set

    const interval = setInterval(() => {
        timeLeft--;
        updateText();

        if (timeLeft <= 0) {
            clearInterval(interval);
            showDownload(filename, width, height);
        }
    }, 1000);
}

function showDownload(filename, width, height) {
    const downloadLink = document.getElementById('download-link');
    const resolutionText = document.getElementById('resolution-text');

    downloadLink.href = `/download/${filename}`;
    if (width && height) {
        resolutionText.textContent = `Resolution: ${width} x ${height}`;
    } else {
        resolutionText.textContent = 'Resolution: 4K (Ultra HD)';
    }
    switchSection('download');
}

document.getElementById('reset-btn').addEventListener('click', () => {
    selectedFile = null;
    document.getElementById('upload-text').textContent = translations[currentLang].uploadText;
    upscaleBtn.disabled = true;
    fileInput.value = '';
    switchSection('upload');
});
