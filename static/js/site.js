(() => {
  const isCartForm = (form) => {
    if (!(form instanceof HTMLFormElement) || form.method.toLowerCase() !== "post") {
      return false;
    }

    const actionUrl = new URL(form.action, window.location.href);
    return actionUrl.origin === window.location.origin
      && actionUrl.pathname.startsWith("/cart/");
  };

  document.addEventListener("submit", async (event) => {
    const form = event.target;
    if (!isCartForm(form) || !window.fetch || !window.DOMParser) {
      return;
    }

    event.preventDefault();

    const scrollX = window.scrollX;
    const scrollY = window.scrollY;
    const submitter = event.submitter;
    const buttons = form.querySelectorAll("button");
    buttons.forEach((button) => {
      button.disabled = true;
    });
    document.body.classList.add("cart-action-pending");

    try {
      const response = await fetch(form.action, {
        method: "POST",
        body: new FormData(form),
        credentials: "same-origin",
        headers: {
          "X-Requested-With": "XMLHttpRequest",
        },
      });

      if (!response.ok) {
        throw new Error(`Cart request failed: ${response.status}`);
      }

      const html = await response.text();
      const nextDocument = new DOMParser().parseFromString(html, "text/html");
      if (!nextDocument.body) {
        throw new Error("Cart response has no body");
      }

      document.title = nextDocument.title;
      document.body.className = nextDocument.body.className;
      document.body.innerHTML = nextDocument.body.innerHTML;
      window.scrollTo(scrollX, scrollY);
      requestAnimationFrame(() => window.scrollTo(scrollX, scrollY));
    } catch (error) {
      buttons.forEach((button) => {
        button.disabled = false;
      });
      document.body.classList.remove("cart-action-pending");

      if (submitter) {
        const fallback = document.createElement("input");
        fallback.type = "hidden";
        fallback.name = submitter.name;
        fallback.value = submitter.value;
        form.append(fallback);
      }
      HTMLFormElement.prototype.submit.call(form);
    }
  });
})();
