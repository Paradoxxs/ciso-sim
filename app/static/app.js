const scenarioSelect = document.getElementById("scenario");
const briefingArticle = document.getElementById("briefing");
const form = document.getElementById("scenario-form");
const rosterContainer = document.getElementById("roster");
const stagePanel = document.getElementById("stage-panel");
const historyList = document.getElementById("history");
const teamStatsPanel = document.getElementById("team-stats");
const statusElements = {
  budget: document.getElementById("budget-value"),
  reputation: document.getElementById("reputation-value"),
  risk: document.getElementById("risk-value"),
};

let sessionId = null;

scenarioSelect?.addEventListener("change", () => {
  const option = scenarioSelect.selectedOptions[0];
  if (!option) {
    return;
  }
  briefingArticle.querySelector("p").textContent =
    option.dataset.briefing || "No briefing available.";
});

form?.addEventListener("submit", async (event) => {
  event.preventDefault();
  const data = new FormData(form);
  const scenarioId = data.get("scenario_id");
  const selectedIds = Array.from(
    document.querySelectorAll('input[name="member"]:checked')
  ).map((el) => el.value);
  if (teamBudget && currentTeamCost > teamBudget) {
    alert(`Team is over budget (${currentTeamCost}/${teamBudget}).`);
    return;
  }
  if (!scenarioId) return;
  form.querySelector("button").disabled = true;
  try {
    const team = selectedIds.map((id) => rosterData[id]).filter(Boolean);
    const response = await fetch("/api/session", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ scenario_id: scenarioId, team }),
    });
    if (!response.ok) throw new Error("Failed to start session");
    const payload = await response.json();
    sessionId = payload.session_id;
    historyList.innerHTML = "";
    updateStatus(payload.state);
    renderStage(payload.stage);
    setRosterDisabled(true);
  } catch (error) {
    console.error(error);
    alert("Unable to launch session. Check server logs.");
  } finally {
    form.querySelector("button").disabled = false;
  }
});

let rosterData = {};
let teamBudget = 0;
let currentTeamCost = 0;
const tabs = document.querySelectorAll(".tab-btn");
const tabPanels = document.querySelectorAll(".tab-panel");

async function loadRoster() {
  try {
    const response = await fetch("/api/roster");
    const data = await response.json();
    teamBudget = data.budget ?? 0;
    rosterData = Object.fromEntries(
      data.members.map((member) => [member.name, member])
    );
    renderRoster(data.members);
    updateTeamCostDisplay();
  } catch (error) {
    console.error("Failed to load roster", error);
  }
}

function renderRoster(list) {
  if (!rosterContainer) return;
  rosterContainer.innerHTML = list
    .map(
      (member) => `
        <label class="member-card">
          <input type="checkbox" name="member" value="${member.name}" />
          <div>
            <strong>${member.name}</strong>
            <p>${member.role}</p>
            <small>Cost:${member.cost} | A:${member.stats.analysis} C:${member.stats.comms} E:${member.stats.engineering} L:${member.stats.leadership}</small>
          </div>
        </label>
      `
    )
    .join("");

  rosterContainer.querySelectorAll('input[name="member"]').forEach((checkbox) => {
    checkbox.addEventListener("change", updateTeamCostDisplay);
  });
}

function updateTeamCostDisplay() {
  const selectedIds = Array.from(
    document.querySelectorAll('input[name="member"]:checked')
  ).map((el) => el.value);
  currentTeamCost = selectedIds.reduce((acc, id) => {
    const member = rosterData[id];
    return acc + (member?.cost || 0);
  }, 0);

  const totalEl = document.getElementById("team-total");
  const budgetEl = document.getElementById("team-budget");
  if (totalEl) totalEl.textContent = currentTeamCost;
  if (budgetEl) budgetEl.textContent = teamBudget;

  const overBudget = teamBudget && currentTeamCost > teamBudget;
  const submitBtn = form?.querySelector("button");
  if (submitBtn) submitBtn.disabled = overBudget;
}

function setRosterDisabled(disabled) {
  rosterContainer
    ?.querySelectorAll('input[name="member"]')
    .forEach((el) => (el.disabled = disabled));
}

tabs.forEach((btn) => {
  btn.addEventListener("click", () => activateTab(btn.dataset.tab));
});

function activateTab(tabId) {
  tabs.forEach((btn) => btn.classList.toggle("active", btn.dataset.tab === tabId));
  tabPanels.forEach((panel) =>
    panel.classList.toggle("active", panel.id === tabId)
  );
}

loadRoster();

async function chooseOption(optionId) {
  if (!sessionId) return;
  toggleOptions(true);
  try {
    const response = await fetch(`/api/session/${sessionId}/decision`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ option_id: optionId }),
    });
    if (!response.ok) throw new Error("Decision failed");
    const result = await response.json();
    updateStatus(result.state);
    appendHistory(result);
    if (result.finished) {
      stagePanel.innerHTML = `<p class="placeholder">Simulation complete. Start a new session to replay.</p>`;
      sessionId = null;
      setRosterDisabled(false);
    } else {
      renderStage(result.stage);
    }
  } catch (error) {
    console.error(error);
    alert("Error applying decision.");
  } finally {
    toggleOptions(false);
  }
}

function renderStage(stage) {
  if (!stage) {
    stagePanel.innerHTML = `<p class="placeholder">No stage available.</p>`;
    return;
  }
  const challenges = stage.challenges
    .map(
      (challenge) => `
        <article class="challenge">
          <h3>${challenge.title}</h3>
          <p>${challenge.prompt}</p>
          <div class="options">
            ${challenge.options
              .map(
                (option) => `
              <button class="option-card" data-option="${option.id}">
                <strong>${option.label}</strong>
                <p>${option.narrative}</p>
                <div class="option-meta">Skill: ${option.skill || "analysis"} • Difficulty: ${option.difficulty ?? 50} • Prob: ${option.probability ?? "?"}%</div>
              </button>
            `
              )
              .join("")}
          </div>
        </article>
      `
    )
    .join("");

  stagePanel.innerHTML = `
    <header>
      <div style="display:flex;align-items:center;gap:0.5rem;">
        <h2>${stage.title}</h2>
        ${stage.is_injection ? `<span class="badge">Injection</span>` : ""}
      </div>
      <p>${stage.summary}</p>
    </header>
    ${challenges}
  `;

  stagePanel.querySelectorAll(".option-card").forEach((button) => {
    button.addEventListener("click", () => chooseOption(button.dataset.option));
  });
}

function updateStatus(state) {
  statusElements.budget.textContent = state.budget;
  statusElements.reputation.textContent = state.reputation;
  statusElements.risk.textContent = state.risk;
  updateTeamStats(state.team_totals || {});
}

function appendHistory(result) {
  const li = document.createElement("li");
  const last = result.state.history[result.state.history.length - 1];
  li.textContent = `${last.stage.toUpperCase()} » ${last.option} → ${last.outcome}`;
  historyList.prepend(li);
}

function toggleOptions(disabled) {
  stagePanel.querySelectorAll(".option-card").forEach((button) => {
    button.disabled = disabled;
  });
}

function updateTeamStats(totals) {
  if (!teamStatsPanel) return;
  const rows = ["analysis", "comms", "engineering", "leadership"].map(
    (key) => `
      <div class="stat-row">
        <span class="stat-label">${key}</span>
        <span class="stat-value">${totals[key] ?? 0}</span>
      </div>
    `
  );
  teamStatsPanel.innerHTML = rows.join("");
}

