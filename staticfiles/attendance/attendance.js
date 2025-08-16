function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let c of cookies) {
      c = c.trim();
      if (c.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(c.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

document.getElementById('submit-att').addEventListener('click', async () => {
  const date = document.getElementById('att-date').value;
  const rows = document.querySelectorAll('tbody tr');
  const records = Array.from(rows).map(row => {
    const id = row.getAttribute('data-student-id');
    const radios = row.querySelectorAll(`input[name="att-${id}"]`);
    let status = 'Present';
    radios.forEach(r => { if (r.checked) status = r.value; });
    return { student_id: id, status };
  });

  const csrftoken = getCookie('csrftoken');

  const resp = await fetch("/mark-attendance/", {  // or use Django URL reverse path here
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': csrftoken
    },
    body: JSON.stringify({ date, records })
  });
  const data = await resp.json();
  if (data.ok) alert('Attendance saved');
  else alert('Error');
});
