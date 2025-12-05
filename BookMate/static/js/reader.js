let pdfDoc = null;
let currentPage = 1;
let pageRendering = false;

const leftCanvas = document.getElementById("leftPage");
const rightCanvas = document.getElementById("rightPage");
const leftCtx = leftCanvas.getContext("2d");
const rightCtx = rightCanvas.getContext("2d");
const pageNumberDisplay = document.getElementById("page-number");

// ✅ Book-specific storage key
const bookId = rightCanvas.dataset.bookId || "default-book";
const STORAGE_KEY = `reader-progress-${bookId}`;

// ✅ Restore last saved page (must be odd for left page)
const savedPage = localStorage.getItem(STORAGE_KEY);
if (savedPage) {
  let page = parseInt(savedPage);
  currentPage = page % 2 === 0 ? page - 1 : page; // Ensure left page
}



fetch("/api/mock-book/")
  .then(res => res.json())
  .then(data => {
    console.log("PDF URL:", data.pdf_url);
    console.log("pdfjsLib available:", typeof pdfjsLib !== 'undefined');
    
    if (typeof pdfjsLib === 'undefined') {
      console.error("PDF.js library not loaded!");
      return;
    }
    
    pdfjsLib.getDocument(data.pdf_url).promise.then(pdf => {
      console.log("PDF loaded successfully, pages:", pdf.numPages);
      pdfDoc = pdf;
      renderPages(currentPage);
      loadChapters();  
    }).catch(error => {
      console.error("Error loading PDF:", error);
    });
  })
  .catch(error => {
    console.error("Error fetching mock book:", error);
  });


function renderPages(leftPageNum) {
  const rightPageNum = leftPageNum + 1;
  
  // Calculate responsive scale based on viewport - optimized for bigger readable text
  const containerWidth = window.innerWidth;
  const containerHeight = window.innerHeight - 140; // Account for header & footer
  const maxCanvasWidth = (containerWidth - 60) / 2; // ~45% width with padding
  const scale = Math.max(2.5, Math.min(3.5, (maxCanvasWidth / 220))); // Scale between 2.5-3.5 for large readable text
  
  // Render left page
  if (leftPageNum <= pdfDoc.numPages) {
    pdfDoc.getPage(leftPageNum).then((page) => {
      const viewport = page.getViewport({ scale: scale });
      leftCanvas.width = viewport.width;
      leftCanvas.height = viewport.height;
      
      page.render({
        canvasContext: leftCtx,
        viewport: viewport,
      });
    });
  } else {
    leftCtx.clearRect(0, 0, leftCanvas.width, leftCanvas.height);
  }
  
  // Render right page
  if (rightPageNum <= pdfDoc.numPages) {
    pdfDoc.getPage(rightPageNum).then((page) => {
      const viewport = page.getViewport({ scale: scale });
      rightCanvas.width = viewport.width;
      rightCanvas.height = viewport.height;
      
      page.render({
        canvasContext: rightCtx,
        viewport: viewport,
      });
    });
  } else {
    rightCtx.clearRect(0, 0, rightCanvas.width, rightCanvas.height);
  }
  
  pageNumberDisplay.textContent = `Pages ${leftPageNum}-${rightPageNum} / ${pdfDoc.numPages}`;
  
  // ✅ SAVE PROGRESS TO LOCALSTORAGE
  localStorage.setItem(STORAGE_KEY, leftPageNum);
  
  // ✅ SYNC PROGRESS TO DATABASE
  syncProgressToDatabase(leftPageNum);
  
  // ✅ SYNC CHAPTER DROPDOWN
  highlightCurrentChapter(leftPageNum);
}

// Debounced function to sync progress to backend
let syncTimeout;
function syncProgressToDatabase(currentPage) {
  // Clear previous timeout to debounce API calls
  clearTimeout(syncTimeout);
  
  // Wait 1 second after user stops flipping pages before syncing
  syncTimeout = setTimeout(() => {
    const bookId = document.getElementById("rightPage").dataset.bookId;
    if (!bookId) return;
    
    fetch('/api/update_progress/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken')
      },
      body: JSON.stringify({
        olid: bookId,
        progress: currentPage
      })
    })
    .then(res => res.json())
    .then(data => {
      if (data.success) {
        console.log('Progress synced to database:', currentPage);
      }
    })
    .catch(error => {
      console.error('Failed to sync progress:', error);
    });
  }, 1000);
}

// Helper function to get CSRF token
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}


function renderPage(num) {
  renderPages(num);
}


function highlightCurrentChapter(currentPage) {
  const select = document.getElementById("chapterSelect");
  const options = select.options;

  let active = "";
  for (let i = 0; i < options.length; i++) {
    const page = parseInt(options[i].value);
    if (page && page <= currentPage) active = options[i].value;
  }

  if (active) select.value = active;
}


function nextPage() {
  if (currentPage + 1 >= pdfDoc.numPages) return;
  
  // Create animated flipping page for right page
  const rightContainer = document.getElementById('rightPageContainer');
  const flippingPage = document.createElement('div');
  flippingPage.className = 'flipping-page flip-forward';
  flippingPage.style.transformStyle = 'preserve-3d';
  flippingPage.style.animationDuration = '0.3s';
  
  // Clone the current right page canvas
  const rightCanvas = document.getElementById('rightPage');
  const clonedCanvas = rightCanvas.cloneNode(true);
  clonedCanvas.style.position = 'absolute';
  clonedCanvas.style.top = '0';
  clonedCanvas.style.left = '0';
  clonedCanvas.style.width = '100%';
  clonedCanvas.style.height = '100%';
  clonedCanvas.style.backfaceVisibility = 'hidden';
  
  // Copy the canvas content
  const ctx = clonedCanvas.getContext('2d');
  ctx.drawImage(rightCanvas, 0, 0);
  
  flippingPage.appendChild(clonedCanvas);
  rightContainer.appendChild(flippingPage);
  
  // Update pages after animation completes
  setTimeout(() => {
    currentPage += 2; // Move by 2 pages (one spread)
    renderPages(currentPage);
    flippingPage.remove();
  }, 300);
}



function prevPage() {
  if (currentPage <= 1) return;
  
  // Create animated flipping page for left page
  const leftContainer = document.getElementById('leftPageContainer');
  const flippingPage = document.createElement('div');
  flippingPage.className = 'flipping-page flip-backward';
  flippingPage.style.transformStyle = 'preserve-3d';
  flippingPage.style.animationDuration = '0.3s';
  
  // Clone the current left page canvas
  const leftCanvas = document.getElementById('leftPage');
  const clonedCanvas = leftCanvas.cloneNode(true);
  clonedCanvas.style.position = 'absolute';
  clonedCanvas.style.top = '0';
  clonedCanvas.style.left = '0';
  clonedCanvas.style.width = '100%';
  clonedCanvas.style.height = '100%';
  clonedCanvas.style.backfaceVisibility = 'hidden';
  
  // Copy the canvas content
  const ctx = clonedCanvas.getContext('2d');
  ctx.drawImage(leftCanvas, 0, 0);
  
  flippingPage.appendChild(clonedCanvas);
  leftContainer.appendChild(flippingPage);
  
  // Update pages after animation completes
  setTimeout(() => {
    currentPage -= 2; // Move back by 2 pages (one spread)
    if (currentPage < 1) currentPage = 1;
    renderPages(currentPage);
    flippingPage.remove();
  }, 300);
}



function loadChapters() {
  const select = document.getElementById("chapterSelect");

  pdfDoc.getOutline().then(outline => {
    select.innerHTML = '<option value="">Go to Chapter</option>';

    if (!outline || outline.length === 0) {
      const opt = document.createElement("option");
      opt.textContent = "No chapters detected";
      opt.disabled = true;
      select.appendChild(opt);
      return;
    }

    outline.forEach((chapter, index) => {
      if (!chapter.dest) return;

      pdfDoc.getPageIndex(chapter.dest[0]).then(pageIndex => {
        const option = document.createElement("option");
        option.value = pageIndex + 1; // ✅ actual page number
        option.textContent = chapter.title || `Chapter ${index + 1}`;
        select.appendChild(option);
      });
    });
  });

  select.onchange = function () {
    if (this.value) {
      let targetPage = parseInt(this.value);
      // Ensure target page is odd (left page) for proper spread display
      if (targetPage % 2 === 0) targetPage -= 1;
      
      const isForward = targetPage > currentPage;
      
      // Show page flipping animation for 3 seconds with speed ramping
      let flipCount = 0;
      const totalDuration = 3000; // 3 seconds total
      const startTime = Date.now();
      
      const animateFlip = () => {
        const elapsed = Date.now() - startTime;
        const progress = elapsed / totalDuration; // 0 to 1
        
        if (elapsed < totalDuration) {
          flipCount++;
          
          // Calculate delay with specific speed progression
          let delay;
          if (progress < 0.15) {
            // Initial slow phase: 200ms
            delay = 200;
          } else if (progress < 0.35) {
            // Speed up to 150ms
            delay = 150;
          } else if (progress < 0.65) {
            // Fastest phase: 100ms
            delay = 100;
          } else if (progress < 0.85) {
            // Slow down to 150ms
            delay = 150;
          } else {
            // Final slow phase: 200ms
            delay = 200;
          }
          
          if (isForward) {
            // First, update the page content
            if (currentPage + 2 <= pdfDoc.numPages) {
              currentPage += 2;
            }
            
            // Then animate forward flipping with OLD content
            const rightContainer = document.getElementById('rightPageContainer');
            const flippingPage = document.createElement('div');
            flippingPage.className = 'flipping-page flip-forward';
            flippingPage.style.transformStyle = 'preserve-3d';
            flippingPage.style.animationDuration = delay + 'ms';
            
            const rightCanvas = document.getElementById('rightPage');
            const clonedCanvas = rightCanvas.cloneNode(true);
            clonedCanvas.style.position = 'absolute';
            clonedCanvas.style.top = '0';
            clonedCanvas.style.left = '0';
            clonedCanvas.style.width = '100%';
            clonedCanvas.style.height = '100%';
            clonedCanvas.style.backfaceVisibility = 'hidden';
            
            const ctx = clonedCanvas.getContext('2d');
            ctx.drawImage(rightCanvas, 0, 0);
            
            flippingPage.appendChild(clonedCanvas);
            rightContainer.appendChild(flippingPage);
            
            // Render new pages underneath the animation
            renderPages(currentPage);
            
            setTimeout(() => flippingPage.remove(), delay);
          } else {
            // First, update the page content
            if (currentPage > 1) {
              currentPage -= 2;
              if (currentPage < 1) currentPage = 1;
            }
            
            // Then animate backward flipping with OLD content
            const leftContainer = document.getElementById('leftPageContainer');
            const flippingPage = document.createElement('div');
            flippingPage.className = 'flipping-page flip-backward';
            flippingPage.style.transformStyle = 'preserve-3d';
            flippingPage.style.animationDuration = delay + 'ms';
            
            const leftCanvas = document.getElementById('leftPage');
            const clonedCanvas = leftCanvas.cloneNode(true);
            clonedCanvas.style.position = 'absolute';
            clonedCanvas.style.top = '0';
            clonedCanvas.style.left = '0';
            clonedCanvas.style.width = '100%';
            clonedCanvas.style.height = '100%';
            clonedCanvas.style.backfaceVisibility = 'hidden';
            
            const ctx = clonedCanvas.getContext('2d');
            ctx.drawImage(leftCanvas, 0, 0);
            
            flippingPage.appendChild(clonedCanvas);
            leftContainer.appendChild(flippingPage);
            
            // Render new pages underneath the animation
            renderPages(currentPage);
            
            setTimeout(() => flippingPage.remove(), delay);
          }
          
          setTimeout(animateFlip, delay);
        } else {
          // Smoothly transition to target page during final flip animation
          // Start one more flip animation, then change page mid-flip
          const container = isForward ? document.getElementById('rightPageContainer') : document.getElementById('leftPageContainer');
          const flippingPage = document.createElement('div');
          flippingPage.className = isForward ? 'flipping-page flip-forward' : 'flipping-page flip-backward';
          flippingPage.style.transformStyle = 'preserve-3d';
          flippingPage.style.animationDuration = '200ms';
          
          const canvas = isForward ? document.getElementById('rightPage') : document.getElementById('leftPage');
          const clonedCanvas = canvas.cloneNode(true);
          clonedCanvas.style.position = 'absolute';
          clonedCanvas.style.top = '0';
          clonedCanvas.style.left = '0';
          clonedCanvas.style.width = '100%';
          clonedCanvas.style.height = '100%';
          clonedCanvas.style.backfaceVisibility = 'hidden';
          
          const ctx = clonedCanvas.getContext('2d');
          ctx.drawImage(canvas, 0, 0);
          
          flippingPage.appendChild(clonedCanvas);
          container.appendChild(flippingPage);
          
          // Switch to target page mid-flip when page is perpendicular (not visible)
          setTimeout(() => {
            currentPage = targetPage % 2 === 1 ? targetPage : targetPage - 1;
            renderPages(currentPage);
          }, 100);
          
          setTimeout(() => flippingPage.remove(), 200);
        }
      };
      
      animateFlip();
    }
  };
}

