const key = new URLSearchParams(window.location.search).get("key") || "";
const list = document.getElementById("task-list");

async function request(path, method = "GET") {
  const response = await fetch(`${path}?key=${encodeURIComponent(key)}`, { method });
  return response.json();
}

async function loadTasks() {
  const data = await request("/api/pending/");
  list.innerHTML = "";
  if (!data.items || !data.items.length) {
    list.innerHTML = "<div class='card'>No pending tasks.</div>";
    return;
  }

  data.items.forEach((task) => {
    const card = document.createElement("div");
    card.className = "card";
    card.innerHTML = `
      <h3>Task #${task.id} - ${task.category}</h3>
      <p><strong>Name:</strong> ${task.name}</p>
      <p><strong>Phone:</strong> ${task.phone_number}</p>
      <p><strong>Address:</strong> ${task.address || "-"}</p>
      <p><strong>Description:</strong> ${task.description}</p>
      <button class="approve">Approve</button>
      <button class="reject">Reject</button>
    `;

    card.querySelector(".approve").addEventListener("click", async () => {
      await request(`/api/task/${task.id}/approve/`, "POST");
      loadTasks();
    });
    card.querySelector(".reject").addEventListener("click", async () => {
      await request(`/api/task/${task.id}/reject/`, "POST");
      loadTasks();
    });
    list.appendChild(card);
  });
}

loadTasks();
