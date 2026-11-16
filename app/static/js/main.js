/* ==========================================================================
   HANDBALL FANTASY — Client-Side Interactivity
   ========================================================================== */

document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".modal-backdrop").forEach((backdrop) => {
    backdrop.addEventListener("click", (e) => {
      if (e.target === backdrop) {
        backdrop.classList.remove("open");
      }
    });
  });

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      document.querySelectorAll(".modal-backdrop.open").forEach((m) => {
        m.classList.remove("open");
      });
    }
  });

  initLiveFilter({
    searchId: "filter-search",
    clubId: "filter-club",
    posId: "filter-pos",
    countryId: "filter-country",
    itemSelector: ".filterable-item"
  });

  const params = new URLSearchParams(window.location.search);
  const verJogadorId = params.get("ver");
  if (verJogadorId) {
    const row = document.querySelector(`[data-player-id="${verJogadorId}"]`);
    if (row) {
      openPlayerDetailModal(row);
    }
  }
});

function openModal(modalId) {
  const el = document.getElementById(modalId);
  if (el) el.classList.add("open");
}

function closeModal(modalId) {
  const el = document.getElementById(modalId);
  if (el) el.classList.remove("open");
}

function openPlayerDetailModal(rowElement) {
  const modal = document.getElementById("modal-detalhe-jogador");
  if (!modal || !rowElement) return;

  const id = rowElement.dataset.playerId || "";
  const nome = rowElement.dataset.playerNome || "";
  const clubeId = rowElement.dataset.playerClubeId || "";
  const clubeNome = rowElement.dataset.playerClube || "";
  const posId = rowElement.dataset.playerPosId || "";
  const posNome = rowElement.dataset.playerPos || "";
  const paisId = rowElement.dataset.playerPaisId || "";
  const camisola = rowElement.dataset.playerCamisola || "";
  const golos = rowElement.dataset.playerGolos || "0";
  const pontos = rowElement.dataset.playerPontos || "0";

  const titleEl = document.getElementById("detail-player-name");
  const subtitleEl = document.getElementById("detail-player-meta");
  const statsBadgeEl = document.getElementById("detail-player-stats");

  if (titleEl) titleEl.textContent = nome;
  if (subtitleEl) subtitleEl.textContent = `${clubeNome} | ${posNome} | Camisola #${camisola || "-"}`;
  if (statsBadgeEl) statsBadgeEl.textContent = `${golos} Golos | ${pontos} Pts`;

  const editForm = document.getElementById("form-edit-player");
  if (editForm) {
    editForm.action = `/jogadores/${id}/editar`;
    const inputNome = editForm.querySelector('[name="nome"]');
    const selectClube = editForm.querySelector('[name="id_clube"]');
    const selectPos = editForm.querySelector('[name="id_posicao"]');
    const selectPais = editForm.querySelector('[name="id_pais"]');
    const inputCamisola = editForm.querySelector('[name="numero_camisola"]');

    if (inputNome) inputNome.value = nome;
    if (selectClube) selectClube.value = clubeId;
    if (selectPos) selectPos.value = posId;
    if (selectPais) selectPais.value = paisId;
    if (inputCamisola) inputCamisola.value = camisola;
  }

  const deleteForm = document.getElementById("form-delete-player");
  if (deleteForm) {
    deleteForm.action = `/jogadores/${id}/eliminar`;
  }

  document.querySelectorAll(".player-history-row").forEach((hRow) => {
    hRow.style.display = hRow.dataset.historyPlayerId === id ? "" : "none";
  });

  openModal("modal-detalhe-jogador");
}

function initLiveFilter({ searchId, clubId, posId, countryId, itemSelector }) {
  const searchInput = document.getElementById(searchId);
  const clubSelect = document.getElementById(clubId);
  const posSelect = document.getElementById(posId);
  const countrySelect = document.getElementById(countryId);
  const items = document.querySelectorAll(itemSelector);

  if (!items.length) return;

  const applyFilters = () => {
    const q = (searchInput?.value || "").trim().toLowerCase();
    const club = clubSelect?.value || "";
    const pos = posSelect?.value || "";
    const country = countrySelect?.value || "";

    items.forEach((item) => {
      const name = (item.dataset.name || "").toLowerCase();
      const itemClub = item.dataset.club || "";
      const itemPos = item.dataset.pos || "";
      const itemCountry = item.dataset.country || "";

      const matchName = !q || name.includes(q);
      const matchClub = !club || itemClub === club;
      const matchPos = !pos || itemPos === pos;
      const matchCountry = !country || itemCountry === country;

      item.style.display = matchName && matchClub && matchPos && matchCountry ? "" : "none";
    });
  };

  [searchInput, clubSelect, posSelect, countrySelect].forEach((el) => {
    if (el) {
      el.addEventListener("input", applyFilters);
      el.addEventListener("change", applyFilters);
    }
  });
}

function resetFilters() {
  ["filter-search", "filter-club", "filter-pos", "filter-country"].forEach((id) => {
    const el = document.getElementById(id);
    if (el) {
      el.value = "";
      el.dispatchEvent(new Event("input"));
    }
  });
}

function filterJornada(jornadaId, btnElement) {
  document.querySelectorAll(".pill-tab").forEach((b) => b.classList.remove("active"));
  if (btnElement) btnElement.classList.add("active");

  document.querySelectorAll(".jornada-match-card").forEach((card) => {
    if (!jornadaId || card.dataset.jornada === String(jornadaId)) {
      card.style.display = "";
    } else {
      card.style.display = "none";
    }
  });
}

function selectClubPanel(clubeId, cardElement) {
  document.querySelectorAll(".club-card").forEach((c) => c.classList.remove("selected"));
  if (cardElement) cardElement.classList.add("selected");

  document.querySelectorAll(".club-squad-group").forEach((panel) => {
    panel.style.display = panel.dataset.clubSquad === String(clubeId) ? "block" : "none";
  });
}
