// ===============================
// 🌐 API BASE URL (Render Backend)
// ===============================
const API_BASE = "https://dropvault-2.onrender.com";  // ✅ Update for live deployment


// ===============================
// 📌 Copy Share Link
// ===============================
function copyLink(id) {
  const input = document.getElementById(id);
  if (!input) return;
  input.select();
  input.setSelectionRange(0, 99999);
  document.execCommand("copy");
  alert("✅ Link copied!");
}


// ===============================
// ⏳ Countdown Timer
// ===============================
function startCountdown() {
  const timers = document.querySelectorAll(".countdown");
  timers.forEach(timer => {
    const expiry = new Date(timer.dataset.expiry);
    function updateCountdown() {
      const diff = expiry - new Date();
      if (diff <= 0) return (timer.textContent = "⏰ Expired");

      const h = Math.floor(diff / (1000 * 60 * 60));
      const m = Math.floor((diff % (1000 * 60 * 60)) / 60000);
      const s = Math.floor((diff % 60000) / 1000);
      timer.textContent = `${h}h ${m}m ${s}s left`;
    }
    updateCountdown();
    setInterval(updateCountdown, 1000);
  });
}


// ===============================
// 📊 Progress Bar Animation
// ===============================
function animateProgressBars() {
  document.querySelectorAll(".progress-bar").forEach(bar => {
    const width = bar.style.width;
    bar.style.width = "0";
    setTimeout(() => {
      bar.style.transition = "width 1s";
      bar.style.width = width;
    }, 200);
  });
}


// ===============================
// 🚀 Upload File API → Flask Backend
// ===============================
document.addEventListener("DOMContentLoaded", () => {
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


async function uploadFileAPI() {
  const fileInput = document.getElementById("file");
  const msg = document.getElementById("upload-msg");

  if (!fileInput.files.length) {
    msg.textContent = "❌ No file selected.";
    msg.style.color = "red";
    return;
  }

  const formData = new FormData();
  formData.append("file", fileInput.files[0]);

  try {
    const res = await fetch(`${API_BASE}/api/upload`, {
      method: "POST",
      headers: {
        "Authorization": localStorage.getItem("token") // user id stored after login
      },
      body: formData
    });

    const data = await res.json();

    if (res.ok) {
      msg.textContent = "✅ File uploaded successfully!";
      msg.style.color = "green";
      fileInput.value = "";

      // store generated link and show user
      alert("🔗 Share link: " + data.share_url);
    } else {
      msg.textContent = "❌ Upload failed";
      msg.style.color = "red";
    }

  } catch (error) {
    msg.textContent = "🚨 Server Error. Try again.";
    msg.style.color = "red";
  }
}


// ===============================
// 🔑 LOGIN FUNCTION (POST to Backend)
// ===============================
async function loginUser() {
  const email = document.getElementById("email").value;
  const password = document.getElementById("password").value;
  const msg = document.getElementById("login-msg");

  const res = await fetch(`${API_BASE}/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password })
  });

  const data = await res.json();

  if (res.ok) {
    localStorage.setItem("token", data.token); // store user id as token
    msg.textContent = "✅ Login successful!";
    msg.style.color = "green";
    window.location.href = "/dashboard.html"; // redirect to dashboard
  } else {
    msg.textContent = "❌ " + data.message;
    msg.style.color = "red";
  }
}
