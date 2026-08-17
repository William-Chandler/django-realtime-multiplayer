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
    const response = await fetch(`/rooms/${ROOM_ID}/save/`, {
        method: "POST",
        headers: { "X-CSRFToken": CSRF_TOKEN }
    });

    const data = await response.json();
    alert("Whiteboard saved!");

    // Refresh dropdown if owner
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
