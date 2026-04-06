let products = [];
let filters = ["All"];
let activeFilter = "All";
let cart = [];
let reviews = [];
let activeProductId = null;
let toastTimeoutId = null;
const selectedSizes = {};

const productsDiv = document.getElementById("products");
const filtersDiv = document.getElementById("filters");
const cartItems = document.getElementById("cartItems");
const cartCount = document.getElementById("cartCount");
const cartTotal = document.getElementById("cartTotal");
const clearCartButton = document.getElementById("clearCart");
const cartButton = document.querySelector(".cart-button");
const cartPanel = document.getElementById("cartPanel");
const membershipForm = document.getElementById("membershipForm");
const checkoutButton = document.getElementById("checkoutButton");
const supportButton = document.getElementById("supportButton");
const toast = document.getElementById("toast");
const supportList = document.getElementById("supportList");
const reviewList = document.getElementById("reviewList");
const reviewAverage = document.getElementById("reviewAverage");
const reviewCount = document.getElementById("reviewCount");
const reviewForm = document.getElementById("reviewForm");
const reviewName = document.getElementById("reviewName");
const reviewRole = document.getElementById("reviewRole");
const reviewRating = document.getElementById("reviewRating");
const reviewComment = document.getElementById("reviewComment");

const productModal = document.getElementById("productModal");
const closeProductModalButton = document.getElementById("closeProductModal");
const modalImage = document.getElementById("modalImage");
const modalCategory = document.getElementById("modalCategory");
const modalTitle = document.getElementById("modalTitle");
const modalPrice = document.getElementById("modalPrice");
const modalNote = document.getElementById("modalNote");
const modalSizes = document.getElementById("modalSizes");
const modalAddToCartButton = document.getElementById("modalAddToCart");

const checkoutModal = document.getElementById("checkoutModal");
const checkoutForm = document.getElementById("checkoutForm");
const checkoutItems = document.getElementById("checkoutItems");
const checkoutTotal = document.getElementById("checkoutTotal");
const customerName = document.getElementById("customerName");
const customerPhone = document.getElementById("customerPhone");
const customerAddress = document.getElementById("customerAddress");
const paymentMethod = document.getElementById("paymentMethod");

const supportModal = document.getElementById("supportModal");

function formatPrice(price) {
  return `${Number(price).toLocaleString()} EGP`;
}

function showToast(message) {
  toast.textContent = message;
  toast.classList.add("is-visible");
  window.clearTimeout(toastTimeoutId);
  toastTimeoutId = window.setTimeout(() => {
    toast.classList.remove("is-visible");
  }, 2400);
}

function syncBodyScroll() {
  const hasOpenModal = document.querySelector(".product-modal.is-open, .overlay-modal.is-open");
  document.body.style.overflow = hasOpenModal ? "hidden" : "";
}

function openOverlay(modal) {
  modal.classList.add("is-open");
  modal.setAttribute("aria-hidden", "false");
  syncBodyScroll();
}

function closeOverlay(modal) {
  modal.classList.remove("is-open");
  modal.setAttribute("aria-hidden", "true");
  syncBodyScroll();
}

async function requestJson(url, options = {}) {
  const response = await fetch(url, options);
  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(data.error || data.message || "Request failed.");
  }

  return data;
}

function getSelectedSize(productId) {
  return selectedSizes[productId] || "";
}

function setSelectedSize(productId, size) {
  selectedSizes[productId] = size;
}

function renderStars(rating) {
  return "★".repeat(rating) + "☆".repeat(5 - rating);
}

function renderSizeButtons(product, scope = "card") {
  const selectedSize = getSelectedSize(product.id);

  return product.sizes
    .map(
      (size) => `
        <button
          class="size-chip ${selectedSize === size ? "active" : ""}"
          type="button"
          data-size-product="${product.id}"
          data-size-value="${size}"
          data-size-scope="${scope}"
          aria-pressed="${selectedSize === size ? "true" : "false"}"
        >
          ${size}
        </button>
      `
    )
    .join("");
}

function renderFilters() {
  filtersDiv.innerHTML = filters
    .map(
      (filter) => `
        <button
          type="button"
          class="filter-chip ${filter === activeFilter ? "active" : ""}"
          data-filter="${filter}"
        >
          ${filter}
        </button>
      `
    )
    .join("");
}

function renderProducts() {
  const visibleProducts = activeFilter === "All"
    ? products
    : products.filter((product) => product.category === activeFilter);

  productsDiv.innerHTML = visibleProducts
    .map(
      (product) => `
        <article class="product-card">
          <button class="product-card-hitbox" type="button" data-open-product="${product.id}" aria-label="Open ${product.name} details"></button>
          <div
            class="product-visual"
            style="background-image:linear-gradient(180deg, rgba(17, 12, 10, 0.06), rgba(17, 12, 10, 0.12)), url('${product.image}')"
          >
            <span class="product-badge">${product.badge}</span>
            <div class="product-swatch" style="background:${product.swatch}"></div>
          </div>

          <div class="product-content">
            <div class="product-title-row">
              <div class="product-title-block">
                <span class="product-category">${product.category}</span>
                <h3>${product.name}</h3>
              </div>
              <span class="product-price">${formatPrice(product.price)}</span>
            </div>

            <p class="product-note">${product.note}</p>

            <div class="product-size-block">
              <span class="size-label">Choose size</span>
              <div class="sizes" aria-label="Available sizes">
                ${renderSizeButtons(product)}
              </div>
            </div>

            <div class="product-footer">
              <p class="size-hint">${getSelectedSize(product.id) ? `Selected size: ${getSelectedSize(product.id)}` : "Select a size before adding to cart."}</p>
              <button class="add-button" type="button" data-id="${product.id}">Add to Cart</button>
            </div>
          </div>
        </article>
      `
    )
    .join("");
}

function renderReviews() {
  if (!reviews.length) {
    reviewList.innerHTML = `<article class="review-card"><p>No reviews yet. Be the first to write one.</p></article>`;
    reviewAverage.textContent = "0.0";
    reviewCount.textContent = "0 reviews";
    return;
  }

  const average = (reviews.reduce((sum, review) => sum + review.rating, 0) / reviews.length).toFixed(1);
  reviewAverage.textContent = average;
  reviewCount.textContent = `${reviews.length} review${reviews.length === 1 ? "" : "s"}`;

  reviewList.innerHTML = reviews
    .map(
      (review) => `
        <article class="review-card">
          <div class="review-stars">${renderStars(review.rating)}</div>
          <p>"${review.comment}"</p>
          <strong>${review.name}</strong>
          <span>${review.role}</span>
        </article>
      `
    )
    .join("");
}

function renderCart() {
  if (!cart.length) {
    cartItems.innerHTML = `
      <li class="empty-cart">
        Your cart is empty. Add a few pieces from the collection to build the order summary.
      </li>
    `;
  } else {
    cartItems.innerHTML = cart
      .map(
        (item, index) => `
          <li class="cart-item">
            <div class="cart-item-row">
              <strong>${item.name}</strong>
              <span class="product-price">${formatPrice(item.price)}</span>
            </div>
            <div class="cart-item-meta">${item.category} • Size ${item.selectedSize}</div>
            <button class="cart-item-remove" type="button" data-cart-index="${index}">
              Remove item
            </button>
          </li>
        `
      )
      .join("");
  }

  const total = cart.reduce((sum, item) => sum + item.price, 0);
  cartCount.textContent = cart.length;
  cartTotal.textContent = formatPrice(total);
}

function renderCheckoutSummary() {
  if (!cart.length) {
    checkoutItems.innerHTML = "<li>Your cart is empty.</li>";
    checkoutTotal.textContent = formatPrice(0);
    return;
  }

  checkoutItems.innerHTML = cart
    .map((item) => `<li>${item.name} <span>Size ${item.selectedSize}</span> <strong>${formatPrice(item.price)}</strong></li>`)
    .join("");

  checkoutTotal.textContent = formatPrice(cart.reduce((sum, item) => sum + item.price, 0));
}

function addToCart(productId) {
  const selectedProduct = products.find((product) => product.id === productId);
  const selectedSize = getSelectedSize(productId);

  if (!selectedProduct) {
    return;
  }

  if (!selectedSize) {
    showToast(`Choose a size for ${selectedProduct.name} first.`);
    return;
  }

  cart.push({ ...selectedProduct, selectedSize });
  renderCart();
  renderCheckoutSummary();
  cartPanel.scrollIntoView({ behavior: "smooth", block: "start" });
  showToast(`${selectedProduct.name} size ${selectedSize} added to cart.`);
}

function openProductModal(productId) {
  const product = products.find((item) => item.id === productId);

  if (!product) {
    return;
  }

  activeProductId = productId;
  modalImage.style.backgroundImage = `linear-gradient(180deg, rgba(17, 12, 10, 0.08), rgba(17, 12, 10, 0.24)), url('${product.image}')`;
  modalCategory.textContent = product.category;
  modalTitle.textContent = product.name;
  modalPrice.textContent = formatPrice(product.price);
  modalNote.textContent = product.note;
  modalSizes.innerHTML = renderSizeButtons(product, "modal");
  openOverlay(productModal);
}

function closeProductModal() {
  activeProductId = null;
  closeOverlay(productModal);
}

function removeFromCart(index) {
  const removedItem = cart[index];
  cart = cart.filter((_, itemIndex) => itemIndex !== index);
  renderCart();
  renderCheckoutSummary();

  if (removedItem) {
    showToast(`${removedItem.name} size ${removedItem.selectedSize} removed from cart.`);
  }
}

async function loadProducts() {
  const data = await requestJson("/api/products");
  products = data.products || [];
  filters = ["All", ...new Set(products.map((product) => product.category))];
  renderFilters();
  renderProducts();
}

async function loadReviews() {
  const data = await requestJson("/api/reviews");
  reviews = data.reviews || [];
  renderReviews();
}

async function loadSupportInfo() {
  const data = await requestJson("/api/support");
  supportList.innerHTML = `
    <div>
      <strong>Phone</strong>
      <p>${data.phone}</p>
    </div>
    <div>
      <strong>Email</strong>
      <p>${data.email}</p>
    </div>
    <div>
      <strong>Hours</strong>
      <p>${data.hours}</p>
    </div>
  `;
}

filtersDiv.addEventListener("click", (event) => {
  const target = event.target.closest("[data-filter]");

  if (!target) {
    return;
  }

  activeFilter = target.dataset.filter;
  renderFilters();
  renderProducts();
  showToast(`Showing ${activeFilter === "All" ? "all items" : activeFilter}.`);
});

productsDiv.addEventListener("click", (event) => {
  const sizeButton = event.target.closest("[data-size-product]");

  if (sizeButton) {
    setSelectedSize(Number(sizeButton.dataset.sizeProduct), sizeButton.dataset.sizeValue);
    renderProducts();

    if (activeProductId === Number(sizeButton.dataset.sizeProduct) && productModal.classList.contains("is-open")) {
      openProductModal(activeProductId);
    }

    return;
  }

  const addButton = event.target.closest("[data-id]");

  if (addButton) {
    addToCart(Number(addButton.dataset.id));
    return;
  }

  const productTrigger = event.target.closest("[data-open-product]");

  if (productTrigger) {
    openProductModal(Number(productTrigger.dataset.openProduct));
    return;
  }

  const productCard = event.target.closest(".product-card");

  if (productCard) {
    const fallbackTrigger = productCard.querySelector("[data-open-product]");

    if (fallbackTrigger) {
      openProductModal(Number(fallbackTrigger.dataset.openProduct));
    }
  }
});

modalSizes.addEventListener("click", (event) => {
  const sizeButton = event.target.closest("[data-size-product]");

  if (!sizeButton) {
    return;
  }

  setSelectedSize(Number(sizeButton.dataset.sizeProduct), sizeButton.dataset.sizeValue);
  const product = products.find((item) => item.id === Number(sizeButton.dataset.sizeProduct));

  if (product) {
    modalSizes.innerHTML = renderSizeButtons(product, "modal");
    renderProducts();
  }
});

cartItems.addEventListener("click", (event) => {
  const target = event.target.closest("[data-cart-index]");

  if (!target) {
    return;
  }

  removeFromCart(Number(target.dataset.cartIndex));
});

clearCartButton.addEventListener("click", () => {
  if (!cart.length) {
    showToast("Your cart is already empty.");
    return;
  }

  cart = [];
  renderCart();
  renderCheckoutSummary();
  showToast("Cart cleared.");
});

cartButton.addEventListener("click", () => {
  cartPanel.scrollIntoView({ behavior: "smooth", block: "start" });
  showToast(cart.length ? "Cart summary opened." : "Your cart is empty.");
});

closeProductModalButton.addEventListener("click", closeProductModal);

productModal.addEventListener("click", (event) => {
  if (event.target.closest("[data-close-modal='true']")) {
    closeProductModal();
  }
});

modalAddToCartButton.addEventListener("click", () => {
  if (activeProductId !== null) {
    addToCart(activeProductId);
  }
});

membershipForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  const input = membershipForm.querySelector("input");
  const button = membershipForm.querySelector("button");
  const email = input.value.trim();

  if (!email) {
    input.focus();
    showToast("Enter your email to join the newsletter.");
    return;
  }

  try {
    button.disabled = true;
    await requestJson("/api/newsletter", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email })
    });
    button.textContent = "Joined";
    input.disabled = true;
    showToast("You joined the Abdo store mailing list.");
  } catch (error) {
    button.disabled = false;
    showToast(error.message);
  }
});

reviewForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  const payload = {
    name: reviewName.value.trim(),
    role: reviewRole.value.trim(),
    rating: Number(reviewRating.value),
    comment: reviewComment.value.trim()
  };

  if (!payload.name || !payload.role || !payload.rating || !payload.comment) {
    showToast("Complete the full review form first.");
    return;
  }

  const submitButton = reviewForm.querySelector("button");

  try {
    submitButton.disabled = true;
    await requestJson("/api/reviews", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    reviewForm.reset();
    await loadReviews();
    showToast("Your review has been published.");
  } catch (error) {
    showToast(error.message);
  } finally {
    submitButton.disabled = false;
  }
});

checkoutButton.addEventListener("click", () => {
  if (!cart.length) {
    document.getElementById("collection").scrollIntoView({ behavior: "smooth", block: "start" });
    showToast("Add products before proceeding to checkout.");
    return;
  }

  renderCheckoutSummary();
  openOverlay(checkoutModal);
});

checkoutForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  const payload = {
    name: customerName.value.trim(),
    phone: customerPhone.value.trim(),
    address: customerAddress.value.trim(),
    payment_method: paymentMethod.value,
    cart: cart.map((item) => ({ id: item.id, size: item.selectedSize }))
  };

  if (!payload.name || !payload.phone || !payload.address || !payload.payment_method) {
    showToast("Complete all checkout fields first.");
    return;
  }

  if (!payload.cart.length) {
    showToast("Your cart is empty.");
    return;
  }

  try {
    const result = await requestJson("/api/checkout", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    cart = [];
    renderCart();
    renderCheckoutSummary();
    checkoutForm.reset();
    closeOverlay(checkoutModal);
    showToast(result.message);
  } catch (error) {
    showToast(error.message);
  }
});

supportButton.addEventListener("click", async () => {
  try {
    await loadSupportInfo();
    openOverlay(supportModal);
  } catch (error) {
    showToast(error.message);
  }
});

document.querySelectorAll("[data-close-overlay]").forEach((button) => {
  button.addEventListener("click", () => {
    const modal = document.getElementById(button.dataset.closeOverlay);

    if (modal) {
      closeOverlay(modal);
    }
  });
});

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") {
    if (productModal.classList.contains("is-open")) {
      closeProductModal();
    }

    document.querySelectorAll(".overlay-modal.is-open").forEach((modal) => {
      closeOverlay(modal);
    });
  }
});

async function init() {
  try {
    await Promise.all([loadProducts(), loadReviews()]);
    renderCart();
    renderCheckoutSummary();
  } catch (error) {
    productsDiv.innerHTML = `<p class="empty-cart">${error.message}</p>`;
    showToast(error.message);
  }
}

init();
