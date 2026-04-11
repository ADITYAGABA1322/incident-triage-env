async function fetchJson(url, options = {}) {
  const response = await fetch(url, options);
  const contentType = response.headers.get("content-type") || "";
  const body = contentType.includes("application/json") ? await response.json() : await response.text();
  if (!response.ok) {
    const detail = typeof body === "object" ? body.detail || JSON.stringify(body) : body;
    throw new Error(`${response.status} ${response.statusText}: ${detail}`);
  }
  return body;
}

function safeText(value) {
  return value == null ? "--" : String(value);
}

function setHealthPill(status) {
  const pills = document.querySelectorAll("[data-health-pill]");
  pills.forEach((pill) => {
    pill.textContent = status === "healthy" ? "Healthy" : "Unavailable";
    pill.classList.toggle("is-pending", status !== "healthy");
  });
}

function renderTaskCards(target, tasks) {
  if (!target) return;
  target.innerHTML = "";
  Object.entries(tasks).forEach(([taskId, task]) => {
    const article = document.createElement("article");
    article.className = "task-card";
    article.innerHTML = `
      <span class="badge difficulty-${task.difficulty}">${task.difficulty}</span>
      <h3>${task.name}</h3>
      <p>Expected field: <strong>${task.expected_field || task.output_field}</strong></p>
      <div class="task-meta">
        <span class="badge">${taskId}</span>
        <span class="badge">${task.ticket_count || 0} incidents</span>
      </div>
      <div class="task-values">
        ${(task.allowed_values || task.labels || []).map((value) => `<span class="badge">${value}</span>`).join("")}
      </div>
    `;
    target.appendChild(article);
  });
}

async function initHome() {
  const [health, metadata] = await Promise.all([
    fetchJson("/health"),
    fetchJson("/metadata"),
  ]);

  setHealthPill(health.status);
  document.querySelector("[data-total-incidents]").textContent = safeText(metadata.total_tickets);
  document.querySelector("[data-task-count]").textContent = safeText(Object.keys(metadata.tasks).length);
  renderTaskCards(document.querySelector("[data-task-grid]"), metadata.tasks);
}

async function initStatus() {
  const [health, metadata, grader, schema] = await Promise.all([
    fetchJson("/health"),
    fetchJson("/metadata"),
    fetchJson("/grader"),
    fetchJson("/schema"),
  ]);

  document.querySelector("[data-health-text]").textContent = health.status;
  document.querySelector("[data-total-incidents]").textContent = safeText(metadata.total_tickets);
  document.querySelector("[data-schema-count]").textContent = safeText(Object.keys(schema).length);
  renderTaskCards(document.querySelector("[data-task-grid]"), metadata.tasks);

  const schemaGrid = document.querySelector("[data-schema-grid]");
  schemaGrid.innerHTML = Object.keys(schema)
    .map((name) => `<span class="badge">${name}</span>`)
    .join("");

  document.querySelector("[data-grader-summary]").textContent = grader.scoring;
  const graderList = document.querySelector("[data-grader-list]");
  graderList.innerHTML = Object.entries(grader.tasks)
    .map(([task, rule]) => `<li><strong>${task}</strong>: ${rule}</li>`)
    .join("");
}

function buildActionPayload(observation, selectedValue) {
  const payload = {
    incident_id: observation.incident_id,
    task_type: observation.task_type,
  };
  payload[observation.expected_field] = selectedValue;
  return payload;
}

async function initPlayground() {
  const resetForm = document.getElementById("reset-form");
  const stepForm = document.getElementById("step-form");
  const taskTypeInput = document.getElementById("task-type");
  const ticketIdInput = document.getElementById("ticket-id");
  const ticketOptions = document.getElementById("ticket-options");
  const ticketHelper = document.getElementById("ticket-helper");
  const expectedFieldInput = document.getElementById("expected-field");
  const actionValueSelect = document.getElementById("action-value");
  const stepButton = document.getElementById("step-button");
  const resetButton = document.getElementById("reset-button");
  const sessionIdTarget = document.getElementById("session-id");
  const observationOutput = document.getElementById("observation-output");
  const resultOutput = document.getElementById("result-output");
  const messageTarget = document.getElementById("playground-message");
  const summaryIncident = document.getElementById("summary-incident");
  const summaryField = document.getElementById("summary-field");
  const summaryReward = document.getElementById("summary-reward");
  const summaryStatus = document.getElementById("summary-status");

  let sessionId = null;
  let observation = null;
  let validTickets = [];

  const setOutput = (target, data) => {
    target.textContent = typeof data === "string" ? data : JSON.stringify(data, null, 2);
  };

  const setMessage = (message, mode = "neutral") => {
    messageTarget.textContent = message;
    messageTarget.dataset.mode = mode;
  };

  const setBusy = (button, isBusy, busyText, idleText) => {
    button.disabled = isBusy;
    button.textContent = isBusy ? busyText : idleText;
  };

  const updateSummaryFromObservation = (nextObservation) => {
    summaryIncident.textContent = nextObservation.incident_id;
    summaryField.textContent = nextObservation.expected_field;
    summaryReward.textContent = "--";
    summaryStatus.textContent = "Awaiting action";
  };

  const updateSummaryFromResult = (result) => {
    summaryReward.textContent = result.reward?.value ?? "--";
    summaryStatus.textContent = result.done ? "Completed" : "In progress";
  };

  const findTicket = (ticketId) => validTickets.find((ticket) => ticket.incident_id === ticketId);

  const syncTaskTypeFromTicket = () => {
    const ticket = findTicket(ticketIdInput.value.trim());
    if (!ticket) return;
    taskTypeInput.value = ticket.task_type;
    ticketHelper.textContent = `${ticket.incident_id} is a ${ticket.task_type} ${ticket.difficulty} ticket.`;
  };

  const chooseFirstTicketForTask = () => {
    if (!taskTypeInput.value) return;
    const ticket = validTickets.find((item) => item.task_type === taskTypeInput.value);
    if (ticket) {
      ticketIdInput.value = ticket.incident_id;
      ticketHelper.textContent = `${ticket.incident_id} selected for ${taskTypeInput.value}.`;
    }
  };

  try {
    const ticketData = await fetchJson("/tickets");
    validTickets = ticketData.tickets || [];
    ticketOptions.innerHTML = validTickets
      .map((ticket) => `<option value="${ticket.incident_id}" label="${ticket.task_type} / ${ticket.task_name}"></option>`)
      .join("");
    ticketHelper.textContent = `Valid ticket range: ${validTickets[0]?.incident_id || "--"} to ${validTickets.at(-1)?.incident_id || "--"}.`;
  } catch (error) {
    ticketHelper.textContent = `Could not load ticket list: ${error.message}`;
  }

  document.querySelectorAll("[data-preset-task]").forEach((button) => {
    button.addEventListener("click", () => {
      taskTypeInput.value = button.dataset.presetTask;
      ticketIdInput.value = button.dataset.presetTicket;
      setMessage(`Preset loaded: ${button.dataset.presetTask} / ${button.dataset.presetTicket}. Click Start / Reset Environment.`, "success");
    });
  });

  resetForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const formData = new FormData(resetForm);
    const payload = {};

    for (const [key, value] of formData.entries()) {
      if (value !== "") {
        payload[key] = key === "seed" ? Number(value) : value;
      }
    }

    const requestedTicket = payload.ticket_id;
    const knownTicket = requestedTicket ? findTicket(requestedTicket) : null;
    if (requestedTicket && validTickets.length > 0 && !knownTicket) {
      const message = `Ticket ${requestedTicket} does not exist. Use one of ${validTickets[0].incident_id} to ${validTickets.at(-1).incident_id}, or click a preset.`;
      setOutput(observationOutput, { error: message });
      setMessage(message, "error");
      return;
    }
    if (knownTicket && payload.task_type && payload.task_type !== knownTicket.task_type) {
      payload.task_type = knownTicket.task_type;
      taskTypeInput.value = knownTicket.task_type;
      ticketHelper.textContent = `Task type changed to ${knownTicket.task_type} because ${knownTicket.incident_id} belongs to that task.`;
    }

    try {
      setBusy(resetButton, true, "Starting...", "Start / Reset Environment");
      setMessage("Reset request sent. Watch the terminal for a [RESET] log.", "neutral");
      const result = await fetchJson("/reset", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      sessionId = result.info.session_id;
      observation = result.observation;

      sessionIdTarget.textContent = sessionId;
      expectedFieldInput.value = observation.expected_field;
      actionValueSelect.disabled = false;
      stepButton.disabled = false;
      actionValueSelect.innerHTML = observation.allowed_values
        .map((value) => `<option value="${value}">${value}</option>`)
        .join("");

      setOutput(observationOutput, result);
      setOutput(resultOutput, "No step submitted yet.");
      updateSummaryFromObservation(observation);
      setMessage(`Session ready for ${observation.incident_id}. Pick a value and submit the step.`, "success");
    } catch (error) {
      setOutput(observationOutput, { error: error.message });
      setMessage(error.message, "error");
    } finally {
      setBusy(resetButton, false, "Starting...", "Start / Reset Environment");
    }
  });

  stepForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!sessionId || !observation) {
      setOutput(resultOutput, { error: "Start a session first." });
      setMessage("Start a session before submitting a step.", "error");
      return;
    }

    try {
      setBusy(stepButton, true, "Submitting...", "Submit Step");
      setMessage("Step request sent. Watch the terminal for a [STEP] log.", "neutral");
      const result = await fetchJson(`/step?session_id=${encodeURIComponent(sessionId)}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(buildActionPayload(observation, actionValueSelect.value)),
      });
      setOutput(resultOutput, result);
      updateSummaryFromResult(result);
      const reward = result.reward?.value ?? "--";
      setMessage(`Step completed with reward ${reward}.`, reward === 1 ? "success" : "neutral");
    } catch (error) {
      setOutput(resultOutput, { error: error.message });
      setMessage(error.message, "error");
    } finally {
      if (observation) {
        setBusy(stepButton, false, "Submitting...", "Submit Step");
      }
    }
  });

  ticketIdInput.addEventListener("change", syncTaskTypeFromTicket);
  ticketIdInput.addEventListener("blur", syncTaskTypeFromTicket);
  taskTypeInput.addEventListener("change", chooseFirstTicketForTask);
}

async function bootstrap() {
  const page = document.body.dataset.page;
  try {
    if (page === "home") {
      await initHome();
    } else if (page === "status") {
      await initStatus();
    } else if (page === "playground") {
      await initPlayground();
    }
  } catch (error) {
    const pageShell = document.querySelector(".page-shell");
    const banner = document.createElement("div");
    banner.className = "floating-panel";
    banner.innerHTML = `<strong>UI data load failed.</strong><p class="status-helper">${error.message}</p>`;
    pageShell?.prepend(banner);
  }
}

window.addEventListener("DOMContentLoaded", bootstrap);
