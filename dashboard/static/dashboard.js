const $ = id => document.getElementById(id);
const messages = $("messages"), form = $("promptForm"), promptInput = $("prompt");
const sendButton = $("sendButton");
const toolsButton = $("toolsButton"), toolsMenu = $("toolsMenu");
const sidebar = $("sidebar"), scrim = $("scrim");
let socket, reconnectTimer, currentConversationId = null;
let busy = false;
const runningTools = new Map();
marked.setOptions({gfm: true, breaks: true});

const overviewStep = $("overviewStep");
const warningStep = $("warningStep");
$("onboardingNext").addEventListener("click", () => {
  overviewStep.classList.remove("active");
  warningStep.classList.add("active");
});
$("onboardingBack").addEventListener("click", () => {
  warningStep.classList.remove("active");
  overviewStep.classList.add("active");
});
$("acknowledge").addEventListener("change", event => {
  $("enterDashboard").disabled = !event.target.checked;
});
$("enterDashboard").addEventListener("click", () => {
  $("onboarding").classList.add("hidden");
  promptInput.focus();
});

function icon(done = false) {
  return done
    ? '<svg viewBox="0 0 24 24"><path d="m5 12 4 4L19 6"/></svg>'
    : '<svg viewBox="0 0 24 24"><path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/></svg>';
}

function setConnected(connected) {
  ["connectionDot", "topConnectionDot"].forEach(id => $(id).classList.toggle("online", connected));
  $("connectionText").textContent = connected ? "Connected" : "Disconnected";
  $("topConnectionText").textContent = connected ? "Online" : "Offline";
}

function connect() {
  clearTimeout(reconnectTimer);
  const protocol = location.protocol === "https:" ? "wss:" : "ws:";
  socket = new WebSocket(`${protocol}//${location.host}/ws/chat`);
  socket.onopen = () => setConnected(true);
  socket.onclose = () => { setConnected(false); reconnectTimer = setTimeout(connect, 1800); };
  socket.onerror = () => setConnected(false);
  socket.onmessage = event => handleEvent(JSON.parse(event.data));
}

function scrollBottom() { messages.scrollTo({top: messages.scrollHeight, behavior: "smooth"}); }

function addMessage(role, content, pending = false) {
  $("welcome")?.remove();
  const article = document.createElement("article");
  article.className = `message ${role}`;
  article.innerHTML = `<div class="message-row"><div class="message-avatar">${role === "assistant" ? "P" : "Y"}</div><div class="message-content"></div></div>`;
  const body = article.querySelector(".message-content");
  if (pending) body.innerHTML = '<div class="thinking"><i></i><i></i><i></i></div>';
  else if (role === "assistant") body.innerHTML = DOMPurify.sanitize(marked.parse(content));
  else body.textContent = content;
  messages.appendChild(article);
  scrollBottom();
  return article;
}

function getToolStack() {
  let stack = $("activeToolStack");
  if (!stack) {
    stack = document.createElement("div");
    stack.id = "activeToolStack";
    stack.className = "tool-stack";
    const pending = $("pendingMessage");
    pending ? pending.before(stack) : messages.appendChild(stack);
  }
  return stack;
}

function addTool(name, status) {
  if (status === "started") {
    const row = document.createElement("details");
    row.className = "tool-call running";
    row.innerHTML = `<summary><span class="tool-state">${icon()}</span><span class="tool-name"></span><span class="tool-time">Running</span><svg class="tool-chevron" viewBox="0 0 24 24"><path d="m6 9 6 6 6-6"/></svg></summary><div class="tool-details">ProxAI requested this tool and is waiting for its result.</div>`;
    row.querySelector(".tool-name").textContent = name.replaceAll("_", " ");
    getToolStack().appendChild(row);
    const queue = runningTools.get(name) || [];
    queue.push({element: row, started: Date.now()});
    runningTools.set(name, queue);
    scrollBottom();
    return;
  }
  const queue = runningTools.get(name) || [];
  const record = queue.shift();
  if (!record) return;
  record.element.className = "tool-call done";
  record.element.querySelector(".tool-state").innerHTML = icon(true);
  record.element.querySelector(".tool-time").textContent = `${((Date.now() - record.started) / 1000).toFixed(1)}s`;
  record.element.querySelector(".tool-details").textContent = "Tool completed and returned its result to ProxAI.";
}

function finishPending() {
  $("pendingMessage")?.remove();
  $("activeToolStack")?.removeAttribute("id");
}

function handleEvent(data) {
  if (data.type === "session") {
    currentConversationId = data.conversation_id;
    loadConversations();
  } else if (data.type === "thinking") {
    $("activeToolStack")?.removeAttribute("id");
    const pending = addMessage("assistant", "", true);
    pending.id = "pendingMessage";
  } else if (data.type === "tool") {
    addTool(data.name, data.status);
  } else if (data.type === "response") {
    currentConversationId = data.conversation_id;
    finishPending();
    addMessage("assistant", data.content);
    setBusy(false);
    loadConversations();
  } else if (data.type === "history") {
    currentConversationId = data.conversation_id;
    renderHistory(data.messages);
    setBusy(false);
    loadConversations();
  } else if (data.type === "error") {
    finishPending();
    addMessage("assistant", `**Request failed:** ${data.message}`);
    setBusy(false);
  } else if (data.type === "reset_complete") {
    currentConversationId = data.conversation_id;
    setBusy(false);
    loadConversations();
  }
}

function setBusy(value) {
  busy = value;
  sendButton.disabled = value;
  promptInput.disabled = value;
  if (!value) promptInput.focus();
}

function submitPrompt(value) {
  const prompt = (value ?? promptInput.value).trim();
  if (!prompt || busy || socket?.readyState !== WebSocket.OPEN) return;
  addMessage("user", prompt);
  socket.send(JSON.stringify({type: "prompt", prompt}));
  promptInput.value = "";
  promptInput.style.height = "auto";
  setBusy(true);
}

function renderHistory(history) {
  messages.innerHTML = "";
  runningTools.clear();
  history.forEach(item => addMessage(item.role, item.content));
  scrollBottom();
}

function historyBucket(value) {
  if (!value) return "Previous";
  const date = new Date(value), now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const messageDay = new Date(date.getFullYear(), date.getMonth(), date.getDate());
  const days = Math.floor((today - messageDay) / 86400000);
  if (days <= 0) return "Today";
  if (days === 1) return "Yesterday";
  if (days < 7) return "Previous 7 days";
  if (days < 30) return "Previous 30 days";
  return date.toLocaleDateString(undefined, {month: "long", year: "numeric"});
}

async function loadConversations() {
  const list = $("conversationList");
  try {
    const response = await fetch("/api/conversations");
    const data = await response.json();
    const groups = new Map();
    data.conversations.forEach(item => {
      const bucket = historyBucket(item.updated_at);
      if (!groups.has(bucket)) groups.set(bucket, []);
      groups.get(bucket).push(item);
    });
    list.innerHTML = "";
    if (!data.conversations.length) {
      list.innerHTML = '<div class="sidebar-empty">No saved conversations yet.</div>';
      return;
    }
    for (const [label, items] of groups) {
      const group = document.createElement("section");
      group.className = "history-group";
      const heading = document.createElement("p");
      heading.className = "group-label";
      heading.textContent = label;
      group.appendChild(heading);
      items.forEach(item => {
        const button = document.createElement("button");
        button.className = `chat-item ${item.id === currentConversationId ? "active" : ""}`;
        button.title = item.preview;
        button.innerHTML = "<span></span><i>•••</i>";
        button.querySelector("span").textContent = item.title;
        button.addEventListener("click", () => selectConversation(item.id, button));
        group.appendChild(button);
      });
      list.appendChild(group);
    }
  } catch (_error) {
    list.innerHTML = '<div class="sidebar-empty">Could not load chat history.</div>';
  }
}

function selectConversation(id, button) {
  if (busy || id === currentConversationId || socket?.readyState !== WebSocket.OPEN) return;
  document.querySelectorAll(".chat-item").forEach(item => item.classList.remove("active"));
  button.classList.add("active", "loading");
  setBusy(true);
  socket.send(JSON.stringify({type: "select_conversation", conversation_id: id}));
  if (innerWidth <= 760) closeSidebar();
}

form.addEventListener("submit", event => { event.preventDefault(); submitPrompt(); });
promptInput.addEventListener("keydown", event => {
  if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); submitPrompt(); }
});
promptInput.addEventListener("input", () => {
  promptInput.style.height = "auto";
  promptInput.style.height = `${Math.min(promptInput.scrollHeight, 180)}px`;
});
document.querySelectorAll("[data-prompt]").forEach(button => button.addEventListener("click", () => submitPrompt(button.dataset.prompt)));

toolsButton.addEventListener("click", event => {
  event.stopPropagation();
  const open = toolsMenu.classList.toggle("open");
  toolsButton.setAttribute("aria-expanded", String(open));
});
toolsMenu.addEventListener("click", event => event.stopPropagation());
document.addEventListener("click", () => { toolsMenu.classList.remove("open"); toolsButton.setAttribute("aria-expanded", "false"); });

function openSidebar() {
  if (innerWidth <= 760) { sidebar.classList.add("mobile-open"); scrim.classList.add("visible"); }
  else document.body.classList.toggle("sidebar-collapsed");
}
function closeSidebar() { sidebar.classList.remove("mobile-open"); scrim.classList.remove("visible"); }
$("openSidebar").addEventListener("click", openSidebar);
$("closeSidebar").addEventListener("click", closeSidebar);
scrim.addEventListener("click", closeSidebar);

$("newChat").addEventListener("click", () => {
  if (busy || socket?.readyState !== WebSocket.OPEN) return;
  currentConversationId = null;
  messages.innerHTML = '<div id="welcome" class="welcome"><div class="welcome-logo">P</div><h1>How can I help you today?</h1><p>Start a fresh task whenever you are ready.</p></div>';
  runningTools.clear();
  socket.send(JSON.stringify({type: "reset"}));
});
document.addEventListener("keydown", event => {
  if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
    event.preventDefault();
    $("newChat").click();
  }
});

connect();
