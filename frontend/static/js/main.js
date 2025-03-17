// État de l'application
let currentCategory = "important";
let emails = [];

// Éléments DOM
const usernameElement = document.getElementById("username");
const fetchEmailsBtn = document.getElementById("fetch-emails");
const settingsBtn = document.getElementById("settings-btn");
const settingsModal = document.getElementById("settings-modal");
const closeSettingsBtn = document.getElementById("close-settings");
const imapSettingsForm = document.getElementById("imap-settings-form");
const logoutBtn = document.getElementById("logout-btn");
const emailsContainer = document.querySelector(".emails-container");
const categoryButtons = document.querySelectorAll(".nav-section li");
const deletePubBtn = document.getElementById("delete-pub-btn");

// Fonctions utilitaires
function formatDate(dateString) {
  const date = new Date(dateString);
  return date.toLocaleDateString("fr-FR", {
    year: "numeric",
    month: "long",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function createEmailCard(email) {
  const reponseAutomatique = email.reponse_automatique
    ? `<div class="email-response">
          <div class="response-header">
            <i class="fas fa-robot"></i> Réponse automatique
          </div>
          <div class="response-content">
            ${email.reponse_automatique}
          </div>
        </div>`
    : "";

  return `
    <div class="email-card">
      <div class="email-header">
        <div>
          <div class="email-subject">${email.objet}</div>
          <div class="email-meta">
            <span class="email-sender" onclick="handleEmailClick(event, '${
              email.expediteur
            }')">${email.expediteur}</span> • 
            <span>${formatDate(email.date_reception)}</span>
          </div>
        </div>
      </div>
      <div class="email-content">
        ${email.contenu}
        ${reponseAutomatique}
      </div>
    </div>
  `;
}

async function updateStats() {
  try {
    const stats = {
      important: 0,
      pub: 0,
      automatique: 0,
    };

    for (const categorie in stats) {
      const response = await fetch(`/api/emails?categorie=${categorie}`);
      if (!response.ok)
        throw new Error("Erreur lors de la récupération des statistiques");
      const emails = await response.json();
      stats[categorie] = emails.length;
    }

    document.getElementById("important-count").textContent = stats.important;
    document.getElementById("pub-count").textContent = stats.pub;
    document.getElementById("automatique-count").textContent =
      stats.automatique;
  } catch (error) {
    console.error("Erreur:", error);
  }
}

async function displayEmails() {
  try {
    console.log("Récupération des emails pour la catégorie:", currentCategory);
    const response = await fetch(`/api/emails?categorie=${currentCategory}`);
    if (!response.ok)
      throw new Error("Erreur lors de la récupération des emails");

    const filteredEmails = await response.json();
    console.log("Emails reçus:", filteredEmails);

    if (!Array.isArray(filteredEmails)) {
      console.error("Les emails reçus ne sont pas un tableau:", filteredEmails);
      emailsContainer.innerHTML =
        '<div class="error">Format de données invalide</div>';
      return;
    }

    emailsContainer.innerHTML =
      filteredEmails.length > 0
        ? filteredEmails.map(createEmailCard).join("")
        : '<div class="no-emails">Aucun email dans cette catégorie</div>';
  } catch (error) {
    console.error("Erreur:", error);
    emailsContainer.innerHTML =
      '<div class="error">Erreur lors du chargement des emails</div>';
  }
}

// Gestionnaires d'événements
categoryButtons.forEach((button) => {
  button.addEventListener("click", () => {
    categoryButtons.forEach((btn) => btn.classList.remove("active"));
    button.classList.add("active");
    currentCategory = button.dataset.category;
    displayEmails();
  });
});

fetchEmailsBtn.addEventListener("click", async () => {
  try {
    fetchEmailsBtn.disabled = true;
    fetchEmailsBtn.innerHTML =
      '<i class="fas fa-spinner fa-spin"></i> Récupération en cours...';

    const response = await fetch("/api/fetch-emails", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (!response.ok)
      throw new Error("Erreur lors de la récupération des emails");

    const data = await response.json();
    emails = data.emails;
    updateStats();
    displayEmails();

    fetchEmailsBtn.innerHTML =
      '<i class="fas fa-sync"></i> Récupérer les nouveaux mails';
  } catch (error) {
    console.error("Erreur:", error);
    alert("Une erreur est survenue lors de la récupération des emails");
  } finally {
    fetchEmailsBtn.disabled = false;
  }
});

settingsBtn.addEventListener("click", () => {
  settingsModal.classList.add("active");
});

closeSettingsBtn.addEventListener("click", () => {
  settingsModal.classList.remove("active");
});

imapSettingsForm.addEventListener("submit", async (e) => {
  e.preventDefault();

  const formData = {
    email: document.getElementById("email").value,
    imap_password: document.getElementById("imap-password").value,
    imap_server: document.getElementById("imap-server").value,
  };

  try {
    const response = await fetch("/api/update-imap", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(formData),
    });

    if (!response.ok)
      throw new Error("Erreur lors de la mise à jour des paramètres IMAP");

    settingsModal.classList.remove("active");
    alert("Paramètres IMAP mis à jour avec succès");
  } catch (error) {
    console.error("Erreur:", error);
    alert("Une erreur est survenue lors de la mise à jour des paramètres IMAP");
  }
});

logoutBtn.addEventListener("click", async () => {
  try {
    const response = await fetch("/api/logout", {
      method: "POST",
    });

    if (!response.ok) throw new Error("Erreur lors de la déconnexion");

    window.location.href = "/login";
  } catch (error) {
    console.error("Erreur:", error);
    alert("Une erreur est survenue lors de la déconnexion");
  }
});

async function handleEmailClick(event, expediteur) {
  // Empêcher la propagation de l'événement
  event.stopPropagation();

  try {
    const response = await fetch("/api/mark-sender-pub", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ expediteur }),
    });

    if (!response.ok) {
      throw new Error("Erreur lors du marquage de l'expéditeur");
    }

    const data = await response.json();
    showNotification(data.message, "success");
  } catch (error) {
    console.error("Erreur:", error);
    showNotification("Erreur lors du marquage de l'expéditeur", "error");
  }
}

function showNotification(message, type = "info") {
  const notification = document.createElement("div");
  notification.className = `notification ${type}`;
  notification.textContent = message;

  document.body.appendChild(notification);

  setTimeout(() => {
    notification.remove();
  }, 3000);
}

async function deletePubEmails() {
  if (
    !confirm(
      "Êtes-vous sûr de vouloir supprimer tous les mails de catégorie pub ?"
    )
  ) {
    return;
  }

  try {
    deletePubBtn.disabled = true;
    deletePubBtn.innerHTML =
      '<i class="fas fa-spinner fa-spin"></i> Suppression en cours...';

    const response = await fetch("/api/delete-pub-emails", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      throw new Error("Erreur lors de la suppression des mails pub");
    }

    const data = await response.json();
    showNotification(data.message, "success");
    updateStats();
    displayEmails();
  } catch (error) {
    console.error("Erreur:", error);
    showNotification("Erreur lors de la suppression des mails pub", "error");
  } finally {
    deletePubBtn.disabled = false;
    deletePubBtn.innerHTML = '<i class="fas fa-trash"></i> Supprimer les pubs';
  }
}

// Gestionnaires d'événements
deletePubBtn.addEventListener("click", deletePubEmails);

// Initialisation
async function init() {
  try {
    // Récupérer les informations de l'utilisateur
    const userResponse = await fetch("/api/user");
    if (!userResponse.ok)
      throw new Error(
        "Erreur lors de la récupération des informations utilisateur"
      );

    const userData = await userResponse.json();
    usernameElement.textContent = userData.username;

    // Récupérer les emails existants
    const emailsResponse = await fetch("/api/emails");
    if (!emailsResponse.ok)
      throw new Error("Erreur lors de la récupération des emails");

    emails = await emailsResponse.json();
    updateStats();
    displayEmails();
  } catch (error) {
    console.error("Erreur:", error);
    alert("Une erreur est survenue lors de l'initialisation de l'application");
  }
}

// Démarrer l'application
init();
