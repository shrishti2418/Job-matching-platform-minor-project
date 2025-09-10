 
document.getElementById("resumeForm")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    let fileInput = document.getElementById("resumeFile");
    if (!fileInput.files.length) return alert("Please select a file!");
  
    let formData = new FormData();
    formData.append("file", fileInput.files[0]);
  
    let response = await fetch("/upload_resume", {
      method: "POST",
      body: formData
    });
  
    if (response.ok) {
      window.location.href = "/results"; // Redirect to results page
    } else {
      alert("Upload failed!");
    }
  });
  