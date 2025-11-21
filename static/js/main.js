//Copy Share link
function copyLink(id) {
  const input = document.getElementById(id);
  if (!input) return;
  input.select();
  input.setSelectionRange(0, 99999); // For mobile
  document.execCommand("copy");
  alert("✅ Link copied to clipboard!");
}

//Countdown Timer 
function startCountdown() {
  const timers = document.querySelectorAll(".countdown");

  timers.forEach(timer => {
    const expiry = new Date(timer.dataset.expiry);
    function updateCountdown() {
      const now = new Date();
      const diff = expiry - now;

      if (diff <= 0) {
        timer.textContent = "⏰ Expired";
        timer.classList.add("expired");
        return;
      }

      const hours = Math.floor(diff / (1000 * 60 * 60));
      const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
      const seconds = Math.floor((diff % (1000 * 60)) / 1000);

      timer.textContent = `${hours}h ${minutes}m ${seconds}s left`;
    }
    updateCountdown();
    setInterval(updateCountdown, 1000);
  });
}

// Animate Progress Bar 
function animateProgressBars() {
  const bars = document.querySelectorAll(".progress-bar");
  bars.forEach(bar => {
    const width = bar.style.width;
    bar.style.width = "0";
    setTimeout(() => {
      bar.style.transition = "width 1s ease-in-out";
      bar.style.width = width;
    }, 200);
  });
}

//  Run on Page Load 
document.addEventListener("DOMContentLoaded", function () {
    const uploadForm = document.getElementById("uploadForm");
  if (uploadForm) {
    uploadForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      await uploadFileAPI();
    });
  }
  startCountdown();
  animateProgressBars();
});

const API_BASE = "http://127.0.0.1:8000";   // your Django backend

// UPLOAD FILE FUNCTION
async function uploadFileAPI() {
  const fileInput = document.getElementById("file");
  const msg = document.getElementById("upload-msg");

  if (!fileInput.files.length) {
    msg.textContent = "❌ Please select a file.";
    msg.style.color = "red";
    return;
  }

  const formData = new FormData();
  formData.append("file", fileInput.files[0]);

  try {
    const res = await fetch(`${API_BASE}/files/upload/`, {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${localStorage.getItem("token")}`
      },
      body: formData
    });

    const data = await res.json();

    if (res.ok) {
      msg.textContent = "✅ File uploaded successfully!";
      msg.style.color = "green";
      fileInput.value = "";
    } else {
      msg.textContent = "❌ Upload failed: " + (data.message || "Try again.");
      msg.style.color = "red";
    }

  } catch (err) {
    msg.textContent = "❌ Server error. File not uploaded.";
    msg.style.color = "red";
  }
}
