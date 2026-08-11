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

  const therapistHint = document.getElementById("booking-therapist-hint");

  // Прод-API, когда лендинг и FastAPI на разных хостах (Railway).
  // Локально при data-api-base="auto" не используется.
  const PROD_API_BASE =
    "https://industrious-exploration-production-512f.up.railway.app";
  const PROD_HOSTS = new Set(["mrboka.com", "www.mrboka.com"]);

  function resolveApiBase() {
    const raw = (document.body.getAttribute("data-api-base") || "auto").trim();
    if (raw && raw !== "auto") {
      return raw.replace(/\/$/, "");
    }
    // auto: localhost → uvicorn :8000; известный прод-хост → PROD_API_BASE; иначе same-origin
    const host = window.location.hostname;
    const isLocal =
      host === "localhost" ||
      host === "127.0.0.1" ||
      host === "[::1]" ||
      host === "";
    if (isLocal) return "http://127.0.0.1:8000";
    if (PROD_HOSTS.has(host)) return PROD_API_BASE;
    return "";
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

  function toISODate(d) {
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, "0");
    const day = String(d.getDate()).padStart(2, "0");
    return `${y}-${m}-${day}`;
  }

  function todayISO() {
    return toISODate(new Date());
  }

  /** Локальный день недели для YYYY-MM-DD (0=вс … 6=сб). */
  function weekdayOfISO(iso) {
    const d = new Date(`${iso}T12:00:00`);
    return d.getDay();
  }

  function isWeekendISO(iso) {
    const day = weekdayOfISO(iso);
    return day === 0 || day === 6;
  }

  /** Ближайший будний день (пн–пт) начиная с сегодня. */
  function nextOpenDayISO() {
    const d = new Date();
    for (let i = 0; i < 8; i += 1) {
      const iso = toISODate(d);
      if (!isWeekendISO(iso)) return iso;
      d.setDate(d.getDate() + 1);
    }
    return todayISO();
  }

  function formatPriceSek(value) {
    const n = Number(value);
    if (Number.isNaN(n)) return "";
    return `${n.toLocaleString("sv-SE")} kr`;
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

  /** Группа в списке услуг: Alfa / Monicor / EIS / Paket */
  function serviceGroupLabel(name) {
    const n = String(name || "").toLowerCase();
    if (n.includes("paket")) return "Paket";
    if (n.includes("eis")) return "EIS";
    if (n.includes("monicor")) return "Monicor";
    if (n.includes("alfa")) return "Alfa";
    return "Övrigt";
  }

  const SERVICE_GROUP_ORDER = ["Alfa", "Monicor", "EIS", "Paket", "Övrigt"];

  function fillServicesGrouped(select, services) {
    const placeholder = document.createElement("option");
    placeholder.value = "";
    placeholder.textContent = "Välj undersökning…";
    select.innerHTML = "";
    select.appendChild(placeholder);

    const groups = new Map();
    for (const svc of services) {
      const key = serviceGroupLabel(svc.name);
      if (!groups.has(key)) groups.set(key, []);
      groups.get(key).push(svc);
    }

    for (const key of SERVICE_GROUP_ORDER) {
      const items = groups.get(key);
      if (!items || items.length === 0) continue;
      const optgroup = document.createElement("optgroup");
      optgroup.label = key;
      for (const svc of items) {
        const opt = document.createElement("option");
        opt.value = String(svc.id);
        opt.textContent = `${svc.name} — ${svc.duration_minutes} min · ${formatPriceSek(svc.price)}`;
        optgroup.appendChild(opt);
      }
      select.appendChild(optgroup);
    }
  }

  function setTherapistHint(message) {
    if (!therapistHint) return;
    if (!message) {
      therapistHint.hidden = true;
      therapistHint.textContent = "";
      return;
    }
    therapistHint.hidden = false;
    therapistHint.textContent = message;
  }

  async function loadServices() {
    // Всегда сбрасываем плейсхолдер (старый кэш мог писать «Välj behandlare först»)
    serviceSelect.disabled = true;
    fillServicesGrouped(serviceSelect, []);
    const services = await fetchJson("/api/services");
    fillServicesGrouped(serviceSelect, services);
    serviceSelect.disabled = false;
    if (!services.length) {
      serviceSelect.options[0].textContent = "Inga tjänster tillgängliga";
      showError(
        "Inga bokningsbara tjänster just nu. Kontrollera att seed körts på API."
      );
    }
  }

  async function loadTherapists() {
    const serviceId = serviceSelect.value;
    const placeholder = document.createElement("option");
    placeholder.value = "";
    therapistSelect.innerHTML = "";
    therapistSelect.appendChild(placeholder);

    if (!serviceId) {
      placeholder.textContent = "Välj tjänst först…";
      therapistSelect.disabled = true;
      setTherapistHint("");
      return;
    }

    placeholder.textContent = "Laddar behandlare…";
    therapistSelect.disabled = true;

    const therapists = await fetchJson(
      `/api/therapists?service_id=${encodeURIComponent(serviceId)}`
    );

    therapistSelect.innerHTML = "";
    const choose = document.createElement("option");
    choose.value = "";
    choose.textContent =
      therapists.length === 0 ? "Ingen behandlare för denna tjänst" : "Välj behandlare…";
    therapistSelect.appendChild(choose);

    fillSelect(therapistSelect, therapists, (t) => ({
      value: String(t.id),
      label: `${t.name} — ${t.specialization}`,
    }));

    if (therapists.length === 0) {
      therapistSelect.disabled = true;
      setTherapistHint(
        "Den här undersökningen kan just nu bara bokas med en annan tjänst eller kontakta oss."
      );
      return;
    }

    therapistSelect.disabled = false;

    // Один terapeut (t.ex. EIS → bara Viktoria): välj automatiskt
    if (therapists.length === 1) {
      therapistSelect.value = String(therapists[0].id);
      setTherapistHint(
        `${therapists[0].name} tar emot den här undersökningen.`
      );
    } else {
      setTherapistHint(
        "Välj behandlare: Iwona (Monicor & Alfa) eller Viktoria (Monicor, Alfa & EIS)."
      );
    }
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
    dateInput.value = nextOpenDayISO();

    showStatus("Laddar formulär…");
    try {
      await loadServices();
      await loadTherapists();
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

  serviceSelect.addEventListener("change", async () => {
    try {
      await loadTherapists();
      await loadSlots();
    } catch (err) {
      showError("Kunde inte ladda behandlare för vald tjänst.");
      console.error(err);
    }
  });

  therapistSelect.addEventListener("change", () => {
    loadSlots();
  });

  dateInput.addEventListener("change", () => {
    if (dateInput.value && isWeekendISO(dateInput.value)) {
      showError("Bokning endast måndag–fredag (lördag/söndag stängt).");
      dateInput.value = nextOpenDayISO();
    } else {
      showError("");
    }
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

  againBtn.addEventListener("click", async () => {
    successPanel.hidden = true;
    formPanel.hidden = false;
    form.reset();
    dateInput.min = todayISO();
    dateInput.value = nextOpenDayISO();
    showError("");
    showStatus("");
    try {
      await loadServices();
      await loadTherapists();
      await loadSlots();
    } catch (err) {
      console.error(err);
    }
  });

  function initTelegramBookingLink() {
    const link = document.getElementById("booking-via-telegram");
    if (!link) return;
    const raw = (document.body.getAttribute("data-bot-username") || "mr_bokning_bot").trim();
    const username = raw.replace(/^@/, "");
    if (username) {
      link.href = `https://t.me/${username}`;
    }
  }

  initTelegramBookingLink();
  init();
})();
