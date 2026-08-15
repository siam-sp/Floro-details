document.addEventListener("DOMContentLoaded", function () {
  const form = document.getElementById("booking-form");
  if (!form) return;

  const serviceInputs = document.querySelectorAll('input[name="service_choice"]');
  const serviceHidden = document.getElementById("id_service");
  const dateChips = document.querySelectorAll(".date-chip");
  const dateHidden = document.getElementById("id_date");
  const startTimeHidden = document.getElementById("id_start_time");
  const slotsContainer = document.getElementById("slots");
  const summaryEl = document.getElementById("booking-summary");

  const progressSteps = document.querySelectorAll(".progress-step");
  const panels = document.querySelectorAll(".wizard-panel");
  const backBtn = document.getElementById("wizard-back");
  const nextBtn = document.getElementById("wizard-next");
  const submitBtn = document.getElementById("wizard-submit");

  const emailInput = document.querySelector('[name="customer_email"]');
  const sendCodeBtn = document.getElementById("send-code-btn");
  const verifyCodeRow = document.getElementById("verify-code-row");
  const verifyCodeInput = document.getElementById("verify-code-input");
  const verifyCodeBtn = document.getElementById("verify-code-btn");
  const verifyMessage = document.getElementById("verify-message");

  const TOTAL_STEPS = panels.length;
  const RESEND_COOLDOWN_SECONDS = 45;
  let currentStep = 1;
  let emailVerified = false;
  let verifiedEmail = null;
  let resendInterval = null;

  function getCsrfToken() {
    return form.querySelector("[name=csrfmiddlewaretoken]").value;
  }

  function getSelectedServiceOption() {
    const checked = document.querySelector('input[name="service_choice"]:checked');
    if (!checked) return null;
    return {
      slug: checked.dataset.slug,
      name: checked.dataset.name,
      price: checked.dataset.price,
    };
  }

  function updateServiceHidden() {
    const checked = document.querySelector('input[name="service_choice"]:checked');
    if (checked) {
      serviceHidden.value = checked.value;
    }
    serviceInputs.forEach((input) => {
      input.closest(".service-option").classList.toggle("selected", input.checked);
    });
  }

  function resetSlotSelection() {
    startTimeHidden.value = "";
  }

  function renderSlots(slots) {
    slotsContainer.innerHTML = "";
    if (!slots.length) {
      slotsContainer.innerHTML = '<p class="muted">Ingen ledige tider denne dagen. Prøv en annen dato.</p>';
      return;
    }
    slots.forEach((slot) => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "slot-btn" + (slot.available ? "" : " unavailable");
      btn.textContent = slot.time;
      if (!slot.available) {
        btn.disabled = true;
      } else {
        btn.addEventListener("click", () => {
          document.querySelectorAll(".slot-btn").forEach((b) => b.classList.remove("selected"));
          btn.classList.add("selected");
          startTimeHidden.value = slot.time;
          updateNextState();
        });
      }
      slotsContainer.appendChild(btn);
    });
  }

  function fetchSlots() {
    const checked = document.querySelector('input[name="service_choice"]:checked');
    const slug = checked ? checked.dataset.slug : null;
    const date = dateHidden.value;
    resetSlotSelection();

    if (!slug || !date) {
      slotsContainer.innerHTML = '<p class="muted">Velg tjeneste og dato for å se ledige tider.</p>';
      return;
    }

    slotsContainer.innerHTML = '<p class="muted">Laster ledige tider…</p>';

    fetch(`/book/ledige-tider/?service=${encodeURIComponent(slug)}&date=${encodeURIComponent(date)}`)
      .then((res) => res.json())
      .then((data) => renderSlots(data.slots || []))
      .catch(() => {
        slotsContainer.innerHTML = '<p class="muted">Kunne ikke hente ledige tider. Prøv igjen.</p>';
      });
  }

  function renderSummary() {
    const service = getSelectedServiceOption();
    const dateObj = dateHidden.value ? new Date(dateHidden.value + "T00:00:00") : null;
    const dateLabel = dateObj
      ? dateObj.toLocaleDateString("nb-NO", { weekday: "long", day: "numeric", month: "long" })
      : "";
    summaryEl.innerHTML = `
      <div class="summary-row"><span>Tjeneste</span><strong>${service ? service.name : ""}</strong></div>
      <div class="summary-row"><span>Dato</span><strong>${dateLabel}</strong></div>
      <div class="summary-row"><span>Tid</span><strong>${startTimeHidden.value}</strong></div>
      <div class="summary-row"><span>Å betale på stedet</span><strong>${service ? service.price : ""} kr</strong></div>
    `;
  }

  function isStepValid(step) {
    if (step === 1) return !!document.querySelector('input[name="service_choice"]:checked');
    if (step === 2) return !!dateHidden.value;
    if (step === 3) return !!startTimeHidden.value;
    return true;
  }

  function updateNextState() {
    nextBtn.disabled = !isStepValid(currentStep);
  }

  function showStep(step) {
    currentStep = step;
    panels.forEach((panel) => {
      panel.classList.toggle("active", Number(panel.dataset.panel) === step);
    });
    progressSteps.forEach((el) => {
      const stepNum = Number(el.dataset.step);
      el.classList.toggle("active", stepNum === step);
      el.classList.toggle("completed", stepNum < step);
    });
    backBtn.hidden = step === 1;
    nextBtn.hidden = step === TOTAL_STEPS;
    submitBtn.hidden = step !== TOTAL_STEPS;
    if (step === TOTAL_STEPS) {
      renderSummary();
    }
    updateNextState();
  }

  // --- Email verification ---------------------------------------------

  function setVerifyMessage(text, type) {
    verifyMessage.textContent = text;
    verifyMessage.className = "verify-message" + (type ? " " + type : "");
  }

  function updateSubmitState() {
    submitBtn.disabled = !emailVerified;
  }

  function resetVerification() {
    emailVerified = false;
    verifiedEmail = null;
    if (resendInterval) {
      clearInterval(resendInterval);
      resendInterval = null;
    }
    verifyCodeRow.hidden = true;
    verifyCodeInput.value = "";
    sendCodeBtn.hidden = false;
    sendCodeBtn.disabled = false;
    sendCodeBtn.textContent = "Send kode";
    setVerifyMessage("");
    updateSubmitState();
  }

  function startResendCooldown() {
    let remaining = RESEND_COOLDOWN_SECONDS;
    sendCodeBtn.disabled = true;
    sendCodeBtn.textContent = `Send kode på nytt (${remaining}s)`;
    resendInterval = setInterval(() => {
      remaining -= 1;
      if (remaining <= 0) {
        clearInterval(resendInterval);
        resendInterval = null;
        sendCodeBtn.disabled = false;
        sendCodeBtn.textContent = "Send kode på nytt";
      } else {
        sendCodeBtn.textContent = `Send kode på nytt (${remaining}s)`;
      }
    }, 1000);
  }

  sendCodeBtn.addEventListener("click", () => {
    const email = emailInput.value.trim();
    if (!email) {
      setVerifyMessage("Skriv inn e-postadressen din først.", "error");
      return;
    }
    sendCodeBtn.disabled = true;
    setVerifyMessage("Sender kode…");

    fetch("/book/send-kode/", {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
        "X-CSRFToken": getCsrfToken(),
      },
      body: `email=${encodeURIComponent(email)}`,
    })
      .then((res) => res.json().then((data) => ({ ok: res.ok, data })))
      .then(({ ok, data }) => {
        if (ok) {
          verifyCodeRow.hidden = false;
          verifyCodeInput.value = "";
          verifyCodeInput.focus();
          setVerifyMessage(`Kode sendt til ${email}. Sjekk innboksen din.`, "success");
          startResendCooldown();
        } else {
          setVerifyMessage(data.error || "Kunne ikke sende kode.", "error");
          sendCodeBtn.disabled = false;
        }
      })
      .catch(() => {
        setVerifyMessage("Noe gikk galt. Prøv igjen.", "error");
        sendCodeBtn.disabled = false;
      });
  });

  verifyCodeBtn.addEventListener("click", () => {
    const email = emailInput.value.trim();
    const code = verifyCodeInput.value.trim();
    if (!code) return;
    verifyCodeBtn.disabled = true;
    setVerifyMessage("Bekrefter…");

    fetch("/book/verifiser-kode/", {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
        "X-CSRFToken": getCsrfToken(),
      },
      body: `email=${encodeURIComponent(email)}&code=${encodeURIComponent(code)}`,
    })
      .then((res) => res.json().then((data) => ({ ok: res.ok, data })))
      .then(({ ok, data }) => {
        verifyCodeBtn.disabled = false;
        if (ok) {
          emailVerified = true;
          verifiedEmail = email;
          if (resendInterval) {
            clearInterval(resendInterval);
            resendInterval = null;
          }
          verifyCodeRow.hidden = true;
          sendCodeBtn.hidden = true;
          setVerifyMessage("✓ E-post bekreftet", "success");
        } else {
          setVerifyMessage(data.error || "Feil kode.", "error");
        }
        updateSubmitState();
      })
      .catch(() => {
        verifyCodeBtn.disabled = false;
        setVerifyMessage("Noe gikk galt. Prøv igjen.", "error");
      });
  });

  emailInput.addEventListener("input", () => {
    if (emailInput.value.trim() !== verifiedEmail) resetVerification();
  });

  emailInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") e.preventDefault();
  });

  verifyCodeInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      verifyCodeBtn.click();
    }
  });

  // --- Wizard wiring -----------------------------------------------------

  serviceInputs.forEach((input) => {
    input.addEventListener("change", () => {
      updateServiceHidden();
      updateNextState();
      if (dateHidden.value) fetchSlots();
    });
  });

  dateChips.forEach((chip) => {
    if (chip.disabled) return;
    chip.addEventListener("click", () => {
      dateChips.forEach((c) => c.classList.remove("selected"));
      chip.classList.add("selected");
      dateHidden.value = chip.dataset.date;
      updateNextState();
      fetchSlots();
    });
  });

  nextBtn.addEventListener("click", () => {
    if (!isStepValid(currentStep)) return;
    if (currentStep < TOTAL_STEPS) showStep(currentStep + 1);
  });

  backBtn.addEventListener("click", () => {
    if (currentStep > 1) showStep(currentStep - 1);
  });

  updateServiceHidden();
  updateSubmitState();
  showStep(1);
});
