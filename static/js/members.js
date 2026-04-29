const params = new URLSearchParams(window.location.search);
const key = params.get("key") || "";
const membersList = document.getElementById("members-list");

const userIdInput = document.getElementById("user-id");
const usernameInput = document.getElementById("username");
const fullNameInput = document.getElementById("full-name");

function endpoint(path) {
  return `${path}?key=${encodeURIComponent(key)}`;
}

async function loadMembers() {
  const response = await fetch(endpoint("/api/members/"));
  const data = await response.json();
  membersList.innerHTML = "<h2>Active Members</h2>";
  (data.items || []).forEach((member) => {
    const card = document.createElement("div");
    card.className = "card";
    card.innerHTML = `
      <p><strong>User ID:</strong> ${member.user_id}</p>
      <p><strong>Username:</strong> ${member.username || "-"}</p>
      <p><strong>Name:</strong> ${member.full_name || "-"}</p>
    `;
    membersList.appendChild(card);
  });
}

async function postJson(path, payload) {
  await fetch(endpoint(path), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

document.getElementById("add-btn").addEventListener("click", async () => {
  await postJson("/api/members/add/", {
    user_id: Number(userIdInput.value),
    username: usernameInput.value,
    full_name: fullNameInput.value,
  });
  loadMembers();
});

document.getElementById("remove-btn").addEventListener("click", async () => {
  await postJson("/api/members/remove/", { user_id: Number(userIdInput.value) });
  loadMembers();
});

loadMembers();
