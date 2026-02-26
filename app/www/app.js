const form = document.getElementById("form");
const list = document.getElementById("list");

function updateTodayDate() {
    const today = new Date();
    const options = { 
        weekday: 'long', 
        year: 'numeric', 
        month: 'long', 
        day: 'numeric' 
    };
    const formattedDate = today.toLocaleDateString('pl-PL', options);
    document.getElementById('todayDate').textContent = formattedDate;
}

document.addEventListener('DOMContentLoaded', updateTodayDate);

form.addEventListener("submit", async (e) => {
  e.preventDefault();

  const id = document.getElementById("id").value;
  // collect checkbox selections
  const timeFieldset = document.getElementById("time");
  const times = Array.from(timeFieldset.querySelectorAll("input[type=checkbox]:checked")).map(i => i.value);
  const data = {
    person: document.getElementById("userSelect").value || "",
    name: document.getElementById("name").value,
    time: times,
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
    li.textContent = `${r.person} ${r.name} – ${Array.isArray(r.time)?r.time.join(','):r.time} (${r.dose})`;

    const edit = document.createElement("button");
    edit.textContent = "Edytuj";
    edit.onclick = () => {
      document.getElementById("id").value = r.id;
      document.getElementById("name").value = r.name;
      const timeFieldset = document.getElementById("time");
      Array.from(timeFieldset.querySelectorAll("input[type=checkbox]")).forEach(cb => cb.checked = false);
      if (Array.isArray(r.time)) {
        r.time.forEach(val => {
          const cb = timeFieldset.querySelector(`input[type=checkbox][value="${val}"]`);
          if (cb) cb.checked = true;
        });
      }
      document.getElementById("dose").value = r.dose;
      document.getElementById("userSelect").value = r.person;
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