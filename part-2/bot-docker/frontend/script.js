const filterButtons = Array.from(document.querySelectorAll(".chip"));
const faqItems = Array.from(document.querySelectorAll(".faq-item"));
const faqQuestions = Array.from(document.querySelectorAll(".faq-item__question"));
const form = document.querySelector("#brief-form");
const formStatus = document.querySelector("#form-status");

faqItems.forEach((item, index) => {
  const question = item.querySelector(".faq-item__question");
  const answer = item.querySelector(".faq-item__answer");
  if (!question || !answer) return;
  const answerId = `faq-answer-${index + 1}`;
  answer.id = answerId;
  question.setAttribute("aria-controls", answerId);
  question.setAttribute("aria-expanded", String(item.classList.contains("is-open")));
});

function openFaqItem(item) {
  const willOpen = !item.classList.contains("is-open");
  faqItems.forEach((node) => {
    node.classList.remove("is-open");
    const question = node.querySelector(".faq-item__question");
    if (question) question.setAttribute("aria-expanded", "false");
  });
  if (willOpen) {
    item.classList.add("is-open");
    const question = item.querySelector(".faq-item__question");
    if (question) question.setAttribute("aria-expanded", "true");
  }
}

faqQuestions.forEach((button) => {
  button.addEventListener("click", () => {
    const item = button.closest(".faq-item");
    if (!item) return;
    openFaqItem(item);
  });
});

filterButtons.forEach((button) => {
  button.addEventListener("click", () => {
    const { filter } = button.dataset;
    filterButtons.forEach((node) => node.classList.remove("is-active"));
    button.classList.add("is-active");

    faqItems.forEach((item) => {
      const topic = item.dataset.topic;
      const show = filter === "all" || topic === filter;
      item.hidden = !show;
      if (!show) item.classList.remove("is-open");
      const question = item.querySelector(".faq-item__question");
      if (question && !show) question.setAttribute("aria-expanded", "false");
    });

    const firstVisible = faqItems.find((item) => !item.hidden);
    if (firstVisible) {
      firstVisible.classList.add("is-open");
      const question = firstVisible.querySelector(".faq-item__question");
      if (question) question.setAttribute("aria-expanded", "true");
    }
  });
});

if (form && formStatus) {
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    const data = new FormData(form);
    const name = String(data.get("name") || "").trim();
    formStatus.textContent = name
      ? `${name}, спасибо! Бриф получен, свяжемся с вами в течение 2 часов.`
      : "Спасибо! Бриф получен, свяжемся с вами в течение 2 часов.";
    form.reset();
  });
}

const revealItems = document.querySelectorAll(".reveal");
if (revealItems.length > 0) {
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        entry.target.classList.add("in");
        observer.unobserve(entry.target);
      });
    },
    {
      threshold: 0.14,
      rootMargin: "0px 0px -30px 0px",
    }
  );
  revealItems.forEach((item) => observer.observe(item));
}
