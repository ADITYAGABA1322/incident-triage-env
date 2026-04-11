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

function createBadge(text, extraClass = "") {
  const badge = document.createElement("span");
  badge.className = extraClass ? `badge ${extraClass}` : "badge";
  badge.textContent = safeText(text);
  return badge;
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
  target.replaceChildren();
  Object.entries(tasks).forEach(([taskId, task]) => {
    const article = document.createElement("article");
    article.className = "task-card";

    const difficultyClass = `difficulty-${safeText(task.difficulty).toLowerCase().replace(/[^a-z0-9_-]/g, "")}`;
    const difficulty = createBadge(task.difficulty, difficultyClass);
    const title = document.createElement("h3");
    title.textContent = safeText(task.name);

    const content = document.createElement("div");
    content.className = "task-card-content";

    const expectedField = document.createElement("p");
    expectedField.append("Expected field: ");
    const expectedFieldValue = document.createElement("strong");
    expectedFieldValue.textContent = safeText(task.expected_field || task.output_field);
    expectedField.appendChild(expectedFieldValue);
    content.append(title, expectedField);

    const taskMeta = document.createElement("div");
    taskMeta.className = "task-meta";
    taskMeta.append(
      createBadge(taskId),
      createBadge(`${task.ticket_count || 0} incidents`),
    );

    const taskValues = document.createElement("div");
    taskValues.className = "task-values";
    (task.allowed_values || task.labels || []).forEach((value) => {
      taskValues.appendChild(createBadge(value));
    });

    article.append(difficulty, content, taskMeta, taskValues);
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
  schemaGrid.replaceChildren();
  Object.keys(schema).forEach((name) => {
    schemaGrid.appendChild(createBadge(name));
  });

  document.querySelector("[data-grader-summary]").textContent = grader.scoring;
  const graderList = document.querySelector("[data-grader-list]");
  graderList.replaceChildren();
  Object.entries(grader.tasks).forEach(([task, rule]) => {
    const item = document.createElement("li");
    const taskName = document.createElement("strong");
    taskName.textContent = task;
    item.append(taskName, `: ${safeText(rule)}`);
    graderList.appendChild(item);
  });
}

function buildActionPayload(observation, selectedValue) {
  const payload = {
    incident_id: observation.incident_id,
    task_type: observation.task_type,
  };
  payload[observation.expected_field] = selectedValue;
  return payload;
}

function createEndpointCard(endpoint) {
  const card = document.createElement("article");
  card.className = "endpoint-card";

  const header = document.createElement("div");
  header.className = "endpoint-card-header";
  header.append(createBadge(endpoint.method, `method-${endpoint.method.toLowerCase()}`));

  const path = document.createElement("code");
  path.textContent = endpoint.path;
  header.appendChild(path);

  const title = document.createElement("h3");
  title.textContent = endpoint.title;

  const description = document.createElement("p");
  description.textContent = endpoint.description;

  const meta = document.createElement("div");
  meta.className = "endpoint-meta";
  endpoint.notes.forEach((note) => {
    meta.appendChild(createBadge(note));
  });

  const link = document.createElement("a");
  link.className = "button button-secondary endpoint-link";
  link.href = endpoint.href;
  link.textContent = endpoint.linkText;

  card.append(header, title, description, meta, link);
  return card;
}

async function initApi() {
  const [health, metadata, grader, schema] = await Promise.all([
    fetchJson("/health"),
    fetchJson("/metadata"),
    fetchJson("/grader"),
    fetchJson("/schema"),
  ]);

  document.querySelector("[data-api-health]").textContent = health.status === "healthy" ? "Healthy" : "Unavailable";
  document.querySelector("[data-api-summary]").textContent =
    `${safeText(metadata.total_tickets)} incidents across ${Object.keys(metadata.tasks || {}).length} task families.`;

  const endpoints = [
    {
      method: "GET",
      path: "/health",
      title: "Health check",
      description: "Fast validator ping. Must return a healthy status.",
      notes: ["validator", "no body"],
      href: "/health",
      linkText: "Open raw health",
    },
    {
      method: "GET",
      path: "/metadata",
      title: "Environment metadata",
      description: "Shows name, task inventory, labels, and dataset count.",
      notes: ["task inventory", "reviewer-friendly"],
      href: "/metadata",
      linkText: "Open raw metadata",
    },
    {
      method: "GET",
      path: "/schema",
      title: "Typed contract schemas",
      description: "Exposes action, observation, reward, state, and step result models.",
      notes: ["typed models", "OpenEnv spec"],
      href: "/schema",
      linkText: "Open raw schema",
    },
    {
      method: "POST",
      path: "/reset",
      title: "Start an episode",
      description: "Creates a session and returns the first observation. No grading happens yet.",
      notes: ["returns session_id", "body optional"],
      href: "/playground",
      linkText: "Try in playground",
    },
    {
      method: "POST",
      path: "/step?session_id=...",
      title: "Submit an answer",
      description: "Grades exactly one action and returns reward, done, correctness, and state.",
      notes: ["reward 0-1", "single step"],
      href: "/playground",
      linkText: "Try in playground",
    },
    {
      method: "GET",
      path: "/state?session_id=...",
      title: "Read episode state",
      description: "Reads active or completed episode state for a known session id.",
      notes: ["typed state", "debugging"],
      href: "/playground",
      linkText: "Create session first",
    },
    {
      method: "GET",
      path: "/docs",
      title: "Generated FastAPI docs",
      description: "Full OpenAPI interface generated from the running backend.",
      notes: ["developer docs", "OpenAPI"],
      href: "/docs",
      linkText: "Open FastAPI docs",
    },
    {
      method: "GET",
      path: "/openapi.json",
      title: "Machine-readable contract",
      description: "Raw OpenAPI document used by tools and automated inspectors.",
      notes: ["JSON", "tooling"],
      href: "/openapi.json",
      linkText: "Open raw OpenAPI",
    },
  ];

  const endpointGrid = document.querySelector("[data-endpoint-grid]");
  endpointGrid.replaceChildren();
  endpoints.forEach((endpoint) => {
    endpointGrid.appendChild(createEndpointCard(endpoint));
  });

  const schemaGrid = document.querySelector("[data-api-schema-grid]");
  schemaGrid.replaceChildren();
  Object.keys(schema).forEach((name) => {
    schemaGrid.appendChild(createBadge(name));
  });

  const graderList = document.querySelector("[data-api-grader-list]");
  graderList.replaceChildren();
  Object.entries(grader.tasks || {}).forEach(([task, rule]) => {
    const item = document.createElement("li");
    const taskName = document.createElement("strong");
    taskName.textContent = task;
    item.append(taskName, `: ${safeText(rule)}`);
    graderList.appendChild(item);
  });
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
    ticketOptions.replaceChildren();
    validTickets.forEach((ticket) => {
      const option = document.createElement("option");
      option.value = safeText(ticket.incident_id);
      option.label = `${safeText(ticket.task_type)} / ${safeText(ticket.task_name)}`;
      ticketOptions.appendChild(option);
    });
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
      actionValueSelect.replaceChildren();
      observation.allowed_values.forEach((value) => {
        const option = document.createElement("option");
        option.value = safeText(value);
        option.textContent = safeText(value);
        actionValueSelect.appendChild(option);
      });

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
    } else if (page === "api") {
      await initApi();
    }
  } catch (error) {
    const pageShell = document.querySelector(".page-shell");
    const banner = document.createElement("div");
    banner.className = "floating-panel";
    const title = document.createElement("strong");
    title.textContent = "UI data load failed.";
    const detail = document.createElement("p");
    detail.className = "status-helper";
    detail.textContent = error.message;
    banner.append(title, detail);
    pageShell?.prepend(banner);
  }
}

window.addEventListener("DOMContentLoaded", bootstrap);
