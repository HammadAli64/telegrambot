const grid = document.getElementById("task-grid");
const detail = document.getElementById("task-detail");
const searchInput = document.getElementById("search-input");
const statusFilter = document.getElementById("status-filter");
const searchBtn = document.getElementById("search-btn");
const clearBtn = document.getElementById("clear-btn");
const prevBtn = document.getElementById("prev-btn");
const nextBtn = document.getElementById("next-btn");
const pageInfo = document.getElementById("page-info");
let currentPage = 1;
let totalPages = 1;
let currentQuery = "";
let currentStatus = "";
let currentItems = [];
let activeTaskId = null;
let flashTimeout = null;

function showFlash(message) {
  let flash = document.getElementById("flash-message");
  if (!flash) {
    flash = document.createElement("div");
    flash.id = "flash-message";
    flash.className = "card";
    flash.style.position = "fixed";
    flash.style.top = "12px";
    flash.style.right = "12px";
    flash.style.zIndex = "9999";
    flash.style.background = "#16a34a";
    flash.style.color = "#fff";
    flash.style.padding = "10px 14px";
    flash.style.margin = "0";
    document.body.appendChild(flash);
  }
  flash.textContent = message;
  flash.style.display = "block";
  if (flashTimeout) clearTimeout(flashTimeout);
  flashTimeout = setTimeout(() => {
    flash.style.display = "none";
  }, 2000);
}

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
  card.className = "card task-item";
  card.dataset.taskId = String(task.id);
  card.innerHTML = `
    <h3>Task #${task.id}</h3>
    <p><strong>Name:</strong> ${task.name || "-"}</p>
    <p><strong>Category:</strong> ${task.category || "-"}</p>
    <p><strong>Status:</strong> ${task.status}</p>
  `;
  card.addEventListener("click", () => showTaskDetail(task.id));
  if (activeTaskId === task.id) {
    card.classList.add("active");
  }
  return card;
}

function getTaskById(taskId) {
  return currentItems.find((t) => t.id === taskId);
}

function showTaskDetail(taskId) {
  const task = getTaskById(taskId);
  if (!task) return;
  activeTaskId = taskId;
  detail.style.display = "block";
  detail.innerHTML = `
    <h3>Task #${task.id}</h3>
    <label>Name <input id="detail-name" value="${task.name || ""}"></label>
    <label>Phone <input id="detail-phone" value="${task.phone_number || ""}"></label>
    <label>Category <input id="detail-category" value="${task.category || ""}"></label>
    <label>Address <input id="detail-address" value="${task.address || ""}"></label>
    <label>Description <input id="detail-description" value="${task.description || ""}"></label>
    <p><strong>Status:</strong> ${task.status}</p>
    <div>
      <button id="detail-approve" class="approve">Approve</button>
      <button id="detail-save">Save</button>
      <button id="detail-delete" class="reject">Delete</button>
    </div>
  `;

  document.getElementById("detail-approve").addEventListener("click", async () => {
    await request(`/api/task/${task.id}/approve/`, "POST");
    showFlash("Task approved");
    await loadTasks();
  });
  document.getElementById("detail-save").addEventListener("click", async () => {
    const payload = {
      name: document.getElementById("detail-name").value,
      phone_number: document.getElementById("detail-phone").value,
      category: document.getElementById("detail-category").value,
      address: document.getElementById("detail-address").value,
      description: document.getElementById("detail-description").value,
    };
    await request(`/api/task/${task.id}/update/`, "POST", payload);
    showFlash("Task saved");
    await loadTasks();
  });
  document.getElementById("detail-delete").addEventListener("click", async () => {
    await request(`/api/task/${task.id}/delete/`, "POST");
    showFlash("Task deleted");
    activeTaskId = null;
    detail.style.display = "none";
    await loadTasks();
  });
  renderGridSelection();
}

function renderGridSelection() {
  grid.querySelectorAll(".task-item").forEach((node) => {
    const id = Number(node.dataset.taskId);
    node.classList.toggle("active", id === activeTaskId);
  });
}

async function loadTasks() {
  const data = await request(
    `/api/tasks/?page=${currentPage}&page_size=10&q=${encodeURIComponent(currentQuery)}&status=${encodeURIComponent(currentStatus)}`
  );
  grid.innerHTML = "";
  if (!data.items || !data.items.length) {
    grid.innerHTML = "<div class='card'>No tasks found.</div>";
    detail.style.display = "none";
    activeTaskId = null;
    pageInfo.textContent = `Page ${currentPage}`;
    return;
  }
  currentItems = data.items;
  totalPages = data.total_pages || 1;
  pageInfo.textContent = `Page ${data.page} of ${totalPages} (Total: ${data.total})`;
  data.items.forEach((task) => grid.appendChild(taskCard(task)));
  if (!activeTaskId || !getTaskById(activeTaskId)) {
    activeTaskId = data.items[0].id;
  }
  showTaskDetail(activeTaskId);
}

searchBtn.addEventListener("click", () => {
  currentQuery = searchInput.value.trim();
  currentStatus = statusFilter.value;
  currentPage = 1;
  loadTasks();
});

clearBtn.addEventListener("click", () => {
  searchInput.value = "";
  statusFilter.value = "";
  currentQuery = "";
  currentStatus = "";
  currentPage = 1;
  loadTasks();
});

prevBtn.addEventListener("click", () => {
  if (currentPage > 1) {
    currentPage -= 1;
    loadTasks();
  }
});

nextBtn.addEventListener("click", () => {
  if (currentPage < totalPages) {
    currentPage += 1;
    loadTasks();
  }
});

loadTasks();
