// État de l'application
let currentCategory = "important";

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
const replyModal = document.getElementById("reply-modal");
const closeReplyModalBtn = document.getElementById("close-reply-modal");
const replyForm = document.getElementById("reply-form");

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
      <div class="email-actions">
        <button class="email-action-btn delete" onclick="deleteEmail('${
          email.id
        }')">
          <i class="fas fa-trash"></i> Supprimer
        </button>
        <button class="email-action-btn reply" onclick="replyToEmail('${
          email.id
        }')">
          <i class="fas fa-reply"></i> Répondre
        </button>
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
      unread: 0,
    };

    // Récupérer le nombre de mails non lus
    const unreadResponse = await fetch("/api/unread-count");
    if (!unreadResponse.ok) {
      throw new Error(
        "Erreur lors de la récupération du nombre de mails non lus"
      );
    }
    const unreadData = await unreadResponse.json();
    stats.unread = unreadData.count;

    // Récupérer les statistiques par catégorie
    for (const categorie in stats) {
      if (categorie !== "unread") {
        const response = await fetch(`/api/emails?categorie=${categorie}`);
        if (!response.ok) {
          throw new Error("Erreur lors de la récupération des statistiques");
        }
        const emails = await response.json();
        stats[categorie] = emails.length;
      }
    }

    document.getElementById("important-count").textContent = stats.important;
    document.getElementById("pub-count").textContent = stats.pub;
    document.getElementById("automatique-count").textContent =
      stats.automatique;
    document.getElementById("unread-count").textContent = stats.unread;
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

async function loadUserSettings() {
  try {
    const response = await fetch("/api/get-settings");
    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || "Erreur lors du chargement des paramètres");
    }

    // Remplir les champs du formulaire
    document.getElementById("email").value = data.email;
    document.getElementById("imap-server").value = data.imap_server;
    document.getElementById("gemini-api-key").value = data.gemini_api_key;
  } catch (error) {
    console.error("Erreur:", error);
    showNotification(error.message, "error");
  }
}

// Charger les paramètres lors de l'ouverture de la modale
settingsBtn.addEventListener("click", () => {
  settingsModal.classList.add("active");
  loadUserSettings();
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
    settingsModal.classList.remove("active");
  } catch (error) {
    console.error("Erreur:", error);
    showNotification(
      error.message ||
        "Une erreur est survenue lors de la mise à jour des paramètres",
      "error"
    );
  }
});

logoutBtn.addEventListener("click", () => {
  window.location.href = "/logout";
});

window.handleEmailClick = async function (event, expediteur) {
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
};

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

// Rendre les fonctions accessibles globalement
window.deleteEmail = async function (emailId) {
  try {
    const response = await fetch(`/api/emails/${emailId}`, {
      method: "DELETE",
    });

    if (!response.ok) {
      throw new Error("Erreur lors de la suppression de l'email");
    }

    showNotification("Email supprimé avec succès", "success");
    displayEmails(); // Rafraîchir l'affichage
    updateStats(); // Mettre à jour les statistiques
  } catch (error) {
    console.error("Erreur:", error);
    showNotification("Erreur lors de la suppression de l'email", "error");
  }
};

window.replyToEmail = async function (emailId) {
  try {
    const response = await fetch(`/api/emails/${emailId}`);
    if (!response.ok) {
      throw new Error("Erreur lors de la récupération de l'email");
    }

    const email = await response.json();

    // Remplir le formulaire avec les informations de l'email
    document.getElementById("reply-to").value = email.expediteur;
    document.getElementById("reply-subject").value = `Re: ${email.objet}`;
    document.getElementById("reply-content").value = "";

    // Afficher le modal
    replyModal.classList.add("active");
  } catch (error) {
    console.error("Erreur:", error);
    showNotification("Erreur lors de la préparation de la réponse", "error");
  }
};

// Gestionnaire pour fermer le modal de réponse
closeReplyModalBtn.addEventListener("click", () => {
  replyModal.classList.remove("active");
});

// Fermer le modal en cliquant en dehors
replyModal.addEventListener("click", (e) => {
  if (e.target === replyModal) {
    replyModal.classList.remove("active");
  }
});

// Gestionnaire pour l'envoi de la réponse
replyForm.addEventListener("submit", async (e) => {
  e.preventDefault();

  const to = document.getElementById("reply-to").value;
  const subject = document.getElementById("reply-subject").value;
  const content = document.getElementById("reply-content").value;

  try {
    const response = await fetch("/api/send-email", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        to,
        subject,
        content,
      }),
    });

    if (!response.ok) {
      throw new Error("Erreur lors de l'envoi de l'email");
    }

    const data = await response.json();
    showNotification(data.message, "success");
    replyModal.classList.remove("active");
  } catch (error) {
    console.error("Erreur:", error);
    showNotification("Erreur lors de l'envoi de l'email", "error");
  }
});

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

    updateStats();
    displayEmails();
  } catch (error) {
    console.error("Erreur:", error);
    alert("Une erreur est survenue lors de l'initialisation de l'application");
  }
}

// Démarrer l'application
init();
