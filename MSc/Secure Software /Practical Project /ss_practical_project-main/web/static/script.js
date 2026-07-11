document.addEventListener("DOMContentLoaded", () => {

  

    const buttons = document.querySelectorAll(".details-btn");

  buttons.forEach(btn => {

    btn.addEventListener("click", () => {

      const title = btn.dataset.title;

      const details = document.getElementById("doc-details");
      const titleField = document.getElementById("doc-title");

      details.style.display = "block";

      renderTitle(title)

    });

  });

    function renderTitle(title) {
      const el = document.getElementById("doc-title");
      updateField(el, title);
    }

    function updateField(element, value) {
      element.textContent = "Title: " + value;
    }

});