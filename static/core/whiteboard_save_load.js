// whiteboard_save_load.js

// These will be injected by the template
let ROOM_ID = null;
let CSRF_TOKEN = null;

// Called once on page load
export function initWhiteboardControls(roomId, csrfToken, isOwner) {
    ROOM_ID = roomId;
    CSRF_TOKEN = csrfToken;

    const saveBtn = document.getElementById("save-board-btn");
    if (saveBtn) {
        saveBtn.addEventListener("click", saveBoard);
    }

    if (isOwner) {
        loadBoardsIntoDropdown();
        const dropdown = document.getElementById("load-board-dropdown");
        dropdown.addEventListener("change", loadSelectedBoard);
    }
}

// ---------------------------
// Ssave board
// ---------------------------
async function saveBoard() {
    const statusEl = document.getElementById("save-status");

    // Clear previous message
    statusEl.textContent = "";
    statusEl.style.color = "";

    const nameInput = document.getElementById("board-name-input");
    const boardName = nameInput ? nameInput.value.trim() : "";

    if (!boardName) {
        statusEl.style.color = "red";
        statusEl.textContent = "Please enter a name for your whiteboard before saving.";
        setTimeout(() => statusEl.textContent = "", 3000);
        return;
    }

    // First attempt: check if board exists
    let response = await fetch(`/rooms/${ROOM_ID}/save/`, {
        method: "POST",
        headers: {
            "X-CSRFToken": CSRF_TOKEN,
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ name: boardName })
    });

    let data = await response.json();

    if (data.exists) {
        const ok = confirm(`A board named "${boardName}" already exists. Overwrite it?`);
        if (!ok) return;

        // Second request: overwrite
        response = await fetch(`/rooms/${ROOM_ID}/save/`, {
            method: "POST",
            headers: {
                "X-CSRFToken": CSRF_TOKEN,
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ name: boardName, overwrite: true })
        });

        data = await response.json();
    }

    // Success message
    statusEl.style.color = "green";
    statusEl.textContent = "Whiteboard saved!";
    setTimeout(() => statusEl.textContent = "", 3000);

    const dropdown = document.getElementById("load-board-dropdown");
    if (dropdown) {
        loadBoardsIntoDropdown();
    }
}



// ---------------------------
// Load board
// ---------------------------
async function loadSelectedBoard(event) {
    const boardId = event.target.value;
    if (!boardId) return;

    const response = await fetch(`/rooms/${ROOM_ID}/load_board/${boardId}/`, {
        method: "POST",
        headers: { "X-CSRFToken": CSRF_TOKEN }
    });

    const data = await response.json();
    console.log("Loaded board:", data);
}

// ---------------------------
// Populate dropdown
// ---------------------------
async function loadBoardsIntoDropdown() {
    const dropdown = document.getElementById("load-board-dropdown");
    if (!dropdown) return;

    const response = await fetch(`/whiteboards/api/my_boards/`);
    const boards = await response.json();

    dropdown.innerHTML = `<option value="">Load Saved Board...</option>`;

    boards.forEach(board => {
        const opt = document.createElement("option");
        opt.value = board.id;
        opt.textContent = board.name;
        dropdown.appendChild(opt);
    });
	
}
