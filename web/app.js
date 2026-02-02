/**
 * Bot Management Dashboard
 * 
 * Full CRUD for bots, guidelines, and journeys with chat functionality.
 * Connects to the Bot Management API (port 8801).
 */

// =============================================================================
// Configuration
// =============================================================================

const API_BASE_URL = "http://localhost:8801";
const ENDPOINTS = {
  // Bots
  listBots: "/bots",
  createBot: "/bots",
  getBot: (id) => `/bots/${id}`,
  updateBot: (id) => `/bots/${id}`,
  deleteBot: (id) => `/bots/${id}`,
  // Guidelines
  listGuidelines: "/guidelines",
  createGuideline: "/guidelines",
  getGuideline: (id) => `/guidelines/${id}`,
  updateGuideline: (id) => `/guidelines/${id}`,
  deleteGuideline: (id) => `/guidelines/${id}`,
  addGuidelineToBot: (botId) => `/bots/${botId}/guidelines`,
  // Journeys
  listJourneys: "/journeys",
  createJourney: "/journeys",
  getJourney: (id) => `/journeys/${id}`,
  updateJourney: (id) => `/journeys/${id}`,
  deleteJourney: (id) => `/journeys/${id}`,
  addJourneyToBot: (botId) => `/bots/${botId}/journeys`,
  // Chat
  createSession: (botId) => `/bots/${botId}/sessions`,
  sendMessage: (sessionId) => `/sessions/${sessionId}/messages`,
  getMessages: (sessionId) => `/sessions/${sessionId}/messages`,
};

// =============================================================================
// DOM Elements
// =============================================================================

const botGrid = document.getElementById("botGrid");
const refreshButton = document.getElementById("refreshButton");
const botModal = document.getElementById("botModal");
const modalOverlay = document.getElementById("modalOverlay");
const closeModalButton = document.getElementById("closeModalButton");
const cancelModalButton = document.getElementById("cancelModalButton");
const botForm = document.getElementById("botForm");
const formStatus = document.getElementById("formStatus");
const submitBotButton = document.getElementById("submitBotButton");

// Form step elements
const stepBasic = document.getElementById("stepBasic");
const stepGuidelines = document.getElementById("stepGuidelines");
const stepJourneys = document.getElementById("stepJourneys");
const prevStepButton = document.getElementById("prevStepButton");
const nextStepButton = document.getElementById("nextStepButton");

// Chat modal elements
const chatModal = document.getElementById("chatModal");
const chatModalOverlay = document.getElementById("chatModalOverlay");
const closeChatButton = document.getElementById("closeChatButton");
const chatMessages = document.getElementById("chatMessages");
const chatInput = document.getElementById("chatInput");
const sendMessageButton = document.getElementById("sendMessageButton");
const chatBotName = document.getElementById("chatBotName");
const chatSessionId = document.getElementById("chatSessionId");

// Bot detail modal elements
const detailModal = document.getElementById("detailModal");
const detailModalOverlay = document.getElementById("detailModalOverlay");
const closeDetailButton = document.getElementById("closeDetailButton");

// =============================================================================
// State Management
// =============================================================================

const formState = {
  currentStep: 1,
  totalSteps: 3,
  data: {
    name: "",
    purpose: "",
    scope: "",
    target_users: "",
    use_cases: [],
    tone: "",
    personality: "",
    tools: ["none"],
    constraints: [],
    guardrails: [],
    guidelines: [],
    journeys: [],
    composition_mode: "FLUID",
    max_engine_iterations: 3,
  },
};

// Chat state
const chatState = {
  botId: null,
  botName: null,
  sessionId: null,
  polling: null,
  lastMessageCount: 0,
  isWaitingForResponse: false,
};

// Detail view state
const detailState = {
  botId: null,
  botName: null,
  bot: null,
};

// =============================================================================
// Utility Functions
// =============================================================================

function setStatus(message, isError = true) {
  formStatus.textContent = message;
  formStatus.style.color = isError ? "#ef4444" : "#16a34a";
}

function formatDate(value) {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  return date.toLocaleDateString("en-US", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

function normalizeBotList(payload) {
  if (Array.isArray(payload)) return payload;
  if (Array.isArray(payload?.bots)) return payload.bots;
  if (Array.isArray(payload?.items)) return payload.items;
  return [];
}

function resolveStatus(bot) {
  const status = bot?.status?.toUpperCase?.() || "CREATED";
  if (status === "PARTIALLY_CREATED") return "unpublished";
  if (status === "FAILED") return "failed";
  return "published";
}

function showToast(message, isError = false) {
  const toast = document.createElement("div");
  toast.className = `toast ${isError ? "error" : "success"}`;
  toast.textContent = message;
  document.body.appendChild(toast);
  
  setTimeout(() => toast.classList.add("show"), 10);
  setTimeout(() => {
    toast.classList.remove("show");
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}

// =============================================================================
// Modal Management
// =============================================================================

function openModal() {
  botModal.classList.remove("hidden");
  document.body.style.overflow = "hidden";
  resetForm();
  showStep(1);
}

function closeModal() {
  botModal.classList.add("hidden");
  document.body.style.overflow = "";
  resetForm();
}

function resetForm() {
  botForm.reset();
  formState.currentStep = 1;
  formState.data = {
    name: "",
    purpose: "",
    scope: "",
    target_users: "",
    use_cases: [],
    tone: "",
    personality: "",
    tools: ["none"],
    constraints: [],
    guardrails: [],
    guidelines: [],
    journeys: [],
    composition_mode: "FLUID",
    max_engine_iterations: 3,
  };
  setStatus("");
  
  document.getElementById("guidelinesList").innerHTML = "";
  document.getElementById("journeysList").innerHTML = "";
  addGuideline();
  addJourney();
}

// =============================================================================
// Multi-Step Form Navigation
// =============================================================================

function showStep(step) {
  formState.currentStep = step;
  
  stepBasic?.classList.add("hidden");
  stepGuidelines?.classList.add("hidden");
  stepJourneys?.classList.add("hidden");
  
  if (step === 1) stepBasic?.classList.remove("hidden");
  if (step === 2) stepGuidelines?.classList.remove("hidden");
  if (step === 3) stepJourneys?.classList.remove("hidden");
  
  prevStepButton.style.display = step === 1 ? "none" : "inline-flex";
  nextStepButton.style.display = step === 3 ? "none" : "inline-flex";
  submitBotButton.style.display = step === 3 ? "inline-flex" : "none";
  
  document.querySelectorAll(".step-indicator").forEach((el, idx) => {
    el.classList.toggle("active", idx + 1 === step);
    el.classList.toggle("completed", idx + 1 < step);
  });
}

function nextStep() {
  if (formState.currentStep < formState.totalSteps) {
    if (!validateCurrentStep()) return;
    collectCurrentStepData();
    showStep(formState.currentStep + 1);
  }
}

function prevStep() {
  if (formState.currentStep > 1) {
    collectCurrentStepData();
    showStep(formState.currentStep - 1);
  }
}

function validateCurrentStep() {
  const step = formState.currentStep;
  
  if (step === 1) {
    const name = document.getElementById("botName")?.value?.trim();
    const purpose = document.getElementById("botPurpose")?.value?.trim();
    const scope = document.getElementById("botScope")?.value?.trim();
    const targetUsers = document.getElementById("botTargetUsers")?.value?.trim();
    const useCases = document.getElementById("botUseCases")?.value?.trim();
    const tone = document.getElementById("botTone")?.value?.trim();
    const personality = document.getElementById("botPersonality")?.value?.trim();
    const constraints = document.getElementById("botConstraints")?.value?.trim();
    const guardrails = document.getElementById("botGuardrails")?.value?.trim();
    
    if (!name || !purpose || !scope || !targetUsers || !useCases || !tone || !personality || !constraints || !guardrails) {
      setStatus("Please fill in all required fields.");
      return false;
    }
  }
  
  if (step === 2) {
    const guidelines = document.querySelectorAll(".guideline-item");
    if (guidelines.length === 0) {
      setStatus("Add at least one guideline.");
      return false;
    }
    for (const item of guidelines) {
      const condition = item.querySelector(".guideline-condition")?.value?.trim();
      if (!condition) {
        setStatus("Each guideline must have a condition.");
        return false;
      }
    }
  }
  
  if (step === 3) {
    const journeys = document.querySelectorAll(".journey-item");
    if (journeys.length === 0) {
      setStatus("Add at least one journey.");
      return false;
    }
    for (const item of journeys) {
      const title = item.querySelector(".journey-title")?.value?.trim();
      const description = item.querySelector(".journey-description")?.value?.trim();
      const conditions = item.querySelector(".journey-conditions")?.value?.trim();
      if (!title || !description || !conditions) {
        setStatus("Each journey must have a title, description, and conditions.");
        return false;
      }
    }
  }
  
  setStatus("");
  return true;
}

function collectCurrentStepData() {
  const step = formState.currentStep;
  
  if (step === 1) {
    formState.data.name = document.getElementById("botName")?.value?.trim() || "";
    formState.data.purpose = document.getElementById("botPurpose")?.value?.trim() || "";
    formState.data.scope = document.getElementById("botScope")?.value?.trim() || "";
    formState.data.target_users = document.getElementById("botTargetUsers")?.value?.trim() || "";
    formState.data.use_cases = (document.getElementById("botUseCases")?.value || "")
      .split("\n").map((s) => s.trim()).filter(Boolean);
    formState.data.tone = document.getElementById("botTone")?.value?.trim() || "";
    formState.data.personality = document.getElementById("botPersonality")?.value?.trim() || "";
    formState.data.tools = (document.getElementById("botTools")?.value || "none")
      .split(",").map((s) => s.trim()).filter(Boolean);
    formState.data.constraints = (document.getElementById("botConstraints")?.value || "")
      .split("\n").map((s) => s.trim()).filter(Boolean);
    formState.data.guardrails = (document.getElementById("botGuardrails")?.value || "")
      .split("\n").map((s) => s.trim()).filter(Boolean);
  }
  
  if (step === 2) {
    formState.data.guidelines = [];
    document.querySelectorAll(".guideline-item").forEach((item) => {
      const condition = item.querySelector(".guideline-condition")?.value?.trim();
      const action = item.querySelector(".guideline-action")?.value?.trim();
      const criticality = item.querySelector(".guideline-criticality")?.value || "MEDIUM";
      if (condition) {
        formState.data.guidelines.push({ condition, action, criticality });
      }
    });
  }
  
  if (step === 3) {
    formState.data.journeys = [];
    document.querySelectorAll(".journey-item").forEach((item) => {
      const title = item.querySelector(".journey-title")?.value?.trim();
      const description = item.querySelector(".journey-description")?.value?.trim();
      const conditionsText = item.querySelector(".journey-conditions")?.value || "";
      const conditions = conditionsText.split("\n").map((s) => s.trim()).filter(Boolean);
      if (title && description && conditions.length > 0) {
        formState.data.journeys.push({ title, description, conditions });
      }
    });
  }
}

// =============================================================================
// Dynamic Form Elements
// =============================================================================

function addGuideline() {
  const container = document.getElementById("guidelinesList");
  const index = container.children.length + 1;
  
  const item = document.createElement("div");
  item.className = "guideline-item";
  item.innerHTML = `
    <div class="item-header">
      <span class="item-number">Guideline ${index}</span>
      <button type="button" class="remove-item" onclick="this.closest('.guideline-item').remove()">✕</button>
    </div>
    <label class="field">
      <span class="field-label">Condition *</span>
      <input class="field-input guideline-condition" placeholder="When this happens..." required />
    </label>
    <label class="field">
      <span class="field-label">Action</span>
      <input class="field-input guideline-action" placeholder="Do this..." />
    </label>
    <label class="field">
      <span class="field-label">Criticality</span>
      <select class="field-input guideline-criticality">
        <option value="LOW">Low</option>
        <option value="MEDIUM" selected>Medium</option>
        <option value="HIGH">High</option>
      </select>
    </label>
  `;
  container.appendChild(item);
}

function addJourney() {
  const container = document.getElementById("journeysList");
  const index = container.children.length + 1;
  
  const item = document.createElement("div");
  item.className = "journey-item";
  item.innerHTML = `
    <div class="item-header">
      <span class="item-number">Journey ${index}</span>
      <button type="button" class="remove-item" onclick="this.closest('.journey-item').remove()">✕</button>
    </div>
    <label class="field">
      <span class="field-label">Title *</span>
      <input class="field-input journey-title" placeholder="Journey name" required />
    </label>
    <label class="field">
      <span class="field-label">Description *</span>
      <textarea class="field-input journey-description" placeholder="What this journey does..." rows="2" required></textarea>
    </label>
    <label class="field">
      <span class="field-label">Conditions * (one per line)</span>
      <textarea class="field-input journey-conditions" placeholder="When to trigger this journey..." rows="2" required></textarea>
    </label>
  `;
  container.appendChild(item);
}

window.addGuideline = addGuideline;
window.addJourney = addJourney;

// =============================================================================
// Bot Cards
// =============================================================================

function renderCreateCard() {
  const card = document.createElement("div");
  card.className = "card create-card";
  card.innerHTML = `
    <div class="create-icon">+</div>
    <div class="card-title">Create</div>
  `;
  card.addEventListener("click", openModal);
  return card;
}

function renderBotCard(bot) {
  const card = document.createElement("div");
  card.className = "card bot-card";
  
  const status = resolveStatus(bot);
  const statusText = status === "published" ? "Created" : 
                     status === "unpublished" ? "Partially Created" : "Failed";
  const statusClass = status === "published" ? "" : "unpublished";
  const createdDate = formatDate(bot.created_at);
  
  card.innerHTML = `
    <div class="card-header">
      <div class="card-title">${bot.name || "Untitled bot"}</div>
      <div class="card-actions">
        <button class="icon-btn edit-btn" title="Edit bot" data-bot-id="${bot.id}">✏️</button>
        <button class="icon-btn delete-btn" title="Delete bot" data-bot-id="${bot.id}">🗑️</button>
      </div>
    </div>
    <div class="card-meta">${bot.guidelines?.length || 0} Guidelines • ${bot.journeys?.length || 0} Journeys</div>
    <div class="status-row">Status</div>
    <div class="status-value ${statusClass}">
      <span class="status-dot"></span>
      ${statusText}
    </div>
    <div class="card-footer">
      <span>Created ${createdDate}</span>
      <button class="chat-btn" data-bot-id="${bot.id}">💬 Chat</button>
    </div>
  `;
  
  // Edit button opens detail view
  card.querySelector(".edit-btn").addEventListener("click", (e) => {
    e.stopPropagation();
    openDetailView(bot);
  });
  
  // Delete button
  card.querySelector(".delete-btn").addEventListener("click", async (e) => {
    e.stopPropagation();
    if (confirm(`Delete "${bot.name}"? This cannot be undone.`)) {
      await deleteBot(bot.id);
    }
  });
  
  // Chat button
  card.querySelector(".chat-btn").addEventListener("click", (e) => {
    e.stopPropagation();
    openChat(bot);
  });
  
  // Card click opens detail view
  card.addEventListener("click", (e) => {
    if (e.target.closest(".card-actions") || e.target.closest(".chat-btn")) return;
    openDetailView(bot);
  });
  
  return card;
}

function renderSkeletons(count = 5) {
  botGrid.innerHTML = "";
  botGrid.appendChild(renderCreateCard());
  for (let i = 0; i < count; i++) {
    const card = document.createElement("div");
    card.className = "card";
    card.innerHTML = `
      <div class="skeleton" style="width: 60%; height: 18px;"></div>
      <div class="skeleton" style="width: 40%; margin-top: 12px;"></div>
      <div class="skeleton" style="width: 80%; margin-top: 20px;"></div>
      <div class="skeleton" style="width: 70%; margin-top: 10px;"></div>
    `;
    botGrid.appendChild(card);
  }
}

function renderBots(bots) {
  botGrid.innerHTML = "";
  botGrid.appendChild(renderCreateCard());
  bots.forEach((bot) => {
    botGrid.appendChild(renderBotCard(bot));
  });
}

function renderError(message) {
  botGrid.innerHTML = "";
  botGrid.appendChild(renderCreateCard());
  const errorCard = document.createElement("div");
  errorCard.className = "card";
  errorCard.innerHTML = `
    <div class="card-title">Unable to load bots</div>
    <div class="card-meta">${message}</div>
    <div class="card-meta" style="margin-top: 8px;">Make sure the API server is running on port 8801</div>
  `;
  botGrid.appendChild(errorCard);
}

// =============================================================================
// Bot Detail View
// =============================================================================

function openDetailView(bot) {
  detailState.botId = bot.id;
  detailState.botName = bot.name;
  detailState.bot = bot;
  
  renderDetailView(bot);
  detailModal.classList.remove("hidden");
  document.body.style.overflow = "hidden";
}

function closeDetailView() {
  detailModal.classList.add("hidden");
  document.body.style.overflow = "";
  detailState.botId = null;
  detailState.botName = null;
  detailState.bot = null;
}

function renderDetailView(bot) {
  const detailContent = document.getElementById("detailContent");
  
  const guidelinesHtml = (bot.guidelines || []).map((g, idx) => `
    <div class="detail-item" data-guideline-id="${g.id}">
      <div class="detail-item-header">
        <span class="detail-item-title">Guideline ${idx + 1}</span>
        <span class="criticality-badge ${(g.criticality || 'medium').toLowerCase()}">${g.criticality || 'medium'}</span>
        <div class="detail-item-actions">
          <button class="icon-btn" onclick="editGuideline('${g.id}')" title="Edit">✏️</button>
          <button class="icon-btn" onclick="deleteGuidelineItem('${g.id}')" title="Delete">🗑️</button>
        </div>
      </div>
      <div class="detail-item-content">
        <div class="detail-field">
          <label>Condition:</label>
          <span>${g.condition || '—'}</span>
        </div>
        <div class="detail-field">
          <label>Action:</label>
          <span>${g.action || '—'}</span>
        </div>
      </div>
    </div>
  `).join("") || '<div class="empty-state">No guidelines yet</div>';
  
  const journeysHtml = (bot.journeys || []).map((j, idx) => `
    <div class="detail-item" data-journey-id="${j.id}">
      <div class="detail-item-header">
        <span class="detail-item-title">${j.title || `Journey ${idx + 1}`}</span>
        <div class="detail-item-actions">
          <button class="icon-btn" onclick="editJourney('${j.id}')" title="Edit">✏️</button>
          <button class="icon-btn" onclick="deleteJourneyItem('${j.id}')" title="Delete">🗑️</button>
        </div>
      </div>
      <div class="detail-item-content">
        <div class="detail-field">
          <label>Description:</label>
          <span>${j.description || '—'}</span>
        </div>
        <div class="detail-field">
          <label>Conditions:</label>
          <span>${(j.conditions || []).join('; ') || '—'}</span>
        </div>
      </div>
    </div>
  `).join("") || '<div class="empty-state">No journeys yet</div>';
  
  detailContent.innerHTML = `
    <div class="detail-header">
      <h2>${bot.name || 'Untitled Bot'}</h2>
      <p class="detail-description">${bot.description || ''}</p>
    </div>
    
    <div class="detail-section">
      <div class="section-header">
        <h3>Guidelines</h3>
        <button class="btn primary small" onclick="openAddGuidelineForm()">+ Add Guideline</button>
      </div>
      <div class="detail-items" id="guidelinesContainer">
        ${guidelinesHtml}
      </div>
    </div>
    
    <div class="detail-section">
      <div class="section-header">
        <h3>Journeys</h3>
        <button class="btn primary small" onclick="openAddJourneyForm()">+ Add Journey</button>
      </div>
      <div class="detail-items" id="journeysContainer">
        ${journeysHtml}
      </div>
    </div>
    
    <!-- Inline Forms (hidden by default) -->
    <div id="addGuidelineForm" class="inline-form hidden">
      <h4>Add Guideline</h4>
      <label class="field">
        <span class="field-label">Condition *</span>
        <input class="field-input" id="newGuidelineCondition" placeholder="When this happens..." />
      </label>
      <label class="field">
        <span class="field-label">Action</span>
        <input class="field-input" id="newGuidelineAction" placeholder="Do this..." />
      </label>
      <label class="field">
        <span class="field-label">Criticality</span>
        <select class="field-input" id="newGuidelineCriticality">
          <option value="low">Low</option>
          <option value="medium" selected>Medium</option>
          <option value="high">High</option>
        </select>
      </label>
      <div class="form-actions">
        <button class="btn ghost" onclick="closeAddGuidelineForm()">Cancel</button>
        <button class="btn primary" onclick="saveNewGuideline()">Save</button>
      </div>
    </div>
    
    <div id="addJourneyForm" class="inline-form hidden">
      <h4>Add Journey</h4>
      <label class="field">
        <span class="field-label">Title *</span>
        <input class="field-input" id="newJourneyTitle" placeholder="Journey name" />
      </label>
      <label class="field">
        <span class="field-label">Description *</span>
        <textarea class="field-input" id="newJourneyDescription" placeholder="What this journey does..." rows="2"></textarea>
      </label>
      <label class="field">
        <span class="field-label">Conditions * (one per line)</span>
        <textarea class="field-input" id="newJourneyConditions" placeholder="When to trigger..." rows="2"></textarea>
      </label>
      <div class="form-actions">
        <button class="btn ghost" onclick="closeAddJourneyForm()">Cancel</button>
        <button class="btn primary" onclick="saveNewJourney()">Save</button>
      </div>
    </div>
    
    <div id="editGuidelineForm" class="inline-form hidden">
      <h4>Edit Guideline</h4>
      <input type="hidden" id="editGuidelineId" />
      <label class="field">
        <span class="field-label">Condition *</span>
        <input class="field-input" id="editGuidelineCondition" placeholder="When this happens..." />
      </label>
      <label class="field">
        <span class="field-label">Action</span>
        <input class="field-input" id="editGuidelineAction" placeholder="Do this..." />
      </label>
      <label class="field">
        <span class="field-label">Criticality</span>
        <select class="field-input" id="editGuidelineCriticality">
          <option value="low">Low</option>
          <option value="medium">Medium</option>
          <option value="high">High</option>
        </select>
      </label>
      <div class="form-actions">
        <button class="btn ghost" onclick="closeEditGuidelineForm()">Cancel</button>
        <button class="btn primary" onclick="saveEditedGuideline()">Update</button>
      </div>
    </div>
    
    <div id="editJourneyForm" class="inline-form hidden">
      <h4>Edit Journey</h4>
      <input type="hidden" id="editJourneyId" />
      <label class="field">
        <span class="field-label">Title *</span>
        <input class="field-input" id="editJourneyTitle" placeholder="Journey name" />
      </label>
      <label class="field">
        <span class="field-label">Description *</span>
        <textarea class="field-input" id="editJourneyDescription" placeholder="What this journey does..." rows="2"></textarea>
      </label>
      <label class="field">
        <span class="field-label">Conditions * (one per line)</span>
        <textarea class="field-input" id="editJourneyConditions" placeholder="When to trigger..." rows="2"></textarea>
      </label>
      <div class="form-actions">
        <button class="btn ghost" onclick="closeEditJourneyForm()">Cancel</button>
        <button class="btn primary" onclick="saveEditedJourney()">Update</button>
      </div>
    </div>
  `;
}

// Inline form handlers
function openAddGuidelineForm() {
  document.getElementById("addGuidelineForm").classList.remove("hidden");
  document.getElementById("newGuidelineCondition").focus();
}

function closeAddGuidelineForm() {
  document.getElementById("addGuidelineForm").classList.add("hidden");
  document.getElementById("newGuidelineCondition").value = "";
  document.getElementById("newGuidelineAction").value = "";
  document.getElementById("newGuidelineCriticality").value = "medium";
}

function openAddJourneyForm() {
  document.getElementById("addJourneyForm").classList.remove("hidden");
  document.getElementById("newJourneyTitle").focus();
}

function closeAddJourneyForm() {
  document.getElementById("addJourneyForm").classList.add("hidden");
  document.getElementById("newJourneyTitle").value = "";
  document.getElementById("newJourneyDescription").value = "";
  document.getElementById("newJourneyConditions").value = "";
}

async function editGuideline(guidelineId) {
  const guideline = detailState.bot?.guidelines?.find(g => g.id === guidelineId);
  if (!guideline) return;
  
  document.getElementById("editGuidelineId").value = guidelineId;
  document.getElementById("editGuidelineCondition").value = guideline.condition || "";
  document.getElementById("editGuidelineAction").value = guideline.action || "";
  document.getElementById("editGuidelineCriticality").value = (guideline.criticality || "medium").toLowerCase();
  
  document.getElementById("editGuidelineForm").classList.remove("hidden");
  document.getElementById("editGuidelineCondition").focus();
}

function closeEditGuidelineForm() {
  document.getElementById("editGuidelineForm").classList.add("hidden");
}

async function editJourney(journeyId) {
  const journey = detailState.bot?.journeys?.find(j => j.id === journeyId);
  if (!journey) return;
  
  document.getElementById("editJourneyId").value = journeyId;
  document.getElementById("editJourneyTitle").value = journey.title || "";
  document.getElementById("editJourneyDescription").value = journey.description || "";
  document.getElementById("editJourneyConditions").value = (journey.conditions || []).join("\n");
  
  document.getElementById("editJourneyForm").classList.remove("hidden");
  document.getElementById("editJourneyTitle").focus();
}

function closeEditJourneyForm() {
  document.getElementById("editJourneyForm").classList.add("hidden");
}

// Make functions globally available
window.openAddGuidelineForm = openAddGuidelineForm;
window.closeAddGuidelineForm = closeAddGuidelineForm;
window.openAddJourneyForm = openAddJourneyForm;
window.closeAddJourneyForm = closeAddJourneyForm;
window.editGuideline = editGuideline;
window.closeEditGuidelineForm = closeEditGuidelineForm;
window.editJourney = editJourney;
window.closeEditJourneyForm = closeEditJourneyForm;

// =============================================================================
// API Calls
// =============================================================================

async function fetchBots() {
  renderSkeletons();
  try {
    const response = await fetch(`${API_BASE_URL}${ENDPOINTS.listBots}`);
    if (!response.ok) {
      throw new Error(`Failed to load bots (${response.status})`);
    }
    const payload = await response.json();
    const bots = normalizeBotList(payload);
    renderBots(bots);
  } catch (error) {
    console.error("Fetch error:", error);
    renderError(error.message);
  }
}

async function createBot() {
  collectCurrentStepData();
  
  if (formState.data.guidelines.length === 0) {
    setStatus("Add at least one guideline.");
    return;
  }
  if (formState.data.journeys.length === 0) {
    setStatus("Add at least one journey.");
    return;
  }
  
  setStatus("Creating bot...", false);
  submitBotButton.disabled = true;
  
  try {
    const response = await fetch(`${API_BASE_URL}${ENDPOINTS.createBot}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(formState.data),
    });
    
    const payload = await response.json();
    
    if (!response.ok) {
      const errorMsg = payload?.detail?.message || payload?.error || `Error ${response.status}`;
      throw new Error(errorMsg);
    }
    
    if (payload.success) {
      setStatus("Bot created successfully!", false);
      showToast("Bot created successfully!");
      setTimeout(() => {
        closeModal();
        fetchBots();
      }, 1000);
    } else {
      const errors = payload.errors?.map((e) => e.message).join(", ") || "Unknown error";
      throw new Error(errors);
    }
  } catch (error) {
    console.error("Create error:", error);
    setStatus(error.message || "Failed to create bot.");
    showToast(error.message || "Failed to create bot.", true);
  } finally {
    submitBotButton.disabled = false;
  }
}

async function deleteBot(botId) {
  try {
    const response = await fetch(`${API_BASE_URL}${ENDPOINTS.deleteBot(botId)}`, {
      method: "DELETE",
    });
    
    if (!response.ok) {
      throw new Error(`Failed to delete (${response.status})`);
    }
    
    showToast("Bot deleted successfully!");
    fetchBots();
  } catch (error) {
    console.error("Delete error:", error);
    showToast(error.message, true);
  }
}

// Guideline CRUD
async function saveNewGuideline() {
  const condition = document.getElementById("newGuidelineCondition").value.trim();
  const action = document.getElementById("newGuidelineAction").value.trim();
  const criticality = document.getElementById("newGuidelineCriticality").value;
  
  if (!condition) {
    showToast("Condition is required", true);
    return;
  }
  
  try {
    const response = await fetch(`${API_BASE_URL}${ENDPOINTS.addGuidelineToBot(detailState.botId)}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ condition, action, criticality }),
    });
    
    if (!response.ok) {
      const data = await response.json();
      throw new Error(data.detail || "Failed to add guideline");
    }
    
    showToast("Guideline added!");
    closeAddGuidelineForm();
    await refreshDetailView();
  } catch (error) {
    console.error("Add guideline error:", error);
    showToast(error.message, true);
  }
}

async function saveEditedGuideline() {
  const guidelineId = document.getElementById("editGuidelineId").value;
  const condition = document.getElementById("editGuidelineCondition").value.trim();
  const action = document.getElementById("editGuidelineAction").value.trim();
  const criticality = document.getElementById("editGuidelineCriticality").value;
  
  if (!condition) {
    showToast("Condition is required", true);
    return;
  }
  
  try {
    const response = await fetch(`${API_BASE_URL}${ENDPOINTS.updateGuideline(guidelineId)}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ condition, action, criticality }),
    });
    
    if (!response.ok) {
      const data = await response.json();
      throw new Error(data.detail || "Failed to update guideline");
    }
    
    showToast("Guideline updated!");
    closeEditGuidelineForm();
    await refreshDetailView();
  } catch (error) {
    console.error("Update guideline error:", error);
    showToast(error.message, true);
  }
}

async function deleteGuidelineItem(guidelineId) {
  if (!confirm("Delete this guideline?")) return;
  
  try {
    const response = await fetch(`${API_BASE_URL}${ENDPOINTS.deleteGuideline(guidelineId)}`, {
      method: "DELETE",
    });
    
    if (!response.ok) {
      throw new Error("Failed to delete guideline");
    }
    
    showToast("Guideline deleted!");
    await refreshDetailView();
  } catch (error) {
    console.error("Delete guideline error:", error);
    showToast(error.message, true);
  }
}

window.saveNewGuideline = saveNewGuideline;
window.saveEditedGuideline = saveEditedGuideline;
window.deleteGuidelineItem = deleteGuidelineItem;

// Journey CRUD
async function saveNewJourney() {
  const title = document.getElementById("newJourneyTitle").value.trim();
  const description = document.getElementById("newJourneyDescription").value.trim();
  const conditionsText = document.getElementById("newJourneyConditions").value.trim();
  const conditions = conditionsText.split("\n").map(s => s.trim()).filter(Boolean);
  
  if (!title || !description || conditions.length === 0) {
    showToast("All fields are required", true);
    return;
  }
  
  try {
    const response = await fetch(`${API_BASE_URL}${ENDPOINTS.addJourneyToBot(detailState.botId)}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title, description, conditions }),
    });
    
    if (!response.ok) {
      const data = await response.json();
      throw new Error(data.detail || "Failed to add journey");
    }
    
    showToast("Journey added!");
    closeAddJourneyForm();
    await refreshDetailView();
  } catch (error) {
    console.error("Add journey error:", error);
    showToast(error.message, true);
  }
}

async function saveEditedJourney() {
  const journeyId = document.getElementById("editJourneyId").value;
  const title = document.getElementById("editJourneyTitle").value.trim();
  const description = document.getElementById("editJourneyDescription").value.trim();
  const conditionsText = document.getElementById("editJourneyConditions").value.trim();
  const conditions = conditionsText.split("\n").map(s => s.trim()).filter(Boolean);
  
  if (!title || !description || conditions.length === 0) {
    showToast("All fields are required", true);
    return;
  }
  
  try {
    const response = await fetch(`${API_BASE_URL}${ENDPOINTS.updateJourney(journeyId)}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title, description, conditions }),
    });
    
    if (!response.ok) {
      const data = await response.json();
      throw new Error(data.detail || "Failed to update journey");
    }
    
    showToast("Journey updated!");
    closeEditJourneyForm();
    await refreshDetailView();
  } catch (error) {
    console.error("Update journey error:", error);
    showToast(error.message, true);
  }
}

async function deleteJourneyItem(journeyId) {
  if (!confirm("Delete this journey?")) return;
  
  try {
    const response = await fetch(`${API_BASE_URL}${ENDPOINTS.deleteJourney(journeyId)}`, {
      method: "DELETE",
    });
    
    if (!response.ok) {
      throw new Error("Failed to delete journey");
    }
    
    showToast("Journey deleted!");
    await refreshDetailView();
  } catch (error) {
    console.error("Delete journey error:", error);
    showToast(error.message, true);
  }
}

window.saveNewJourney = saveNewJourney;
window.saveEditedJourney = saveEditedJourney;
window.deleteJourneyItem = deleteJourneyItem;

async function refreshDetailView() {
  try {
    const response = await fetch(`${API_BASE_URL}${ENDPOINTS.getBot(detailState.botId)}`);
    if (!response.ok) throw new Error("Failed to refresh");
    
    const bot = await response.json();
    detailState.bot = bot;
    renderDetailView(bot);
    
    // Also refresh the main list
    fetchBots();
  } catch (error) {
    console.error("Refresh error:", error);
  }
}

// =============================================================================
// Chat Modal Functions
// =============================================================================

async function openChat(bot) {
  chatState.botId = bot.id;
  chatState.botName = bot.name;
  chatState.lastMessageCount = 0;
  chatState.isWaitingForResponse = false;
  
  chatBotName.textContent = `Chat with ${bot.name || "Bot"}`;
  chatSessionId.textContent = "Creating session...";
  chatMessages.innerHTML = `
    <div class="chat-welcome">
      <div class="chat-welcome-icon">💬</div>
      <div class="chat-welcome-text">Connecting to ${bot.name || "Bot"}...</div>
    </div>
  `;
  chatModal.classList.remove("hidden");
  document.body.style.overflow = "hidden";
  
  try {
    const response = await fetch(`${API_BASE_URL}${ENDPOINTS.createSession(bot.id)}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
    });
    
    if (!response.ok) {
      throw new Error(`Failed to create session (${response.status})`);
    }
    
    const data = await response.json();
    chatState.sessionId = data.session_id;
    
    chatSessionId.textContent = `Session: ${chatState.sessionId?.slice(0, 8) || "--"}...`;
    chatMessages.innerHTML = `
      <div class="chat-welcome">
        <div class="chat-welcome-icon">💬</div>
        <div class="chat-welcome-text">Connected! Start chatting with ${bot.name || "Bot"}</div>
      </div>
    `;
    
    startMessagePolling();
    chatInput?.focus();
    
  } catch (error) {
    console.error("Failed to create chat session:", error);
    chatSessionId.textContent = "Connection failed";
    chatMessages.innerHTML = `
      <div class="chat-message system">
        Failed to connect: ${error.message}
      </div>
    `;
  }
}

function closeChat() {
  stopMessagePolling();
  
  chatState.botId = null;
  chatState.botName = null;
  chatState.sessionId = null;
  chatState.lastMessageCount = 0;
  chatState.isWaitingForResponse = false;
  
  chatModal.classList.add("hidden");
  document.body.style.overflow = "";
}

async function sendChatMessage() {
  const message = chatInput?.value?.trim();
  if (!message || !chatState.sessionId) return;
  
  chatInput.value = "";
  appendChatMessage(message, "user");
  
  chatState.isWaitingForResponse = true;
  showTypingIndicator();
  
  try {
    const response = await fetch(`${API_BASE_URL}${ENDPOINTS.sendMessage(chatState.sessionId)}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    });
    
    if (!response.ok) {
      throw new Error(`Failed to send message (${response.status})`);
    }
    
  } catch (error) {
    console.error("Failed to send message:", error);
    hideTypingIndicator();
    appendChatMessage(`Error: ${error.message}`, "system");
  }
}

function appendChatMessage(content, type = "bot") {
  const welcome = chatMessages.querySelector(".chat-welcome");
  if (welcome) welcome.remove();
  
  const messageDiv = document.createElement("div");
  messageDiv.className = `chat-message ${type}`;
  messageDiv.textContent = content;
  
  chatMessages.appendChild(messageDiv);
  scrollToBottom();
}

function showTypingIndicator() {
  hideTypingIndicator();
  
  const typingDiv = document.createElement("div");
  typingDiv.className = "chat-typing";
  typingDiv.id = "typingIndicator";
  typingDiv.innerHTML = `
    <div class="chat-typing-dot"></div>
    <div class="chat-typing-dot"></div>
    <div class="chat-typing-dot"></div>
  `;
  
  chatMessages.appendChild(typingDiv);
  scrollToBottom();
}

function hideTypingIndicator() {
  const typing = document.getElementById("typingIndicator");
  if (typing) typing.remove();
}

function scrollToBottom() {
  if (chatMessages) {
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }
}

function startMessagePolling() {
  chatState.polling = setInterval(async () => {
    if (!chatState.sessionId) return;
    
    try {
      const response = await fetch(`${API_BASE_URL}${ENDPOINTS.getMessages(chatState.sessionId)}`);
      if (!response.ok) return;
      
      const data = await response.json();
      const messages = data.messages || [];
      
      renderNewMessages(messages);
      
    } catch (error) {
      console.error("Polling error:", error);
    }
  }, 1500);
}

function stopMessagePolling() {
  if (chatState.polling) {
    clearInterval(chatState.polling);
    chatState.polling = null;
  }
}

function renderNewMessages(messages) {
  const messageEvents = messages.filter(
    (m) => m.kind === "message" || m.event_kind === "message"
  );
  
  if (messageEvents.length <= chatState.lastMessageCount) {
    return;
  }
  
  const newMessages = messageEvents.slice(chatState.lastMessageCount);
  chatState.lastMessageCount = messageEvents.length;
  
  const hasBotMessage = newMessages.some(
    (m) => (m.source === "ai_agent" || m.event_source === "ai_agent")
  );
  
  if (hasBotMessage) {
    chatState.isWaitingForResponse = false;
    hideTypingIndicator();
  }
  
  for (const msg of newMessages) {
    const source = msg.source || msg.event_source;
    const content = msg.message || msg.data?.message || "";
    
    if (!content) continue;
    
    let type = "bot";
    if (source === "customer" || source === "user") {
      continue;
    } else if (source === "ai_agent") {
      type = "bot";
    } else if (source === "system") {
      type = "system";
    }
    
    appendChatMessage(content, type);
  }
}

// =============================================================================
// Event Listeners
// =============================================================================

botForm?.addEventListener("submit", async (event) => {
  event.preventDefault();
  await createBot();
});

refreshButton?.addEventListener("click", fetchBots);
modalOverlay?.addEventListener("click", closeModal);
closeModalButton?.addEventListener("click", closeModal);
cancelModalButton?.addEventListener("click", closeModal);
nextStepButton?.addEventListener("click", nextStep);
prevStepButton?.addEventListener("click", prevStep);

// Chat modal
chatModalOverlay?.addEventListener("click", closeChat);
closeChatButton?.addEventListener("click", closeChat);
sendMessageButton?.addEventListener("click", sendChatMessage);
chatInput?.addEventListener("keypress", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendChatMessage();
  }
});

// Detail modal
detailModalOverlay?.addEventListener("click", closeDetailView);
closeDetailButton?.addEventListener("click", closeDetailView);

// =============================================================================
// Initialize
// =============================================================================

document.addEventListener("DOMContentLoaded", () => {
  fetchBots();
  if (document.getElementById("guidelinesList")) {
    addGuideline();
  }
  if (document.getElementById("journeysList")) {
    addJourney();
  }
});
