const form = document.getElementById("form");
const list = document.getElementById("list");

form.addEventListener("submit", async (e) => {
  e.preventDefault();

  const id = document.getElementById("id").value;
  const data = {
    name: document.getElementById("name").value,
    time: document.getElementById("time").value,
    dose: parseInt(document.getElementById("dose").value)
  };

  if (id) {
    await fetch(`/api/reminders/${id}`, {
      method: "PUT",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(data)
    });
  } else {
    await fetch("/api/reminders", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(data)
    });
  }

  resetForm();
  load();
});

function resetForm() {
  form.reset();
  document.getElementById("id").value = "";
}

async function load() {
  const res = await fetch("/api/reminders");
  const data = await res.json();

  list.innerHTML = "";
  data.forEach(r => {
    const li = document.createElement("li");
    li.textContent = `${r.name} – ${r.time} (${r.dose})`;

    const edit = document.createElement("button");
    edit.textContent = "Edytuj";
    edit.onclick = () => {
      document.getElementById("id").value = r.id;
      document.getElementById("name").value = r.name;
      document.getElementById("time").value = r.time;
      document.getElementById("dose").value = r.dose;
    };

    const del = document.createElement("button");
    del.textContent = "Usuń";
    del.onclick = async () => {
      await fetch(`/api/reminders/${r.id}`, { method: "DELETE" });
      load();
    };

    li.appendChild(edit);
    li.appendChild(del);
    list.appendChild(li);
  });
}

load();