/**
 * Py-Booking — Client-side JavaScript
 * Tab switching, city autocomplete, dynamic passenger fields, and micro-animations.
 */

document.addEventListener("DOMContentLoaded", () => {
  // ── Tab Switching ──
  const tabs = document.querySelectorAll(".tab");
  const tabContents = document.querySelectorAll(".tab-content");

  tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      const target = tab.dataset.tab;

      // Deactivate all
      tabs.forEach((t) => t.classList.remove("active"));
      tabContents.forEach((tc) => tc.classList.remove("active"));

      // Activate clicked
      tab.classList.add("active");
      const form = document.getElementById(`form-${target}`);
      if (form) {
        form.classList.add("active");
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
    dropdown.style.cssText = `
      position:absolute; top:100%; left:0; right:0; z-index:999;
      background:#1e293b; border:1px solid rgba(255,255,255,0.15);
      border-radius:8px; max-height:240px; overflow-y:auto;
      display:none; box-shadow:0 8px 32px rgba(0,0,0,0.4);
      margin-top:4px;
    `;
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
              <div class="ac-item" style="
                padding:10px 16px; cursor:pointer; display:flex;
                justify-content:space-between; align-items:center;
                border-bottom:1px solid rgba(255,255,255,0.06);
                transition:background 0.15s;
              " data-city="${c.city}" data-code="${c.code}">
                <span style="color:#e2e8f0;font-weight:500">${c.city}</span>
                <span style="color:#818cf8;font-size:0.8rem;font-weight:600;
                  background:rgba(99,102,241,0.15);padding:2px 8px;border-radius:4px">
                  ${c.code}
                </span>
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
              item.addEventListener("mouseenter", () => {
                item.style.background = "rgba(255,255,255,0.08)";
              });
              item.addEventListener("mouseleave", () => {
                item.style.background = "transparent";
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
});
