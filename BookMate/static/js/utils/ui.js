// utils/ui.js
import { addBook } from "./api.js";
import { showSuccess, showError, showBookNotification } from "./notifications.js";

// Toggle between welcome and search results sections
export function toggleSections(mode) {
  const welcomeSection = document.getElementById("welcome-section");
  const searchResultsSection = document.getElementById("search-results");

  if (welcomeSection) welcomeSection.style.display = mode === "search" ? "none" : "block";
  if (searchResultsSection) searchResultsSection.style.display = mode === "search" ? "block" : "none";
}

// Render search results
export function renderSearchResults(data, query) {
  const resultsGrid = document.getElementById("results-grid");
  resultsGrid.innerHTML = "";

  if (!data || !data.length) {
    resultsGrid.innerHTML = `<p>No results found for "${query}"</p>`;
    return;
  }

  data.forEach((book) => {
    const card = document.createElement("div");
    card.classList.add("book-card", "search-book-card");
    card.dataset.olid = book.olid;

    card.innerHTML = `
      <img src="${book.cover_url}" alt="cover" class="book-cover">
      <p class="book-title">${book.title}</p>
      <p class="book-author">${book.author || "Unknown"}</p>
      <!-- ➕ Add Button -->
      <button class="add-btn"
        data-olid="${book.olid}"
        data-title="${book.title}"
        data-author="${book.author || ''}"
        data-cover="${book.cover_url || ''}"
        data-pages="${book.pages || 0}">
        ➕ Add to List
      </button>

    `;
    resultsGrid.appendChild(card);
  });

  // reattach listeners after render
  attachAddButtonHandlers();
}

// Create a single book card
export function createBookCard(book) {
  const card = document.createElement("div");
  card.className = "book-card";

  // Match CSS classes — no inline styles
  const coverHTML = book.cover_url
    ? `<img src="${book.cover_url}" alt="${book.title}" class="book-cover">`
    : `<div class="no-cover">No Cover</div>`;

  card.innerHTML = `
    ${coverHTML}
    <p class="book-title">${book.title}</p>
    <p class="book-author">${book.author || "Unknown"}</p>
    <button class="add-btn"
      data-olid="${book.olid}"
      data-title="${book.title}"
      data-author="${book.author || ''}"
      data-cover="${book.cover_url || ''}"
      data-pages="${book.pages || 0}">
      ➕ Add to List
    </button>
  `;

  return card;
}


// Add “Add to List” button handlers
export function attachAddButtonHandlers() {
  document.querySelectorAll(".add-btn").forEach(btn => {
    btn.addEventListener("click", async () => {
      const payload = {
        title: btn.dataset.title,
        author: btn.dataset.author,
        cover_url: btn.dataset.cover,
        olid: btn.dataset.olid,
        pages: btn.dataset.pages ? parseInt(btn.dataset.pages) : null
      };

      console.log("Adding book:", payload);
      const result = await addBook(payload);
      
      // Use custom notification instead of alert
      if (result.success || result.message === "Book added successfully!" || result.message.includes("added")) {
        showSuccess("Book added to your list!", { title: "Success" });
        addBookToUserList(payload);
      } else {
        showError(result.message || "Failed to add book", { title: "Error" });
      }
    });
  });
}


// Add a book card to user bookshelf UI
// export function addBookToUserList(payload) {
//   const userBooksGrid = document.getElementById("user-books");
//   if (!userBooksGrid) return;

//   const existing = userBooksGrid.querySelector(`[data-olid="${payload.olid}"]`);
//   if (existing) return;

//   const newCard = document.createElement("div");
//   newCard.className = "book-card";
//   newCard.setAttribute("data-olid", payload.olid);
//   newCard.setAttribute("data-title", payload.title);
//   newCard.setAttribute("data-author", payload.author || "");
//   newCard.setAttribute("data-pages", payload.pages || 0);

//   newCard.innerHTML = `
//     <a href="/book/${payload.olid}" class="book-card-link">
//       <img src="${payload.cover_url || ""}" alt="${payload.title} cover" class="book-cover">
//       <p class="book-title">${payload.title}</p>
//       <p class="book-author">${payload.author || "Unknown"}</p>
//     </a>
//     <div class="book-actions">
//       <button class="favorite-btn" data-olid="${payload.olid}">
//         <span class="star-icon">☆</span>
//       </button>

//       <button class="edit-btn"
//         data-olid="${payload.olid}"
//         data-page="${payload.current_page || 0}"
//         data-pages="${payload.pages || 0}">
//         Edit
//       </button>

//       <button class="remove-btn" data-olid="${payload.olid}">❌ Remove</button>
//     </div>
//   `;
//   userBooksGrid.appendChild(newCard);

// }

export function addBookToUserList(payload) {
  const userBooksGrid = document.getElementById("user-books");
  if (!userBooksGrid) return;

  // REMOVE EMPTY STATE MESSAGE IF IT EXISTS
  // Look for a direct child paragraph that contains the "No books" text
  const directChildren = Array.from(userBooksGrid.children);
  const emptyMessage = directChildren.find(child => 
    child.tagName === "P" && 
    child.textContent.trim().includes("No books added yet")
  );
  if (emptyMessage) {
    emptyMessage.remove();
  }

  const existing = userBooksGrid.querySelector(`[data-olid="${payload.olid}"]`);
  if (existing) return;

  const newCard = document.createElement("div");
  newCard.className = "book-card";
  newCard.setAttribute("data-olid", payload.olid);
  newCard.setAttribute("data-title", payload.title);
  newCard.setAttribute("data-author", payload.author || "");
  // store page on card dataset so sorting/filtering can use it
  newCard.setAttribute("data-page", payload.current_page || 0);
  newCard.setAttribute("data-pages", payload.pages || 0);

newCard.innerHTML = `
<a href="/book/${payload.olid}" class="book-card-link">
  <img src="${payload.cover_url || ""}" alt="${payload.title} cover" class="book-cover">
  <p class="book-title">${payload.title}</p>
  <p class="book-author">${payload.author || "Unknown"}</p>
</a>

<!-- ✅ PROGRESS BAR (THIS WAS MISSING) -->
<div class="reading-progress-container">
  <div class="progress-info">
    <span class="progress-text" data-progress-text>
      Page ${payload.current_page || 0} of ${payload.pages || 0}
    </span>
    <span class="progress-percentage">0%</span>
  </div>
  <div class="progress-bar-wrapper">
    <div class="progress-bar-bg">
      <div 
        class="progress-bar-fill" 
        data-progress-bar 
        data-current="${payload.current_page || 0}" 
        data-total="${payload.pages || 0}">
      </div>
    </div>
  </div>
</div>

<div class="book-actions">
  <button class="favorite-btn" data-olid="${payload.olid}" title="Add to favorites">
    <span class="star-icon">☆</span>
  </button>

  <!-- ✅ KEEP edit-btn EXACTLY AS YOU SAID -->
  <button 
    class="edit-btn" 
    data-olid="${payload.olid}" 
    data-page="${payload.current_page || 0}" 
    data-pages="${payload.pages || 0}">
    📝 Progress
  </button>

  <button class="remove-btn" data-olid="${payload.olid}">
    ❌ Remove
  </button>
</div>
`;

  userBooksGrid.appendChild(newCard);

  // ✅ Initialize progress bar for newly added card
  const newBar = newCard.querySelector("[data-progress-bar]");
  if (newBar) {
    const current = Number(newBar.dataset.current) || 0;
    const total = Number(newBar.dataset.total) || 0;
    const percent = total > 0 ? Math.round((current / total) * 100) : 0;
    newBar.style.width = `${percent}%`;
  }

  // NO local edit click handler here — rely on delegated handler in dashboard.js
}


// Handle removal from DOM
export function handleBookRemoval(removeBtn) {
  const bookCard = removeBtn.closest(".book-card");
  if (bookCard) bookCard.remove();

  const userBooksGrid = document.getElementById("user-books");
  if (userBooksGrid && userBooksGrid.children.length === 0) {
    const emptyMsg = document.createElement("p");
    emptyMsg.textContent = "No books added yet. Try searching above!";
    userBooksGrid.appendChild(emptyMsg);
  }
}
