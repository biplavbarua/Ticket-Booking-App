/**
 * Py-Booking — Client-side JavaScript
 * Tab switching, city autocomplete, dynamic passenger fields, and micro-animations.
 */

document.addEventListener("DOMContentLoaded", () => {
  // ── Theme Toggle ──
  const themeBtn = document.getElementById("theme-toggle");
  if (themeBtn) {
    const updateIcon = () => {
      const isDark =
        document.documentElement.getAttribute("data-theme") !== "light";
      themeBtn.innerHTML = isDark
        ? '<i class="fa-solid fa-moon"></i>'
        : '<i class="fa-solid fa-sun"></i>';
    };
    updateIcon();
    themeBtn.addEventListener("click", () => {
      const current =
        document.documentElement.getAttribute("data-theme") || "dark";
      const next = current === "dark" ? "light" : "dark";
      document.documentElement.setAttribute("data-theme", next);
      localStorage.setItem("py-booking-theme", next);
      updateIcon();
    });
  }

  // ── Mobile Menu Toggle ──
  const mobileMenuBtn = document.getElementById("mobile-menu-btn");
  const mobileNav = document.getElementById("mobile-nav");

  if (mobileMenuBtn && mobileNav) {
    mobileMenuBtn.addEventListener("click", () => {
      const isOpen = !mobileNav.classList.contains("hidden");
      mobileNav.classList.toggle("hidden");
      mobileMenuBtn.innerHTML = isOpen
        ? '<i class="fa-solid fa-bars"></i>'
        : '<i class="fa-solid fa-xmark"></i>';
    });
  }

  // ── Tab Switching ──
  const tabs = document.querySelectorAll(".tab");
  const tabContents = document.querySelectorAll(".tab-content");

  tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      const target = tab.dataset.tab;

      // Deactivate all
      tabs.forEach((t) => t.classList.remove("active"));
      tabContents.forEach((tc) => {
        tc.classList.remove("active");
        // Remove 'required' from inputs in inactive tabs
        tc.querySelectorAll("input[name]").forEach((inp) => inp.removeAttribute("required"));
      });

      // Activate clicked
      tab.classList.add("active");
      const form = document.getElementById(`form-${target}`);
      if (form) {
        form.classList.add("active");
        // Restore 'required' on text/city inputs in the active form
        form.querySelectorAll("input[type='text'][name]").forEach((inp) => inp.setAttribute("required", ""));
        // Focus the first input in the active form
        const firstInput = form.querySelector("input");
        if (firstInput) firstInput.focus();
      }
    });
  });

  // ── City Autocomplete ──
  let debounceTimer = null;
  const autocompleteInputs = document.querySelectorAll(".city-autocomplete");

  autocompleteInputs.forEach((input) => {
    // Create dropdown container
    const wrapper = input.parentElement;
    wrapper.style.position = "relative";

    const dropdown = document.createElement("div");
    dropdown.className = "autocomplete-dropdown";
    wrapper.appendChild(dropdown);

    input.addEventListener("input", () => {
      const q = input.value.trim();
      if (q.length < 1) {
        dropdown.style.display = "none";
        return;
      }

      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => {
        fetch(`/api/cities?q=${encodeURIComponent(q)}`)
          .then((r) => r.json())
          .then((cities) => {
            if (!cities.length) {
              dropdown.style.display = "none";
              return;
            }
            dropdown.innerHTML = cities
              .map(
                (c) => `
              <div class="ac-item" data-city="${c.city}" data-code="${c.code}">
                <span class="ac-item-city">${c.city}</span>
                <span class="ac-item-code">${c.code}</span>
              </div>`,
              )
              .join("");
            dropdown.style.display = "block";

            // Click handler for items
            dropdown.querySelectorAll(".ac-item").forEach((item) => {
              item.addEventListener("mousedown", (e) => {
                e.preventDefault();
                input.value = item.dataset.city;
                dropdown.style.display = "none";
              });
            });
          })
          .catch(() => {
            dropdown.style.display = "none";
          });
      }, 200);
    });

    input.addEventListener("blur", () => {
      setTimeout(() => {
        dropdown.style.display = "none";
      }, 150);
    });

    input.addEventListener("focus", () => {
      if (input.value.trim().length >= 1 && dropdown.children.length > 0) {
        dropdown.style.display = "block";
      }
    });
  });

  // ── Dynamic "Add Passenger" Button ──
  const addBtn = document.getElementById("add-passenger-btn");
  const container = document.getElementById("passengers-container");

  if (addBtn && container) {
    let passengerCount = 1;

    addBtn.addEventListener("click", () => {
      passengerCount++;
      const row = document.createElement("div");
      row.className = "passenger-row";
      row.innerHTML = `
                <div class="form-group">
                    <label>Passenger ${passengerCount} Name</label>
                    <div style="display:flex;gap:8px">
                        <input type="text" name="passenger_names[]" required class="input"
                               placeholder="Full name">
                        <button type="button" class="btn btn--danger btn--sm remove-passenger"
                                title="Remove passenger">✕</button>
                    </div>
                </div>
            `;
      container.appendChild(row);

      // Focus the new input
      row.querySelector("input").focus();

      // Remove handler
      row.querySelector(".remove-passenger").addEventListener("click", () => {
        row.remove();
        // Re-number labels
        renumberPassengers();
      });
    });

    function renumberPassengers() {
      const rows = container.querySelectorAll(".passenger-row");
      rows.forEach((row, index) => {
        const label = row.querySelector("label");
        if (label) label.textContent = `Passenger ${index + 1} Name`;
      });
      passengerCount = rows.length;
    }
  }

  // ── Flash message auto-dismiss ──
  const flashes = document.querySelectorAll(".flash-msg");
  flashes.forEach((flash) => {
    setTimeout(() => {
      flash.style.opacity = "0";
      flash.style.transform = "translateY(-10px)";
      flash.style.transition = "all 0.3s ease";
      setTimeout(() => flash.remove(), 300);
    }, 6000);
  });

  // ── Smooth scroll for anchor links ──
  document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
    anchor.addEventListener("click", (e) => {
      e.preventDefault();
      const target = document.querySelector(anchor.getAttribute("href"));
      if (target) target.scrollIntoView({ behavior: "smooth" });
    });
  });

  // ── Set minimum date to today for date inputs ──
  const today = new Date().toISOString().split("T")[0];
  document.querySelectorAll('input[type="date"]').forEach((input) => {
    if (!input.value) {
      input.setAttribute("min", today);
    }
  });

  // ── Global Loading State for Forms and Actions ──
  const searchForms = document.querySelectorAll("form:not(.cancel-form)");
  const loader = document.getElementById("global-loader");
  const loaderText = document.getElementById("loader-text");

  searchForms.forEach((form) => {
    form.addEventListener("submit", () => {
      if (loader) {
        if (loaderText)
          loaderText.textContent = "Searching for the best prices...";
        loader.classList.remove("hidden");
      }
    });
  });

  // Show loader on Book/Select buttons
  const actionBtns = document.querySelectorAll("a.btn--primary[href]");
  actionBtns.forEach((btn) => {
    if (!btn.getAttribute("href").startsWith("#")) {
      btn.addEventListener("click", () => {
        if (loader) {
          if (loaderText) loaderText.textContent = "Processing...";
          loader.classList.remove("hidden");
        }
      });
    }
  });

  // ── Chatbot Widget ──
  const chatToggle = document.getElementById("chatbot-toggle");
  const chatPanel = document.getElementById("chatbot-panel");
  const chatClose = document.getElementById("chatbot-close");
  const chatInput = document.getElementById("chatbot-input");
  const chatSend = document.getElementById("chatbot-send");
  const chatMessages = document.getElementById("chatbot-messages");

  if (chatToggle && chatPanel) {
    chatToggle.addEventListener("click", () => {
      chatPanel.classList.toggle("hidden");
      if (!chatPanel.classList.contains("hidden") && chatInput) {
        chatInput.focus();
      }
    });

    if (chatClose) {
      chatClose.addEventListener("click", () =>
        chatPanel.classList.add("hidden"),
      );
    }

    const formatBotReply = (text) => {
      return text
        .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
        .replace(/\n/g, "<br>")
        .replace(/•/g, "&bull;");
    };

    const addMsg = (text, type) => {
      const div = document.createElement("div");
      div.className = `chat-msg chat-msg--${type}`;
      if (type === "bot") {
        div.innerHTML = formatBotReply(text);
      } else {
        div.textContent = text;
      }
      chatMessages.appendChild(div);
      chatMessages.scrollTop = chatMessages.scrollHeight;
    };

    const sendChat = () => {
      const msg = chatInput.value.trim();
      if (!msg) return;
      addMsg(msg, "user");
      chatInput.value = "";

      fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: msg }),
      })
        .then((r) => r.json())
        .then((data) => {
          addMsg(data.reply || "Sorry, something went wrong!", "bot");
        })
        .catch(() => {
          addMsg("Oops! Couldn't reach the assistant. Try again.", "bot");
        });
    };

    if (chatSend) chatSend.addEventListener("click", sendChat);
    if (chatInput) {
      chatInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter") sendChat();
      });
    }
  }

  // ── Fare Calendar ──
  const calSearch = document.getElementById("cal-search");
  const calGrid = document.getElementById("fare-calendar-grid");

  if (calSearch && calGrid) {
    // Set default month to current month
    const monthInput = document.getElementById("cal-month");
    if (monthInput && !monthInput.value) {
      const now = new Date();
      monthInput.value = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`;
    }

    calSearch.addEventListener("click", () => {
      const type = document.getElementById("cal-type").value;
      const origin = document.getElementById("cal-origin").value.trim();
      const dest = document.getElementById("cal-destination").value.trim();
      const month = document.getElementById("cal-month").value;

      if (!origin || !dest || !month) {
        calGrid.innerHTML =
          '<p style="color:var(--danger);text-align:center;padding:2rem">Please fill in all fields</p>';
        return;
      }

      calGrid.innerHTML =
        '<p style="color:var(--text-muted);text-align:center;padding:2rem">Loading fares...</p>';

      fetch(
        `/api/calendar?type=${type}&origin=${encodeURIComponent(origin)}&destination=${encodeURIComponent(dest)}&month=${month}`,
      )
        .then((r) => r.json())
        .then((data) => {
          if (data.error) {
            calGrid.innerHTML = `<p style="color:var(--danger);text-align:center;padding:2rem">${data.error}</p>`;
            return;
          }
          renderCalendar(data, type, origin, dest, month);
        })
        .catch(() => {
          calGrid.innerHTML =
            '<p style="color:var(--danger);text-align:center;padding:2rem">Failed to load fare data</p>';
        });
    });

    function renderCalendar(data, type, origin, dest, month) {
      const prices = {};
      data.days.forEach((d) => {
        prices[d.date] = d;
      });

      // Determine price range for color coding
      const allPrices = data.days.map((d) => d.min_price);
      const minP = Math.min(...allPrices);
      const maxP = Math.max(...allPrices);
      const mid = minP + (maxP - minP) * 0.5;

      const [year, mon] = month.split("-").map(Number);
      const firstDay = new Date(year, mon - 1, 1).getDay(); // 0=Sun
      const daysInMonth = new Date(year, mon, 0).getDate();

      const dayNames = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
      let html = '<div class="cal-grid">';

      // Header row
      dayNames.forEach((d) => {
        html += `<div class="cal-header-cell">${d}</div>`;
      });

      // Empty cells before first day
      for (let i = 0; i < firstDay; i++) {
        html += '<div class="cal-cell empty"></div>';
      }

      // Day cells
      for (let d = 1; d <= daysInMonth; d++) {
        const dateStr = `${year}-${String(mon).padStart(2, "0")}-${String(d).padStart(2, "0")}`;
        const info = prices[dateStr];
        const hasPrice = !!info;
        let priceHtml = "";

        if (hasPrice) {
          let cls = "mid";
          if (info.min_price <= minP + (maxP - minP) * 0.33) cls = "cheap";
          else if (info.min_price >= minP + (maxP - minP) * 0.66)
            cls = "pricey";
          priceHtml = `<div class="cal-price ${cls}">₹${info.min_price}</div>`;
        }

        const clickAttr = hasPrice
          ? ` onclick="window.location.href='/${type}s/search?origin=${encodeURIComponent(origin)}&destination=${encodeURIComponent(dest)}&date=${dateStr}'"`
          : "";

        html += `<div class="cal-cell ${hasPrice ? "has-price" : ""}"${clickAttr}>
          <div class="cal-day">${d}</div>
          ${priceHtml}
        </div>`;
      }

      html += "</div>";

      if (!data.days.length) {
        html = `<p style="color:var(--text-muted);text-align:center;padding:2rem">No fares found for this route and month. Try different dates!</p>`;
      }

      calGrid.innerHTML = html;
    }
  }
});
