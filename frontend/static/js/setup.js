// Fonction pour afficher les notifications
function showNotification(message, type = "info") {
  const notification = document.createElement("div");
  notification.className = `notification ${type}`;
  notification.innerHTML = `
    <i class="fas ${
      type === "success"
        ? "fa-check-circle"
        : type === "error"
        ? "fa-exclamation-circle"
        : "fa-info-circle"
    }"></i>
    <span>${message}</span>
  `;

  document.body.appendChild(notification);

  // Supprimer la notification après 5 secondes
  setTimeout(() => {
    notification.style.animation = "slideOut 0.3s ease";
    setTimeout(() => notification.remove(), 300);
  }, 5000);
}

// Gestionnaire du formulaire de configuration IMAP
document.addEventListener("DOMContentLoaded", () => {
  const imapSettingsForm = document.getElementById("imap-settings-form");

  if (!imapSettingsForm) {
    console.error("Formulaire IMAP non trouvé");
    return;
  }

  imapSettingsForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    // Désactiver le bouton pendant la soumission
    const submitButton = e.target.querySelector('button[type="submit"]');
    submitButton.disabled = true;
    submitButton.innerHTML =
      '<i class="fas fa-spinner fa-spin"></i> Enregistrement...';

    const formData = {
      email: document.getElementById("email").value,
      imap_password: document.getElementById("imap-password").value,
      imap_server: document.getElementById("imap-server").value,
      gemini_api_key: document.getElementById("gemini-api-key").value,
    };

    try {
      const response = await fetch("/api/update-settings", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(formData),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.error ||
            "Une erreur est survenue lors de la mise à jour des paramètres"
        );
      }

      showNotification(data.message, "success");
      if (data.test_message) {
        showNotification(data.test_message, "info");
      }

      // Redirection vers la page principale après un court délai
      setTimeout(() => {
        window.location.href = "/";
      }, 1500);
    } catch (error) {
      console.error("Erreur:", error);
      showNotification(
        error.message ||
          "Une erreur est survenue lors de la mise à jour des paramètres",
        "error"
      );
    } finally {
      // Réactiver le bouton
      submitButton.disabled = false;
      submitButton.innerHTML = '<i class="fas fa-save"></i> Enregistrer';
    }
  });
});
