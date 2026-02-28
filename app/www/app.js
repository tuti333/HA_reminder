const form = document.getElementById("form");
const list = document.getElementById("list");

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
    await fetch(`api/reminders/${id}`, {
      method: "PUT",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(data)
    });
  } else {
    await fetch("api/reminders", {
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
  const res = await fetch("api/reminders");
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
      await fetch(`api/reminders/${r.id}`, { method: "DELETE" });
      load();
    };

    li.appendChild(edit);
    li.appendChild(del);
    list.appendChild(li);
  });
  // refresh schedule display as well
  loadSchedule();
}

// helpers for user actions (currently just log, can be extended)
function markAllTaken(person, period) {
  console.log(`mark all taken for ${person} ${period}`);
}
function skipAll(person, period) {
  console.log(`skip all for ${person} ${period}`);
}

async function loadSchedule() {
  const res = await fetch("api/today");
  if (!res.ok) return;
  const payload = await res.json();
  const schedule = payload.schedule || {};

  // for each person and period, fill the corresponding container
  Object.keys(schedule).forEach(person => {
    const periods = schedule[person];
    Object.keys(periods).forEach(period => {
      // match element id like 'Magda-rano' or 'Mateusz-wieczór'
      const el = document.getElementById(`${person}-${period}`);
      if (!el) return;
      // clear out old content
      el.innerHTML = '';

      if (periods[period].length > 0) {
        const ul = document.createElement('ul');
        periods[period].forEach(r => {
          const li = document.createElement('li');
          li.innerHTML = `<strong>${r.name}</strong> (${r.dose})`;
          ul.appendChild(li);
        });
        el.appendChild(ul);

        const actionDiv = document.createElement('div');
        actionDiv.className = 'actions';
        const taken = document.createElement('button');
        taken.textContent = 'Wzięte';
        taken.onclick = () => markAllTaken(person, period);
        const skipped = document.createElement('button');
        skipped.textContent = 'Pominięte';
        skipped.onclick = () => skipAll(person, period);
        actionDiv.appendChild(taken);
        actionDiv.appendChild(skipped);
        el.appendChild(actionDiv);
      }
    });
  });
}

load();
loadSchedule();