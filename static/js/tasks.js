const list = document.getElementById("task-list");

async function request(path, method = "GET", body = null) {
  const options = { method };
  if (body) {
    options.headers = { "Content-Type": "application/json" };
    options.body = JSON.stringify(body);
  }
  const response = await fetch(path, options);
  if (response.status === 401) {
    window.location.href = "/admin/login/";
    return { items: [] };
  }
  return response.json();
}

function taskCard(task) {
  const card = document.createElement("div");
  card.className = "card";
  card.innerHTML = `
    <h3>Task #${task.id}</h3>
    <label>Name <input data-field="name" value="${task.name || ""}"></label>
    <label>Phone <input data-field="phone_number" value="${task.phone_number || ""}"></label>
    <label>Category <input data-field="category" value="${task.category || ""}"></label>
    <label>Address <input data-field="address" value="${task.address || ""}"></label>
    <label>Description <input data-field="description" value="${task.description || ""}"></label>
    <label>Status
      <select data-field="status">
        <option value="pending" ${task.status === "pending" ? "selected" : ""}>pending</option>
        <option value="approved" ${task.status === "approved" ? "selected" : ""}>approved</option>
        <option value="rejected" ${task.status === "rejected" ? "selected" : ""}>rejected</option>
      </select>
    </label>
    <div>
      <button class="approve">Approve</button>
      <button class="reject">Reject</button>
      <button class="save">Save</button>
      <button class="reject delete">Delete</button>
    </div>
  `;

  card.querySelector(".approve").addEventListener("click", async () => {
    await request(`/api/task/${task.id}/approve/`, "POST");
    loadTasks();
  });

  card.querySelector(".reject").addEventListener("click", async () => {
    await request(`/api/task/${task.id}/reject/`, "POST");
    loadTasks();
  });

  card.querySelector(".save").addEventListener("click", async () => {
    const payload = {};
    card.querySelectorAll("[data-field]").forEach((el) => {
      payload[el.getAttribute("data-field")] = el.value;
    });
    await request(`/api/task/${task.id}/update/`, "POST", payload);
    loadTasks();
  });

  card.querySelector(".delete").addEventListener("click", async () => {
    await request(`/api/task/${task.id}/delete/`, "POST");
    loadTasks();
  });
  return card;
}

async function loadTasks() {
  const data = await request("/api/tasks/");
  list.innerHTML = "";
  if (!data.items || !data.items.length) {
    list.innerHTML = "<div class='card'>No tasks found.</div>";
    return;
  }
  data.items.forEach((task) => list.appendChild(taskCard(task)));
}

loadTasks();
