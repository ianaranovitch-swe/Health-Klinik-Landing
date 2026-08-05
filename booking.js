/**
 * Форма бронирования на лендинге (этап 3).
 * Тянет терапевтов / услуги / слоты из FastAPI и создаёт запись через POST /api/bookings.
 */
(function () {
  "use strict";

  const formPanel = document.getElementById("booking-form-panel");
  const form = document.getElementById("booking-form");
  const successPanel = document.getElementById("booking-success");
  if (!form || !formPanel || !successPanel) return;

  const therapistSelect = document.getElementById("booking-therapist");
  const serviceSelect = document.getElementById("booking-service");
  const dateInput = document.getElementById("booking-date");
  const timeSelect = document.getElementById("booking-time");
  const nameInput = document.getElementById("booking-name");
  const phoneInput = document.getElementById("booking-phone");
  const emailInput = document.getElementById("booking-email");
  const errorEl = document.getElementById("booking-error");
  const statusEl = document.getElementById("booking-status");
  const submitBtn = document.getElementById("booking-submit");
  const successSummary = document.getElementById("booking-success-summary");
  const telegramLink = document.getElementById("booking-telegram-link");
  const againBtn = document.getElementById("booking-again");

  function resolveApiBase() {
    const raw = (document.body.getAttribute("data-api-base") || "auto").trim();
    if (raw && raw !== "auto") {
      return raw.replace(/\/$/, "");
    }
    // auto: локальная разработка → uvicorn на :8000; прод → same-origin
    const host = window.location.hostname;
    const isLocal =
      host === "localhost" ||
      host === "127.0.0.1" ||
      host === "[::1]" ||
      host === "";
    return isLocal ? "http://127.0.0.1:8000" : "";
  }

  const apiBase = resolveApiBase();

  function apiUrl(path) {
    return `${apiBase}${path}`;
  }

  function showError(message) {
    errorEl.hidden = !message;
    errorEl.textContent = message || "";
  }

  function showStatus(message) {
    statusEl.hidden = !message;
    statusEl.textContent = message || "";
  }

  function todayISO() {
    const d = new Date();
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, "0");
    const day = String(d.getDate()).padStart(2, "0");
    return `${y}-${m}-${day}`;
  }

  function formatTimeForApi(slot) {
    // API ждёт HH:MM:SS; слоты приходят как HH:MM
    return slot.length === 5 ? `${slot}:00` : slot;
  }

  async function fetchJson(path) {
    const response = await fetch(apiUrl(path), {
      headers: { Accept: "application/json" },
    });
    if (!response.ok) {
      const text = await response.text();
      throw new Error(text || `HTTP ${response.status}`);
    }
    return response.json();
  }

  function fillSelect(select, items, mapOption) {
    const first = select.options[0];
    select.innerHTML = "";
    if (first) select.appendChild(first);
    for (const item of items) {
      const opt = document.createElement("option");
      const { value, label } = mapOption(item);
      opt.value = value;
      opt.textContent = label;
      select.appendChild(opt);
    }
  }

  async function loadTherapists() {
    const therapists = await fetchJson("/api/therapists");
    fillSelect(therapistSelect, therapists, (t) => ({
      value: String(t.id),
      label: `${t.name} — ${t.specialization}`,
    }));
  }

  async function loadServices() {
    const services = await fetchJson("/api/services");
    fillSelect(serviceSelect, services, (s) => ({
      value: String(s.id),
      label: `${s.name} (${s.duration_minutes} min)`,
    }));
  }

  async function loadSlots() {
    const therapistId = therapistSelect.value;
    const date = dateInput.value;
    timeSelect.innerHTML = "";
    timeSelect.disabled = true;

    if (!therapistId || !date) {
      const opt = document.createElement("option");
      opt.value = "";
      opt.textContent = "Välj behandlare och datum…";
      timeSelect.appendChild(opt);
      return;
    }

    const placeholder = document.createElement("option");
    placeholder.value = "";
    placeholder.textContent = "Laddar tider…";
    timeSelect.appendChild(placeholder);

    try {
      const data = await fetchJson(
        `/api/availability?therapist_id=${encodeURIComponent(therapistId)}&date=${encodeURIComponent(date)}`
      );
      timeSelect.innerHTML = "";
      const choose = document.createElement("option");
      choose.value = "";
      choose.textContent = "Välj tid…";
      timeSelect.appendChild(choose);

      const slots = data.slots || [];
      if (slots.length === 0) {
        choose.textContent = "Inga tider lediga";
        return;
      }

      for (const slot of slots) {
        const opt = document.createElement("option");
        opt.value = slot;
        opt.textContent = slot;
        timeSelect.appendChild(opt);
      }
      timeSelect.disabled = false;
      showError("");
    } catch (err) {
      timeSelect.innerHTML = "";
      const opt = document.createElement("option");
      opt.value = "";
      opt.textContent = "Kunde inte ladda tider";
      timeSelect.appendChild(opt);
      showError("Kunde inte hämta lediga tider. Kontrollera att API:t körs.");
      console.error(err);
    }
  }

  async function init() {
    dateInput.min = todayISO();
    if (!dateInput.value) dateInput.value = todayISO();

    showStatus("Laddar formulär…");
    try {
      await Promise.all([loadTherapists(), loadServices()]);
      showStatus("");
      await loadSlots();
    } catch (err) {
      showStatus("");
      showError(
        "Kunde inte ansluta till boknings-API:t. Starta backend (uvicorn) och kontrollera data-api-base."
      );
      console.error(err);
    }
  }

  therapistSelect.addEventListener("change", () => {
    loadSlots();
  });
  dateInput.addEventListener("change", () => {
    loadSlots();
  });

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    showError("");
    showStatus("");

    // disabled+required у #booking-time не участвует в HTML-валидации —
    // проверяем время отдельно, пока слоты не загружены или не выбраны
    if (timeSelect.disabled || !timeSelect.value.trim()) {
      showError("Välj en ledig tid innan du bokar.");
      timeSelect.focus();
      return;
    }

    if (!form.checkValidity()) {
      form.reportValidity();
      return;
    }

    const payload = {
      name: nameInput.value.trim(),
      phone: phoneInput.value.trim(),
      email: emailInput.value.trim(),
      therapist_id: Number(therapistSelect.value),
      service_id: Number(serviceSelect.value),
      date: dateInput.value,
      time: formatTimeForApi(timeSelect.value),
    };

    submitBtn.disabled = true;
    showStatus("Skickar bokning…");

    try {
      const response = await fetch(apiUrl("/api/bookings"), {
        method: "POST",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      let data = null;
      try {
        data = await response.json();
      } catch {
        data = null;
      }

      if (!response.ok) {
        const detail =
          (data && (data.detail || data.message)) ||
          `HTTP ${response.status}`;
        const message =
          typeof detail === "string" ? detail : JSON.stringify(detail);
        throw new Error(message);
      }

      if (
        !data ||
        typeof data !== "object" ||
        !data.service_name ||
        !data.therapist_name ||
        !data.date ||
        !data.time ||
        !data.telegram_deep_link
      ) {
        throw new Error(
          "Ogiltigt svar från servern. Bokningen kan ha sparats — kontrollera eller försök igen."
        );
      }

      const timeLabel = String(data.time).slice(0, 5);
      formPanel.hidden = true;
      successPanel.hidden = false;
      successSummary.textContent = `${data.service_name} med ${data.therapist_name}, ${data.date} kl. ${timeLabel}.`;
      telegramLink.href = data.telegram_deep_link;
      showStatus("");
      successPanel.scrollIntoView({ behavior: "smooth", block: "start" });
    } catch (err) {
      showStatus("");
      showError(err.message || "Något gick fel. Försök igen.");
      console.error(err);
    } finally {
      submitBtn.disabled = false;
    }
  });

  againBtn.addEventListener("click", () => {
    successPanel.hidden = true;
    formPanel.hidden = false;
    form.reset();
    dateInput.min = todayISO();
    dateInput.value = todayISO();
    showError("");
    showStatus("");
    loadSlots();
  });

  init();
})();
