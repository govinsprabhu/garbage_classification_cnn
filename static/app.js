(() => {
  const form = document.getElementById('upload-form');
  const input = document.getElementById('image-input');
  const submitBtn = document.getElementById('submit-btn');
  const preview = document.getElementById('preview');
  const previewImg = document.getElementById('preview-img');
  const filenameEl = document.getElementById('filename');
  const result = document.getElementById('result');
  const labelEl = document.getElementById('label');
  const confidenceEl = document.getElementById('confidence');

  function resetUI() {
    result.classList.add('hidden');
  }

  input.addEventListener('change', () => {
    resetUI();
    const file = input.files && input.files[0];
    if (!file) {
      preview.classList.add('hidden');
      previewImg.src = '';
      filenameEl.textContent = '';
      return;
    }
    const url = URL.createObjectURL(file);
    previewImg.src = url;
    filenameEl.textContent = file.name;
    preview.classList.remove('hidden');
  });

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const file = input.files && input.files[0];
    if (!file) return;

    submitBtn.disabled = true;
    submitBtn.textContent = 'Predicting...';

    try {
      const formData = new FormData();
      formData.append('image', file);
      const resp = await fetch('/predict', {
        method: 'POST',
        body: formData
      });
      const data = await resp.json();
      if (!resp.ok) {
        throw new Error(data && data.error ? data.error : 'Prediction failed');
      }
      labelEl.textContent = data.prediction.label;
      //confidenceEl.textContent = `${(data.prediction.confidence * 100).toFixed(1)}%`;
      result.classList.remove('hidden');
    } catch (err) {
      alert(err.message || 'Something went wrong');
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = 'Predict';
    }
  });
})();


