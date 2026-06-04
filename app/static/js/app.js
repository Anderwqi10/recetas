const api = {
  async request(url, options = {}) {
    const res = await fetch(url, {
      credentials: "same-origin",
      headers: { "Content-Type": "application/json", ...options.headers },
      ...options,
    });
    const text = await res.text();
    let data = null;
    if (text) {
      try {
        data = JSON.parse(text);
      } catch {
        data = { detail: text };
      }
    }
    if (!res.ok) {
      const msg = data?.detail || (typeof data?.detail === "string" ? data.detail : res.statusText);
      throw new Error(Array.isArray(msg) ? msg.map((e) => e.msg).join(", ") : msg);
    }
    return data;
  },
  get(url) {
    return api.request(url);
  },
  post(url, body) {
    return api.request(url, { method: "POST", body: JSON.stringify(body) });
  },
  patch(url, body) {
    return api.request(url, { method: "PATCH", body: JSON.stringify(body) });
  },
  del(url) {
    return api.request(url, { method: "DELETE" });
  },
};

function showToast(message, type = "success") {
  const el = document.getElementById("toast");
  if (!el) return;
  el.textContent = message;
  el.className = `alert alert-${type === "error" ? "error" : "success"} toast`;
  el.hidden = false;
  setTimeout(() => {
    el.hidden = true;
  }, 4000);
}

async function loadIngredients() {
  const list = document.getElementById("ingredient-list");
  const items = await api.get("/api/ingredients");
  if (!items.length) {
    list.innerHTML = '<p class="muted">Aún no tienes ingredientes. Añade los que tengas en casa.</p>';
    return;
  }
  list.innerHTML = items
    .map(
      (i) => `
    <li class="ingredient-item" data-id="${i.id}">
      <span><strong>${escapeHtml(i.name)}</strong>${i.quantity ? ` <em>(${escapeHtml(i.quantity)})</em>` : ""}</span>
      <button type="button" class="btn-icon" data-delete="${i.id}" title="Eliminar">✕</button>
    </li>`
    )
    .join("");
}

async function loadRecipes() {
  const list = document.getElementById("recipe-list");
  const data = await api.get("/api/recipes");
  if (!data.items.length) {
    list.innerHTML = '<p class="muted">Genera tu primera receta con el botón de arriba.</p>';
    return;
  }
  list.innerHTML = data.items.map(renderRecipeCard).join("");
}

function escapeHtml(s) {
  const d = document.createElement("div");
  d.textContent = s;
  return d.innerHTML;
}

function renderRecipeCard(r) {
  const steps = r.steps.map((s, i) => `<li>${escapeHtml(s)}</li>`).join("");
  const stars = [1, 2, 3, 4, 5]
    .map(
      (n) =>
        `<button type="button" class="star ${r.rating >= n ? "active" : ""}" data-rate="${n}" data-id="${r.id}">★</button>`
    )
    .join("");
  return `
  <article class="recipe-card" data-id="${r.id}">
    <header>
      <h3>${escapeHtml(r.title)}</h3>
      <div class="recipe-actions">
        <button type="button" class="btn-outline btn-sm ${r.is_saved ? "saved" : ""}" data-save="${r.id}">
          ${r.is_saved ? "★ Guardada" : "Guardar"}
        </button>
        <button type="button" class="btn-icon" data-delete-recipe="${r.id}">✕</button>
      </div>
    </header>
    ${r.description ? `<p class="recipe-desc">${escapeHtml(r.description)}</p>` : ""}
    <p class="recipe-meta"><strong>Ingredientes:</strong> ${r.ingredients_used.map(escapeHtml).join(", ")}</p>
    <ol class="recipe-steps">${steps}</ol>
    <div class="rating-row">
      <span>Calificar:</span>
      <div class="stars">${stars}</div>
    </div>
  </article>`;
}

document.getElementById("ingredient-form")?.addEventListener("submit", async (e) => {
  e.preventDefault();
  const name = document.getElementById("ingredient-name").value;
  const quantity = document.getElementById("ingredient-qty").value;
  try {
    await api.post("/api/ingredients", { name, quantity: quantity || null });
    e.target.reset();
    await loadIngredients();
    showToast("Ingrediente añadido");
  } catch (err) {
    showToast(err.message, "error");
  }
});

document.getElementById("ingredient-list")?.addEventListener("click", async (e) => {
  const id = e.target.dataset.delete;
  if (!id) return;
  try {
    await api.del(`/api/ingredients/${id}`);
    await loadIngredients();
    showToast("Ingrediente eliminado");
  } catch (err) {
    showToast(err.message, "error");
  }
});

document.getElementById("btn-generate")?.addEventListener("click", async () => {
  const btn = document.getElementById("btn-generate");
  const notes = document.getElementById("extra-notes")?.value || null;
  btn.disabled = true;
  btn.textContent = "Generando receta…";
  try {
    await api.post("/api/recipes/generate", { extra_notes: notes });
    await loadRecipes();
    showToast("¡Receta generada!");
  } catch (err) {
    showToast(err.message, "error");
  } finally {
    btn.disabled = false;
    btn.textContent = "Generar receta con IA";
  }
});

document.getElementById("recipe-list")?.addEventListener("click", async (e) => {
  const recipeId = e.target.dataset.id || e.target.dataset.save || e.target.dataset.deleteRecipe;
  if (!recipeId) return;

  if (e.target.dataset.deleteRecipe) {
    if (!confirm("¿Eliminar esta receta?")) return;
    try {
      await api.del(`/api/recipes/${recipeId}`);
      await loadRecipes();
      showToast("Receta eliminada");
    } catch (err) {
      showToast(err.message, "error");
    }
    return;
  }

  if (e.target.dataset.save) {
    const card = e.target.closest(".recipe-card");
    const saved = e.target.classList.contains("saved");
    try {
      await api.patch(`/api/recipes/${recipeId}`, { is_saved: !saved });
      await loadRecipes();
      showToast(!saved ? "Receta guardada" : "Receta quitada de guardados");
    } catch (err) {
      showToast(err.message, "error");
    }
    return;
  }

  if (e.target.dataset.rate) {
    const rating = parseInt(e.target.dataset.rate, 10);
    try {
      await api.patch(`/api/recipes/${recipeId}`, { rating });
      await loadRecipes();
      showToast("Calificación guardada");
    } catch (err) {
      showToast(err.message, "error");
    }
  }
});

document.addEventListener("DOMContentLoaded", async () => {
  try {
    await Promise.all([loadIngredients(), loadRecipes()]);
  } catch (err) {
    showToast(err.message, "error");
  }
});
