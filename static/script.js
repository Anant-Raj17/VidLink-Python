document.addEventListener("DOMContentLoaded", function () {
  fetchVideoList();
  document.getElementById("add-video-btn").addEventListener("click", addVideo);
});

async function fetchVideoList() {
  try {
    const response = await fetch("/get_videos");
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const data = await response.json();
    updateVideoList(data.videos);
  } catch (error) {
    console.error("Error fetching video list:", error);
    // Display an error message to the user
    const videoList = document.getElementById("video-list");
    videoList.innerHTML =
      "<p>Error loading videos. Please try again later.</p>";
  }
}

function updateVideoList(videos) {
  const videoList = document.getElementById("video-list");
  videoList.innerHTML = "";
  videos.forEach((video) => {
    const videoItem = document.createElement("div");
    videoItem.className = "video-item";
    videoItem.innerHTML = `
            <span class="video-title">${video.title}</span>
            <button class="delete-video-btn" data-id="${video.id}">Delete</button>
        `;
    videoList.appendChild(videoItem);
  });

  // Add event listeners to delete buttons
  document.querySelectorAll(".delete-video-btn").forEach((button) => {
    button.addEventListener("click", deleteVideo);
  });
}

async function deleteVideo(event) {
  const videoId = event.target.getAttribute("data-id");
  try {
    const response = await fetch(`/delete_video/${videoId}`, {
      method: "DELETE",
    });
    if (response.ok) {
      fetchVideoList(); // Refresh the list after deletion
    } else {
      console.error("Failed to delete video");
    }
  } catch (error) {
    console.error("Error deleting video:", error);
  }
}

async function addVideo() {
  const urlInput = document.getElementById("video-url-input");
  const url = urlInput.value.trim();

  if (!url) {
    alert("Please enter a YouTube URL");
    return;
  }

  try {
    const response = await fetch("/add_video", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ url: url }),
    });

    const data = await response.json();
    alert(data.message);

    if (response.ok) {
      urlInput.value = "";
      fetchVideoList(); // Refresh the list after adding a new video
    }
  } catch (error) {
    console.error("Error:", error);
    alert("An error occurred while adding the video");
  }
}

async function sendMessage() {
  const userInput = document.getElementById("user-input");
  const question = userInput.value.trim();

  if (!question) {
    alert("Please enter a question");
    return;
  }

  addMessageToChat("user", question);
  userInput.value = "";

  try {
    const response = await fetch("/ask_question", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ question: question }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    addMessageToChat("ai", data.answer);
  } catch (error) {
    console.error("Error:", error);
    addMessageToChat("ai", "An error occurred while processing your question");
  }
}

function addMessageToChat(sender, message) {
  const chatMessages = document.getElementById("chat-messages");
  const messageElement = document.createElement("div");
  messageElement.classList.add("message", `${sender}-message`);
  messageElement.textContent = message;
  chatMessages.appendChild(messageElement);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}
