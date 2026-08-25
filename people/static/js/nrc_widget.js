// NRC composition widget powered by the myanmar-nrc-x format.
// Builds an NRC string: [State]/[District](N)[6-digit number]
(function () {
  "use strict";

  function buildOptions(select, items, placeholder) {
    select.innerHTML = "";
    const ph = document.createElement("option");
    ph.value = "";
    ph.textContent = placeholder;
    ph.disabled = true;
    ph.selected = true;
    select.appendChild(ph);
    items.forEach(function (it) {
      const opt = document.createElement("option");
      opt.value = it.value;
      opt.textContent = it.label;
      select.appendChild(opt);
    });
  }

  function initNrcWidget(root) {
    if (!root || root.dataset.nrcBound) return;
    root.dataset.nrcBound = "1";

    const stateSel = root.querySelector("[data-nrc-state]");
    const districtSel = root.querySelector("[data-nrc-district]");
    const numberInput = root.querySelector("[data-nrc-number]");
    const hidden = root.querySelector("[data-nrc-hidden]");
    const scope = root.closest(".form-control") || root;
    const preview = scope.querySelector("[data-nrc-preview]");
    const errorEl = scope.querySelector("[data-nrc-error]");

    const states = window.NRC_STATES || [];
    const districts = window.NRC_DISTRICTS || {};

    const initState = root.dataset.state || "";
    const initDistrict = root.dataset.district || "";
    const initNumber = root.dataset.number || "";

    buildOptions(
      stateSel,
      states.map(function (s) {
        return { value: s.num, label: s.num + " - " + s.en };
      }),
      "State"
    );

    function refreshDistricts() {
      const code = stateSel.value;
      const list = (districts[code] || []).map(function (d) {
        const mm = d.mm ? " (" + d.mm + ")" : "";
        return { value: d.en, label: d.en + mm + " - " + d.name };
      });
      buildOptions(districtSel, list, "District");
      districtSel.disabled = !code;
    }

    function update() {
      const state = stateSel.value;
      const district = districtSel.value;
      const number = (numberInput.value || "").trim();
      let value = "";
      if (state && district && /^\d{6}$/.test(number)) {
        value = state + "/" + district + "(N)" + number;
      }
      hidden.value = value;
      if (preview) {
        preview.textContent = value || "—";
      }
      if (errorEl) errorEl.classList.add("hidden");
    }

    stateSel.addEventListener("change", function () {
      districtSel.value = "";
      refreshDistricts();
      update();
    });
    districtSel.addEventListener("change", update);
    numberInput.addEventListener("input", function () {
      this.value = this.value.replace(/\D/g, "").slice(0, 6);
      update();
    });

    // Prefill from data attributes (edit / validation error restore)
    if (initState) stateSel.value = initState;
    refreshDistricts();
    if (initDistrict) districtSel.value = initDistrict;
    if (initNumber) numberInput.value = initNumber;
    update();

    const form = root.closest("form");
    if (form) {
      form.addEventListener("submit", function (e) {
        const state = stateSel.value;
        const district = districtSel.value;
        const number = (numberInput.value || "").trim();
        if (!state || !district || !/^\d{6}$/.test(number)) {
          e.preventDefault();
          if (errorEl) {
            errorEl.textContent =
              "Please select state, district and enter a 6-digit registration number.";
            errorEl.classList.remove("hidden");
          }
          return;
        }
        hidden.value = state + "/" + district + "(N)" + number;
      });
    }
  }

  document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll("[data-nrc-widget]").forEach(initNrcWidget);
  });

  window.initNrcWidget = initNrcWidget;
})();
