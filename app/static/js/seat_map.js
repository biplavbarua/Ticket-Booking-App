/**
 * seat_map.js — Interactive flat seat-map renderer
 *
 * Usage:
 *   SeatMap.init({ vehicleType, vehicleId, containerId, maxSeats, onSelectionChange })
 */
const SeatMap = (() => {
    let _config = {};
    let _selectedSeats = [];
    let _seatData = [];

    /* ────────── PUBLIC ────────── */

    function init(config) {
        _config = config;
        _selectedSeats = [];
        fetchSeats();
    }

    function getSelectedSeats() {
        return _selectedSeats.map(s => ({ id: s.id, label: s.seat_label }));
    }

    /* ────────── DATA ────────── */

    async function fetchSeats() {
        const container = document.getElementById(_config.containerId);
        container.innerHTML = '<div class="seat-loading"><div class="seat-loading-spinner"></div>Loading seat map…</div>';

        try {
            const res = await fetch(`/api/seats/${_config.vehicleType}/${_config.vehicleId}`);
            const data = await res.json();
            _seatData = data.seats;
            render();
        } catch (e) {
            container.innerHTML = '<p style="color:var(--text);text-align:center;padding:24px;">Could not load seat map.</p>';
        }
    }

    /* ────────── RENDER ROUTER ────────── */

    function render() {
        const container = document.getElementById(_config.containerId);
        container.innerHTML = '';

        switch (_config.vehicleType) {
            case 'flight': renderFlight(container); break;
            case 'bus': renderBus(container); break;
            case 'train': renderTrain(container); break;
        }

        // Add legend
        const legend = document.createElement('div');
        legend.className = 'seat-legend';
        legend.innerHTML = `
      <span><span class="seat-swatch available"></span> Available</span>
      <span><span class="seat-swatch selected"></span> Selected</span>
      <span><span class="seat-swatch booked"></span> Booked</span>
    `;
        container.appendChild(legend);
    }

    /* ────────── FLIGHT ────────── */

    function renderFlight(container) {
        const wrapper = document.createElement('div');
        wrapper.className = 'seat-perspective-wrapper';

        const vehicle = document.createElement('div');
        vehicle.className = 'seat-vehicle flight-body';

        // — Cockpit nose (fixed, outside scroll)
        const nose = document.createElement('div');
        nose.className = 'flight-nose';
        nose.innerHTML = `<div class="flight-nose-inner">
      <i class="fa-solid fa-plane" style="font-size:20px;color:#6366f1;"></i>
      <span style="font-size:10px;opacity:.7;margin-top:2px;">COCKPIT</span>
    </div>`;
        vehicle.appendChild(nose);

        // — Scrollable seat area
        const scrollArea = document.createElement('div');
        scrollArea.className = 'seat-scroll-area';

        const grid = document.createElement('div');
        grid.className = 'seat-grid flight-grid';

        // Column headers
        const cols = ['A', 'B', 'C', '', 'D', 'E', 'F'];
        const headerRow = document.createElement('div');
        headerRow.className = 'seat-row seat-header-row';
        cols.forEach(c => {
            const cell = document.createElement('div');
            cell.className = c === '' ? 'seat-aisle' : 'seat-col-label';
            cell.textContent = c;
            headerRow.appendChild(cell);
        });
        grid.appendChild(headerRow);

        // Group seats by row
        const rows = groupByRow(_seatData);
        const rowNums = Object.keys(rows).sort((a, b) => a - b);

        rowNums.forEach(rowNum => {
            const rowEl = document.createElement('div');
            rowEl.className = 'seat-row';

            // Row number label
            const rowLabel = document.createElement('div');
            rowLabel.className = 'seat-row-label';
            rowLabel.textContent = rowNum;
            rowEl.appendChild(rowLabel);

            const rowSeats = rows[rowNum];
            for (let c = 0; c < 6; c++) {
                if (c === 3) {
                    const aisle = document.createElement('div');
                    aisle.className = 'seat-aisle';
                    rowEl.appendChild(aisle);
                }
                const seat = rowSeats.find(s => s.col === c);
                if (seat) {
                    rowEl.appendChild(createSeatEl(seat));
                } else {
                    const empty = document.createElement('div');
                    empty.className = 'seat empty';
                    rowEl.appendChild(empty);
                }
            }
            grid.appendChild(rowEl);
        });

        scrollArea.appendChild(grid);
        vehicle.appendChild(scrollArea);

        // — Tail (fixed, outside scroll)
        const tail = document.createElement('div');
        tail.className = 'flight-tail';
        vehicle.appendChild(tail);

        wrapper.appendChild(vehicle);
        container.appendChild(wrapper);
    }

    /* ────────── BUS ────────── */

    function renderBus(container) {
        const wrapper = document.createElement('div');
        wrapper.className = 'seat-perspective-wrapper';

        const vehicle = document.createElement('div');
        vehicle.className = 'seat-vehicle bus-body';

        // Driver cabin (fixed)
        const driver = document.createElement('div');
        driver.className = 'bus-driver';
        driver.innerHTML = `<div class="bus-driver-inner">
      <i class="fa-solid fa-bus" style="font-size:18px;color:#6366f1;"></i>
      <span style="font-size:9px;opacity:.7;">DRIVER</span>
    </div>
    <div class="bus-steering"><i class="fa-solid fa-circle-notch" style="font-size:20px;color:#444;"></i></div>`;
        vehicle.appendChild(driver);

        // Door
        const door = document.createElement('div');
        door.className = 'bus-door';
        door.innerHTML = '<span>DOOR</span>';
        vehicle.appendChild(door);

        // Scrollable seat area
        const scrollArea = document.createElement('div');
        scrollArea.className = 'seat-scroll-area';

        const grid = document.createElement('div');
        grid.className = 'seat-grid bus-grid';

        // Column headers
        const cols = ['W', 'A', '', 'B', 'W'];
        const headerRow = document.createElement('div');
        headerRow.className = 'seat-row seat-header-row';
        cols.forEach(c => {
            const cell = document.createElement('div');
            cell.className = c === '' ? 'seat-aisle' : 'seat-col-label';
            cell.textContent = c;
            headerRow.appendChild(cell);
        });
        grid.appendChild(headerRow);

        // Group seats by row
        const rows = groupByRow(_seatData);
        const rowNums = Object.keys(rows).sort((a, b) => a - b);

        rowNums.forEach(rowNum => {
            const rowEl = document.createElement('div');
            rowEl.className = 'seat-row';

            const rowSeats = rows[rowNum];
            for (let c = 0; c < 4; c++) {
                if (c === 2) {
                    const aisle = document.createElement('div');
                    aisle.className = 'seat-aisle';
                    rowEl.appendChild(aisle);
                }
                const seat = rowSeats.find(s => s.col === c);
                if (seat) {
                    rowEl.appendChild(createSeatEl(seat));
                } else {
                    const empty = document.createElement('div');
                    empty.className = 'seat empty';
                    rowEl.appendChild(empty);
                }
            }
            grid.appendChild(rowEl);
        });

        scrollArea.appendChild(grid);
        vehicle.appendChild(scrollArea);

        // Rear (fixed)
        const rear = document.createElement('div');
        rear.className = 'bus-rear';
        vehicle.appendChild(rear);

        wrapper.appendChild(vehicle);
        container.appendChild(wrapper);
    }

    /* ────────── TRAIN ────────── */

    function renderTrain(container) {
        const wrapper = document.createElement('div');
        wrapper.className = 'seat-perspective-wrapper';

        const vehicle = document.createElement('div');
        vehicle.className = 'seat-vehicle train-body';

        // Engine (fixed, outside scroll)
        const engine = document.createElement('div');
        engine.className = 'train-engine';
        engine.innerHTML = `<div class="train-engine-inner">
      <i class="fa-solid fa-train" style="font-size:18px;color:#6366f1;"></i>
      <span style="font-size:9px;opacity:.7;">COACH</span>
    </div>`;
        vehicle.appendChild(engine);

        // Scrollable compartment area
        const scrollArea = document.createElement('div');
        scrollArea.className = 'seat-scroll-area';

        // Group by compartments
        const rows = groupByRow(_seatData);
        const rowNums = Object.keys(rows).sort((a, b) => a - b);

        rowNums.forEach((rowNum) => {
            const compartment = document.createElement('div');
            compartment.className = 'train-compartment';

            const compLabel = document.createElement('div');
            compLabel.className = 'train-comp-label';
            compLabel.textContent = `Bay ${parseInt(rowNum)}`;
            compartment.appendChild(compLabel);

            const berthGrid = document.createElement('div');
            berthGrid.className = 'train-berth-grid';

            const rowSeats = rows[rowNum];

            // Main berths (cols 0-5): 2 columns × 3 tiers
            const mainSection = document.createElement('div');
            mainSection.className = 'train-main-berths';
            for (let tier = 2; tier >= 0; tier--) { // UB, MB, LB (top-down)
                const tierRow = document.createElement('div');
                tierRow.className = 'train-tier-row';
                for (let side = 0; side < 2; side++) {
                    const col = side * 3 + tier;
                    const seat = rowSeats.find(s => s.col === col);
                    if (seat) {
                        const el = createSeatEl(seat, true);
                        tierRow.appendChild(el);
                    }
                }
                mainSection.appendChild(tierRow);
            }
            berthGrid.appendChild(mainSection);

            // Aisle
            const aisle = document.createElement('div');
            aisle.className = 'train-aisle';
            berthGrid.appendChild(aisle);

            // Side berths (cols 6-7)
            const sideSection = document.createElement('div');
            sideSection.className = 'train-side-berths';
            for (let col = 7; col >= 6; col--) {
                const seat = rowSeats.find(s => s.col === col);
                if (seat) {
                    sideSection.appendChild(createSeatEl(seat, true));
                }
            }
            berthGrid.appendChild(sideSection);

            compartment.appendChild(berthGrid);
            scrollArea.appendChild(compartment);
        });

        vehicle.appendChild(scrollArea);

        wrapper.appendChild(vehicle);
        container.appendChild(wrapper);
    }

    /* ────────── SEAT ELEMENT ────────── */

    function createSeatEl(seat, isBerth = false) {
        const el = document.createElement('div');
        el.className = `seat ${seat.is_booked ? 'booked' : 'available'}${isBerth ? ' berth' : ''}`;
        el.dataset.seatId = seat.id;
        el.dataset.seatLabel = seat.seat_label;

        el.innerHTML = `<span class="seat-label">${seat.seat_label}</span>`;

        if (!seat.is_booked) {
            el.addEventListener('click', () => toggleSeat(el, seat));
            el.title = `Seat ${seat.seat_label} — Click to select`;
        } else {
            el.title = `Seat ${seat.seat_label} — Booked`;
        }

        return el;
    }

    /* ────────── SELECTION LOGIC ────────── */

    function toggleSeat(el, seat) {
        const idx = _selectedSeats.findIndex(s => s.id === seat.id);

        if (idx !== -1) {
            // Deselect
            _selectedSeats.splice(idx, 1);
            el.classList.remove('selected');
            el.classList.add('available');
        } else {
            // Check max
            if (_selectedSeats.length >= _config.maxSeats) {
                showToast(`Maximum ${_config.maxSeats} seat(s) allowed`);
                return;
            }
            _selectedSeats.push(seat);
            el.classList.remove('available');
            el.classList.add('selected');
        }

        // Update hidden inputs
        syncHiddenInputs();

        // Notify parent
        if (_config.onSelectionChange) {
            _config.onSelectionChange(_selectedSeats);
        }
    }

    function syncHiddenInputs() {
        // Remove old hidden inputs
        document.querySelectorAll('input[name="seat_ids[]"]').forEach(i => i.remove());

        const form = document.getElementById('bookingForm');
        if (!form) return;

        _selectedSeats.forEach(seat => {
            const input = document.createElement('input');
            input.type = 'hidden';
            input.name = 'seat_ids[]';
            input.value = seat.id;
            form.appendChild(input);
        });
    }

    /* ────────── HELPERS ────────── */

    function groupByRow(seats) {
        const groups = {};
        seats.forEach(s => {
            if (!groups[s.row]) groups[s.row] = [];
            groups[s.row].push(s);
        });
        return groups;
    }

    function showToast(msg) {
        let toast = document.getElementById('seat-toast');
        if (!toast) {
            toast = document.createElement('div');
            toast.id = 'seat-toast';
            toast.className = 'seat-toast';
            document.body.appendChild(toast);
        }
        toast.textContent = msg;
        toast.classList.add('show');
        setTimeout(() => toast.classList.remove('show'), 2500);
    }

    /* ────────── PUBLIC API ────────── */

    return { init, getSelectedSeats };
})();
