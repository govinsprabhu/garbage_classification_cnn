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
  const rateEl = document.getElementById('rate');
  const earnings1kgEl = document.getElementById('earnings-1kg');
  const earnings5kgEl = document.getElementById('earnings-5kg');
  const earnings10kgEl = document.getElementById('earnings-10kg');
  const recyclingTipEl = document.getElementById('recycling-tip');

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
      // Update basic info
      labelEl.textContent = data.prediction.label.toUpperCase();
      
      // Find the highest probability
      const probs = data.prediction.probabilities;
      const maxProb = Math.max(...Object.values(probs));
      confidenceEl.textContent = `${(maxProb * 100).toFixed(1)}%`;
      
      // Update recycling information
      const recyclingInfo = data.prediction.recycling_info;
      rateEl.textContent = `$${recyclingInfo.rate_per_kg.toFixed(2)}`;
      earnings1kgEl.textContent = `$${recyclingInfo.example_earnings['1kg'].toFixed(2)}`;
      earnings5kgEl.textContent = `$${recyclingInfo.example_earnings['5kg'].toFixed(2)}`;
      earnings10kgEl.textContent = `$${recyclingInfo.example_earnings['10kg'].toFixed(2)}`;
      recyclingTipEl.textContent = recyclingInfo.tip;
      
      result.classList.remove('hidden');
    } catch (err) {
      alert(err.message || 'Something went wrong');
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = 'Predict';
    }
  });
})();


