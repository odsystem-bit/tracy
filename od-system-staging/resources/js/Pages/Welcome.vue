<script setup>
import { Head, Link } from '@inertiajs/vue3';
import { ref, reactive, nextTick, onMounted, onBeforeUnmount, computed } from 'vue';

const props = defineProps({
    vendors_count: { type: Number, default: 0 },
    total_buyers: { type: Number, default: 0 },
    products_count: { type: Number, default: 0 },
    testimonials: { type: Array, default: () => [] },
    shops: { type: Array, default: () => [] },
    trending: { type: Array, default: () => [] },
    categories: { type: Array, default: () => [] },
});

// ── Sidebar ──
const sidebarOpen = ref(true);

// ── Chat ──
const messages = ref([]);
const input = ref('');
const typing = ref(false);
const scrollRef = ref(null);
const inputRef = ref(null);
const hasStarted = ref(false);
const conversationId = ref('conv_' + Date.now().toString(36) + Math.random().toString(36).slice(2, 8));
const fileInputRef = ref(null);
const selectedImage = ref(null); // base64 preview
const stickToBottom = ref(true);
const buyingProduct = ref(null);
const reducedMotion = typeof window !== 'undefined'
    && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
let revealTimer = null;

// ── Guest ID persistant (localStorage) pour la mémoire Tracy ──
function getGuestId() {
    let gid = localStorage.getItem('mantota_guest_id');
    if (!gid) {
        gid = 'web_guest_' + Date.now().toString(36) + Math.random().toString(36).slice(2, 8);
        localStorage.setItem('mantota_guest_id', gid);
    }
    return gid;
}
const guestId = ref(getGuestId());

// ── Checkout ──
const showCheckout = ref(false);
const selectedProduct = ref(null);
const checkoutForm = ref({
    name: '',
    phone: '',
    email: '',
    country: 'BJ',
    city: '',
    landmark: '',
});
const checkoutLoading = ref(false);

const suggestions = [
    { svg: 'shirt', text: 'Trouve-moi des chaussures' },
    { svg: 'smartphone', text: 'Je cherche un téléphone' },
    { svg: 'sparkles', text: 'Des robes pour un mariage' },
    { svg: 'utensils', text: 'Où manger près de moi' },
];

function onScroll() {
    const el = scrollRef.value;
    if (!el) return;
    // Épinglé en bas tant que l'utilisateur reste à <80px du dernier message
    stickToBottom.value = el.scrollHeight - el.scrollTop - el.clientHeight < 80;
}

function scroll() {
    nextTick(() => {
        const el = scrollRef.value;
        if (el) el.scrollTo({ top: el.scrollHeight, behavior: reducedMotion ? 'auto' : 'smooth' });
    });
}

// Suit le flux uniquement si l'utilisateur n'est pas remonté pour relire
function scrollIfPinned() {
    if (stickToBottom.value) scroll();
}

// Révélation progressive des réponses de Tracy (effet machine à écrire, 100% frontend)
function revealMessage(msg) {
    const full = msg.fullText || '';
    if (!full || reducedMotion) {
        msg.text = full;
        msg.revealing = false;
        scroll();
        return;
    }
    // Vitesse adaptative : ~1,9 s maximum même pour les longues réponses
    const step = Math.max(3, Math.ceil(full.length / 120));
    revealTimer = setInterval(() => {
        if (msg.text.length >= full.length) {
            clearInterval(revealTimer);
            revealTimer = null;
            msg.revealing = false;
            scroll();
            return;
        }
        msg.text = full.slice(0, msg.text.length + step);
        scrollIfPinned();
    }, 16);
}

// Termine instantanément une révélation encore en cours avant un nouvel envoi
// (évite les intervalles orphelins et les textes tronqués).
function finishReveals() {
    if (revealTimer) {
        clearInterval(revealTimer);
        revealTimer = null;
    }
    for (const m of messages.value) {
        if (m.revealing) {
            m.text = m.fullText;
            m.revealing = false;
        }
    }
}

function autogrowInput() {
    const el = inputRef.value;
    if (!el) return;
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 120) + 'px';
}

function resetInputHeight() {
    const el = inputRef.value;
    if (el) el.style.height = 'auto';
}

function onFileSelected(e) {
    const file = e.target.files[0];
    if (!file) return;
    if (!file.type.startsWith('image/')) return;
    const reader = new FileReader();
    reader.onload = (ev) => {
        compressImage(ev.target.result)
            .then((dataUrl) => { selectedImage.value = dataUrl; })
            .catch(() => { selectedImage.value = ev.target.result; });
    };
    reader.readAsDataURL(file);
    e.target.value = '';
}

// Redimensionne à 1024 px max et ré-encode en JPEG : une photo de téléphone
// (3-5 Mo) passe à ~150 Ko, sous les limites PHP et de l'API vision.
function compressImage(dataUrl, maxSide = 1024, quality = 0.82) {
    return new Promise((resolve, reject) => {
        const img = new Image();
        img.onload = () => {
            const scale = Math.min(1, maxSide / Math.max(img.width, img.height));
            const canvas = document.createElement('canvas');
            canvas.width = Math.round(img.width * scale);
            canvas.height = Math.round(img.height * scale);
            const ctx = canvas.getContext('2d');
            ctx.fillStyle = '#fff';
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
            resolve(canvas.toDataURL('image/jpeg', quality));
        };
        img.onerror = reject;
        img.src = dataUrl;
    });
}

function clearImage() {
    selectedImage.value = null;
}

async function send(text) {
    const msg = (text || input.value).trim();
    const img = selectedImage.value;
    if ((!msg && !img) || typing.value) return;
    if (!hasStarted.value) hasStarted.value = true;
    finishReveals();
    const displayText = img ? (msg || '📷 Image') : msg;
    messages.value.push({ sender: 'user', text: displayText, image: img });
    input.value = '';
    selectedImage.value = null;
    typing.value = true;
    stickToBottom.value = true;
    resetInputHeight();
    scroll();

    try {
        const res = await fetch('/api/public/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest',
            },
            body: JSON.stringify({
                text: msg || 'Voici une image',
                conversation_id: conversationId.value,
                customer_id: guestId.value,
                country_code: detectedCountry.value,
                city: detectedCity.value,
                image: img,
            }),
        });

        const data = await res.json();
        // reactive() obligatoire : l'intervalle mute msg.text et Vue ne déclenche
        // un re-render que via le proxy — un objet brut resterait figé visuellement.
        const reply = reactive({
            sender: 'tracy',
            text: '',
            fullText: data.text || 'Désolée, je n\'ai pas compris. Peux-tu reformuler ?',
            cards: data.cards || [],
            revealing: true,
        });
        messages.value.push(reply);
        revealMessage(reply);
    } catch (e) {
        messages.value.push({
            sender: 'tracy',
            text: 'Désolée, je rencontre un problème technique. Réessaie dans un instant.',
        });
    } finally {
        typing.value = false;
        scroll();
    }
}

function sendSuggestion(text) { send(text); }
function sendDiscover(name) { send('Je cherche ' + name); }
function sendShop(name) { send('Montre-moi ' + name); }
function sendProduct(name) { send('Je veux ' + name); }
async function buyProduct(name) {
    if (buyingProduct.value) return;
    buyingProduct.value = name;
    try {
        await send('Je veux acheter ' + name);
    } finally {
        buyingProduct.value = null;
    }
}

function closeCheckout() {
    showCheckout.value = false;
    selectedProduct.value = null;
    checkoutLoading.value = false;
}

async function submitCheckout() {
    if (!selectedProduct.value || checkoutLoading.value) return;
    const f = checkoutForm.value;
    if (!f.name.trim() || !f.phone.trim() || !f.city.trim()) {
        alert('Renseigne au moins ton nom, téléphone et ville.');
        return;
    }

    checkoutLoading.value = true;
    try {
        const res = await fetch('/api/public/checkout', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest' },
            body: JSON.stringify({
                product_id: selectedProduct.value.id,
                customer_name: f.name.trim(),
                customer_phone: f.phone.trim(),
                customer_email: f.email.trim() || null,
                country: f.country,
                city: f.city.trim(),
                landmark_indication: f.landmark.trim() || null,
            }),
        });
        const data = await res.json();
        if (!data.success) {
            throw new Error(data.error || 'Erreur de commande');
        }

        hasStarted.value = true;
        messages.value.push({
            sender: 'tracy',
            type: 'order',
            text: `Commande ${data.reference} enregistrée pour ${data.product.name}.`,
            order: data,
        });
        closeCheckout();
        scroll();
    } catch (e) {
        alert(e.message || 'Impossible de créer la commande. Réessaie.');
    } finally {
        checkoutLoading.value = false;
    }
}

// ── Détection du pays du visiteur ──
const detectedCountry = ref(null);
const detectedCity = ref(null);
const countryFlags = { BJ: '🇧🇯', CI: '🇨🇮', SN: '🇸🇳', TG: '🇹🇬', NG: '🇳🇬', GH: '🇬🇭', ML: '🇲🇱', BF: '🇧🇫', NE: '🇳🇪', CM: '🇨🇲', FR: '🇫🇷' };
function countryFlag(code) { return countryFlags[code] || '🌍'; }

onMounted(() => {
    inputRef.value?.focus();
    // Détecter le pays via l'API de géolocalisation
    fetch('https://ipapi.co/json/').then(r => r.json()).then(d => {
        if (d && d.country_code && d.country_code.length === 2) {
            detectedCountry.value = d.country_code;
        }
        if (d && typeof d.city === 'string' && d.city.length <= 100) {
            detectedCity.value = d.city;
        }
    }).catch(() => {});
});

onBeforeUnmount(() => {
    if (revealTimer) clearInterval(revealTimer);
});

// ── Listes localisées : items du pays du visiteur en premier ──
// Mantota est multi-pays : un visiteur de Dakar ne doit pas voir que du Bénin.
function localFirst(list) {
    if (!detectedCountry.value) return list;
    const local = list.filter(i => i.country === detectedCountry.value);
    const others = list.filter(i => i.country !== detectedCountry.value);
    return [...local, ...others];
}
const sortedShops = computed(() => localFirst(props.shops));
const sortedTrending = computed(() => localFirst(props.trending));
</script>

<template>
    <Head title="MANTOTA — Discuter avec Tracy">
        <meta head-key="description" name="description" content="Tracy, votre assistante commerciale IA. Discutez, achetez, vendez et payez par la conversation." />
    </Head>

    <div class="flex h-[100dvh] flex-col bg-white">

        <!-- ══════ TOP BAR ══════ -->
        <header class="relative z-30 flex items-center justify-between border-b border-surface-3 bg-white px-4 py-2.5 sm:px-6">
            <div class="flex items-center gap-3">
                <!-- Sidebar toggle -->
                <button @click="sidebarOpen = !sidebarOpen" class="rounded-lg p-1.5 text-grey-2 hover:bg-surface-1 transition">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5" /></svg>
                </button>
                <!-- Mantota logo -->
                <img src="/images/mantota-logo.png" alt="Mantota" class="h-9 w-9 rounded-xl" />
                <span class="text-base font-extrabold text-grey-1 tracking-tight hidden sm:inline">Mantota</span>
            </div>

            <!-- Tracy -->
            <div class="flex items-center gap-2.5">
                <span class="text-xs font-semibold text-grey-2 hidden sm:inline">Discuter avec</span>
                <div class="relative">
                    <img src="/images/tracy-avatar.jpeg" alt="Tracy" class="h-8 w-8 rounded-full object-cover ring-2 ring-mantota-teal/30" />
                    <span class="absolute -bottom-0.5 -right-0.5 h-2.5 w-2.5 rounded-full bg-mantota-teal ring-2 ring-white"></span>
                </div>
                <div class="hidden sm:block text-left">
                    <p class="text-xs font-bold text-grey-1 leading-none">Tracy</p>
                    <p class="text-[10px] text-mantota-teal font-semibold leading-none mt-0.5">En ligne</p>
                </div>
            </div>
        </header>

        <!-- ══════ MAIN ══════ -->
        <div class="flex flex-1 overflow-hidden">

            <!-- ══════ SIDEBAR — Découvrir ══════ -->
            <Transition
                enter-active-class="transition-all duration-200 ease-out"
                enter-from-class="w-0 opacity-0"
                enter-to-class="w-72 opacity-100"
                leave-active-class="transition-all duration-150 ease-in"
                leave-from-class="w-72 opacity-100"
                leave-to-class="w-0 opacity-0"
            >
                <aside v-show="sidebarOpen" class="hidden md:flex w-72 flex-col border-r border-surface-3 bg-surface-1 overflow-hidden flex-shrink-0">
                    <div class="flex-1 overflow-y-auto sidebar-scroll">

                        <!-- Catégories -->
                        <div class="px-4 pt-5 pb-2">
                            <p class="text-[11px] font-semibold text-grey-3 mb-3 flex items-center gap-1.5">
                                <svg class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35" stroke-linecap="round"/></svg>
                                Catégories
                            </p>
                        </div>
                        <div class="flex gap-2 px-4 pb-4 overflow-x-auto sidebar-scroll">
                            <button v-for="cat in props.categories" :key="cat.name"
                                @click="sendDiscover(cat.name)"
                                class="flex-shrink-0 flex flex-col items-center gap-1.5 rounded-xl border border-surface-3 bg-white px-3.5 py-2.5 transition hover:border-mantota-teal/30 hover:bg-mantota-teal-pale/30 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-mantota-teal/40"
                            >
                                <svg class="h-5 w-5 text-mantota-teal" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                                    <path v-if="cat.svg === 'shirt'" stroke-linecap="round" stroke-linejoin="round" d="M15.75 10.5V6a3.75 3.75 0 10-7.5 0v4.5m11.356-1.993l1.263 12c.07.665-.45 1.243-1.119 1.243H4.25a1.125 1.125 0 01-1.12-1.243l1.264-12A1.125 1.125 0 015.513 7.5h12.974c.576 0 1.059.435 1.119 1.007z"/>
                                    <path v-if="cat.svg === 'smartphone'" stroke-linecap="round" stroke-linejoin="round" d="M10.5 1.5H8.25A2.25 2.25 0 006 3.75v16.5a2.25 2.25 0 002.25 2.25h7.5A2.25 2.25 0 0018 20.25V3.75a2.25 2.25 0 00-2.25-2.25H13.5m-3 0V3h3V1.5m-3 0h3m-6 18.75h6"/>
                                    <path v-if="cat.svg === 'utensils'" stroke-linecap="round" stroke-linejoin="round" d="M12 8.25v-1.5m0 1.5c-1.355 0-2.697.056-4.024.166C6.845 8.51 6 9.473 6 10.608v2.513m6-4.87c1.355 0 2.697.055 4.024.165C17.155 8.51 18 9.473 18 10.608v2.513M15 8.25v-1.5m-6 1.5v-1.5m12 9.75l-1.5.75a3.354 3.354 0 01-3 0 3.354 3.354 0 00-3 0 3.354 3.354 0 01-3 0 3.354 3.354 0 00-3 0 3.354 3.354 0 01-3 0L3 16.5m15-3.38a48.474 48.474 0 00-6-.37c-2.032 0-4.034.125-6 .37"/>
                                    <path v-if="cat.svg === 'sparkles'" stroke-linecap="round" stroke-linejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 00-2.455 2.456zM16.894 20.567L16.5 21.75l-.394-1.183a2.25 2.25 0 00-1.423-1.423L13.5 18.75l1.183-.394a2.25 2.25 0 001.423-1.423l.394-1.183.394 1.183a2.25 2.25 0 001.423 1.423l1.183.394-1.183.394a2.25 2.25 0 00-1.423 1.423z"/>
                                    <path v-if="cat.svg === 'home'" stroke-linecap="round" stroke-linejoin="round" d="M2.25 12l8.954-8.955c.44-.439 1.152-.439 1.591 0L21.75 12M4.5 9.75v10.125c0 .621.504 1.125 1.125 1.125H9.75v-4.875c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21h4.125c.621 0 1.125-.504 1.125-1.125V9.75M8.25 21h8.25"/>
                                    <path v-if="cat.svg === 'tag'" stroke-linecap="round" stroke-linejoin="round" d="M15.41 4.93 8.59.93a2.25 2.25 0 0 0-3.18.53l-3.5 4.67a2.25 2.25 0 0 0 .53 3.18l6.82 5c.87.64 2.07.5 2.77-.32l3.5-4.67a2.25 2.25 0 0 0-.53-3.18Z"/>
                                </svg>
                                <span class="text-[10px] font-semibold text-grey-3">{{ cat.name }}</span>
                            </button>
                        </div>

                        <!-- Boutiques populaires -->
                        <div class="px-4 pb-2">
                            <p class="text-[11px] font-semibold text-grey-3 mb-3 flex items-center gap-1.5">
                                <svg class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M13.5 21v-7.5a.75.75 0 01.75-.75h3a.75.75 0 01.75.75V21m-4.5 0H2.36m11.14 0H18m0 0h3.64m-1.39 0V9.349m-16.5 11.65V9.35m0 0a3.001 3.001 0 003.75-.615A2.993 2.993 0 009.75 9.75c.896 0 1.7-.393 2.25-1.016a2.993 2.993 0 002.25 1.016c.896 0 1.7-.393 2.25-1.016a3.001 3.001 0 003.75.614m-16.5 0a3.004 3.004 0 01-.621-4.72L4.318 3.44A1.5 1.5 0 015.378 3h13.243a1.5 1.5 0 011.06.44l1.19 1.189a3 3 0 01-.621 4.72m-13.5 8.65h3.75a.75.75 0 00.75-.75V13.5a.75.75 0 00-.75-.75H6.75a.75.75 0 00-.75.75v3.75c0 .415.336.75.75.75z"/></svg>
                                Boutiques populaires
                            </p>
                        </div>
                        <div class="space-y-1.5 px-3 pb-4">
                            <button v-for="shop in sortedShops" :key="shop.name"
                                @click="sendShop(shop.name)"
                                class="flex w-full items-center gap-2.5 rounded-xl px-3 py-2.5 text-left transition-colors hover:bg-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-mantota-teal/40"
                            >
                                <div class="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg overflow-hidden" :class="shop.image_url ? '' : 'bg-mantota-teal-pale'">
                                    <img v-if="shop.image_url" :src="shop.image_url" :alt="shop.name" class="h-full w-full object-cover" />
                                    <svg v-else class="h-4 w-4 text-mantota-teal" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M13.5 21v-7.5a.75.75 0 01.75-.75h3a.75.75 0 01.75.75V21m-4.5 0H2.36m11.14 0H18m0 0h3.64m-1.39 0V9.349m-16.5 11.65V9.35m0 0a3.001 3.001 0 003.75-.615A2.993 2.993 0 009.75 9.75c.896 0 1.7-.393 2.25-1.016a2.993 2.993 0 002.25 1.016c.896 0 1.7-.393 2.25-1.016a3.001 3.001 0 003.75.614m-16.5 0a3.004 3.004 0 01-.621-4.72L4.318 3.44A1.5 1.5 0 015.378 3h13.243a1.5 1.5 0 011.06.44l1.19 1.189a3 3 0 01-.621 4.72m-13.5 8.65h3.75a.75.75 0 00.75-.75V13.5a.75.75 0 00-.75-.75H6.75a.75.75 0 00-.75.75v3.75c0 .415.336.75.75.75z"/></svg>
                                </div>
                                <div class="flex-1 min-w-0">
                                    <p class="text-xs font-bold text-grey-1 truncate">{{ shop.name }}</p>
                                    <p class="text-[10px] text-grey-4 truncate">{{ shop.category }} · {{ countryFlag(shop.country) }} {{ shop.location }}</p>
                                </div>
                                <div class="flex items-center gap-0.5 text-[10px] font-semibold text-mantota-teal">
                                    <svg class="h-3 w-3" fill="currentColor" viewBox="0 0 20 20"><path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z"/></svg>
                                    {{ shop.rating }}
                                </div>
                            </button>
                        </div>

                        <!-- Produits tendance -->
                        <div class="px-4 pb-2">
                            <p class="text-[11px] font-semibold text-grey-3 mb-3 flex items-center gap-1.5">
                                <svg class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M2.25 18L9 11.25l4.306 4.307a11.95 11.95 0 015.814-5.519l2.74-1.22m0 0l-5.94-2.28m5.94 2.28l-2.28 5.941"/></svg>
                                Produits tendance
                            </p>
                        </div>
                        <div class="grid grid-cols-2 gap-2 px-3 pb-4">
                            <div v-for="p in props.trending" :key="p.name"
                                class="rounded-xl border border-surface-3 bg-white overflow-hidden text-left transition hover:border-mantota-teal/30 hover:shadow-mantota"
                            >
                                <button @click="sendProduct(p.name)" class="block w-full h-20 overflow-hidden focus-visible:outline-none" :class="p.image_url ? '' : 'flex items-center justify-center bg-mantota-teal-pale'">
                                    <img v-if="p.image_url" :src="p.image_url" :alt="p.name" class="h-full w-full object-cover" />
                                    <svg v-else class="h-6 w-6 text-mantota-teal/40" fill="none" viewBox="0 0 24 24" stroke-width="1" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M15.75 10.5V6a3.75 3.75 0 10-7.5 0v4.5m11.356-1.993l1.263 12c.07.665-.45 1.243-1.119 1.243H4.25a1.125 1.125 0 01-1.12-1.243l1.264-12A1.125 1.125 0 015.513 7.5h12.974c.576 0 1.059.435 1.119 1.007z"/></svg>
                                </button>
                                <div class="px-2.5 py-2">
                                    <p class="text-[10px] font-bold text-grey-1 truncate">{{ p.name }}</p>
                                    <div class="flex items-center justify-between mt-0.5">
                                        <p class="text-xs font-extrabold text-mantota-teal">{{ p.price }}</p>
                                        <button @click.stop="buyProduct(p.name)" :disabled="!!buyingProduct" class="rounded-md bg-mantota-coral px-2 py-0.5 text-[10px] font-bold text-white transition hover:bg-mantota-coral/90 disabled:opacity-60">{{ buyingProduct === p.name ? 'Envoi…' : 'Acheter' }}</button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Download + Legal -->
                    <div class="border-t border-surface-3 px-3 py-3 space-y-2.5 flex-shrink-0">
                        <a href="#" class="flex items-center gap-2 rounded-xl bg-mantota-teal px-3.5 py-2.5 text-xs font-bold text-white shadow-teal transition hover:bg-mantota-teal-dark">
                            <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" /></svg>
                            Télécharger l'app
                        </a>
                        <div class="flex flex-wrap gap-x-3 gap-y-1">
                            <a :href="route('about')" class="text-[10px] text-grey-4 hover:text-mantota-teal transition">À propos</a>
                            <a :href="route('tarifs')" class="text-[10px] text-grey-4 hover:text-mantota-teal transition">Tarifs</a>
                            <a :href="route('documentation')" class="text-[10px] text-grey-4 hover:text-mantota-teal transition">Documentation</a>
                            <a :href="route('support.create')" class="text-[10px] text-grey-4 hover:text-mantota-teal transition">Support</a>
                            <a :href="route('legal.terms')" class="text-[10px] text-grey-4 hover:text-mantota-teal transition">CGV</a>
                            <a :href="route('legal.privacy')" class="text-[10px] text-grey-4 hover:text-mantota-teal transition">Confidentialité</a>
                        </div>
                    </div>
                </aside>
            </Transition>

            <!-- Mobile sidebar -->
            <Transition
                enter-active-class="transition duration-200 ease-out"
                enter-from-class="-translate-x-full"
                enter-to-class="translate-x-0"
                leave-active-class="transition duration-150 ease-in"
                leave-from-class="translate-x-0"
                leave-to-class="-translate-x-full"
            >
                <aside v-if="sidebarOpen" class="fixed inset-y-0 left-0 z-40 flex w-72 flex-col border-r border-surface-3 bg-white shadow-mantota-lg md:hidden overflow-hidden">
                    <div class="flex items-center justify-between border-b border-surface-3 px-4 py-3">
                        <div class="flex items-center gap-2">
                            <img src="/images/mantota-logo.png" alt="Mantota" class="h-8 w-8 rounded-xl" />
                            <span class="text-sm font-extrabold text-grey-1">Mantota</span>
                        </div>
                        <button @click="sidebarOpen = false" class="rounded-lg p-1 text-grey-2 hover:bg-surface-1">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" /></svg>
                        </button>
                    </div>
                    <div class="flex-1 overflow-y-auto sidebar-scroll">
                        <!-- Catégories -->
                        <div class="px-4 pt-5 pb-2">
                            <p class="text-[11px] font-semibold text-grey-3 mb-3 flex items-center gap-1.5">
                                <svg class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35" stroke-linecap="round"/></svg>
                                Catégories
                            </p>
                        </div>
                        <div class="flex gap-2 px-4 pb-4 overflow-x-auto sidebar-scroll">
                            <button v-for="cat in props.categories" :key="cat.name"
                                @click="sendDiscover(cat.name); sidebarOpen = false"
                                class="flex-shrink-0 flex flex-col items-center gap-1.5 rounded-xl border border-surface-3 bg-surface-1 px-3.5 py-2.5 transition hover:border-mantota-teal/30 hover:bg-mantota-teal-pale/30 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-mantota-teal/40"
                            >
                                <svg class="h-5 w-5 text-mantota-teal" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                                    <path v-if="cat.svg === 'shirt'" stroke-linecap="round" stroke-linejoin="round" d="M15.75 10.5V6a3.75 3.75 0 10-7.5 0v4.5m11.356-1.993l1.263 12c.07.665-.45 1.243-1.119 1.243H4.25a1.125 1.125 0 01-1.12-1.243l1.264-12A1.125 1.125 0 015.513 7.5h12.974c.576 0 1.059.435 1.119 1.007z"/>
                                    <path v-if="cat.svg === 'smartphone'" stroke-linecap="round" stroke-linejoin="round" d="M10.5 1.5H8.25A2.25 2.25 0 006 3.75v16.5a2.25 2.25 0 002.25 2.25h7.5A2.25 2.25 0 0018 20.25V3.75a2.25 2.25 0 00-2.25-2.25H13.5m-3 0V3h3V1.5m-3 0h3m-6 18.75h6"/>
                                    <path v-if="cat.svg === 'utensils'" stroke-linecap="round" stroke-linejoin="round" d="M12 8.25v-1.5m0 1.5c-1.355 0-2.697.056-4.024.166C6.845 8.51 6 9.473 6 10.608v2.513m6-4.87c1.355 0 2.697.055 4.024.165C17.155 8.51 18 9.473 18 10.608v2.513M15 8.25v-1.5m-6 1.5v-1.5m12 9.75l-1.5.75a3.354 3.354 0 01-3 0 3.354 3.354 0 00-3 0 3.354 3.354 0 01-3 0 3.354 3.354 0 00-3 0 3.354 3.354 0 01-3 0L3 16.5m15-3.38a48.474 48.474 0 00-6-.37c-2.032 0-4.034.125-6 .37"/>
                                    <path v-if="cat.svg === 'sparkles'" stroke-linecap="round" stroke-linejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 00-2.455 2.456zM16.894 20.567L16.5 21.75l-.394-1.183a2.25 2.25 0 00-1.423-1.423L13.5 18.75l1.183-.394a2.25 2.25 0 001.423-1.423l.394-1.183.394 1.183a2.25 2.25 0 001.423 1.423l1.183.394-1.183.394a2.25 2.25 0 00-1.423 1.423z"/>
                                    <path v-if="cat.svg === 'home'" stroke-linecap="round" stroke-linejoin="round" d="M2.25 12l8.954-8.955c.44-.439 1.152-.439 1.591 0L21.75 12M4.5 9.75v10.125c0 .621.504 1.125 1.125 1.125H9.75v-4.875c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21h4.125c.621 0 1.125-.504 1.125-1.125V9.75M8.25 21h8.25"/>
                                    <path v-if="cat.svg === 'tag'" stroke-linecap="round" stroke-linejoin="round" d="M15.41 4.93 8.59.93a2.25 2.25 0 0 0-3.18.53l-3.5 4.67a2.25 2.25 0 0 0 .53 3.18l6.82 5c.87.64 2.07.5 2.77-.32l3.5-4.67a2.25 2.25 0 0 0-.53-3.18Z"/>
                                </svg>
                                <span class="text-[10px] font-semibold text-grey-3">{{ cat.name }}</span>
                            </button>
                        </div>
                        <!-- Boutiques -->
                        <div class="px-4 pb-2">
                            <p class="text-[11px] font-semibold text-grey-3 mb-3">Boutiques populaires</p>
                        </div>
                        <div class="space-y-1.5 px-3 pb-4">
                            <button v-for="shop in sortedShops" :key="shop.name"
                                @click="sendShop(shop.name); sidebarOpen = false"
                                class="flex w-full items-center gap-2.5 rounded-xl px-3 py-2.5 text-left transition-colors hover:bg-surface-1 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-mantota-teal/40"
                            >
                                <div class="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg overflow-hidden" :class="shop.image_url ? '' : 'bg-mantota-teal-pale'">
                                    <img v-if="shop.image_url" :src="shop.image_url" :alt="shop.name" class="h-full w-full object-cover" />
                                    <svg v-else class="h-4 w-4 text-mantota-teal" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M13.5 21v-7.5a.75.75 0 01.75-.75h3a.75.75 0 01.75.75V21m-4.5 0H2.36m11.14 0H18m0 0h3.64m-1.39 0V9.349m-16.5 11.65V9.35m0 0a3.001 3.001 0 003.75-.615A2.993 2.993 0 009.75 9.75c.896 0 1.7-.393 2.25-1.016a2.993 2.993 0 002.25 1.016c.896 0 1.7-.393 2.25-1.016a3.001 3.001 0 003.75.614m-16.5 0a3.004 3.004 0 01-.621-4.72L4.318 3.44A1.5 1.5 0 015.378 3h13.243a1.5 1.5 0 011.06.44l1.19 1.189a3 3 0 01-.621 4.72m-13.5 8.65h3.75a.75.75 0 00.75-.75V13.5a.75.75 0 00-.75-.75H6.75a.75.75 0 00-.75.75v3.75c0 .415.336.75.75.75z"/></svg>
                                </div>
                                <div class="flex-1 min-w-0">
                                    <p class="text-xs font-bold text-grey-1 truncate">{{ shop.name }}</p>
                                    <p class="text-[10px] text-grey-4 truncate">{{ shop.category }} · {{ countryFlag(shop.country) }} {{ shop.location }}</p>
                                </div>
                                <div class="flex items-center gap-0.5 text-[10px] font-semibold text-mantota-teal">
                                    <svg class="h-3 w-3" fill="currentColor" viewBox="0 0 20 20"><path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z"/></svg>
                                    {{ shop.rating }}
                                </div>
                            </button>
                        </div>
                        <!-- Download -->
                        <div class="px-3 pb-4">
                            <a href="#" class="flex items-center gap-2 rounded-xl bg-mantota-teal px-3.5 py-2.5 text-xs font-bold text-white shadow-teal transition hover:bg-mantota-teal-dark">
                                <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" /></svg>
                                Télécharger l'app
                            </a>
                        </div>
                    </div>
                    <div class="border-t border-surface-3 px-4 py-3 flex flex-wrap gap-x-3 gap-y-1">
                        <a :href="route('about')" class="text-[10px] text-grey-4 hover:text-mantota-teal transition">À propos</a>
                        <a :href="route('tarifs')" class="text-[10px] text-grey-4 hover:text-mantota-teal transition">Tarifs</a>
                        <a :href="route('documentation')" class="text-[10px] text-grey-4 hover:text-mantota-teal transition">Documentation</a>
                        <a :href="route('support.create')" class="text-[10px] text-grey-4 hover:text-mantota-teal transition">Support</a>
                        <a :href="route('legal.terms')" class="text-[10px] text-grey-4 hover:text-mantota-teal transition">CGV</a>
                        <a :href="route('legal.privacy')" class="text-[10px] text-grey-4 hover:text-mantota-teal transition">Confidentialité</a>
                    </div>
                </aside>
            </Transition>
            <div v-if="sidebarOpen" @click="sidebarOpen = false" class="fixed inset-0 z-30 bg-black/20 backdrop-blur-sm md:hidden"></div>

            <!-- ══════ CHAT ══════ -->
            <div class="relative flex flex-1 flex-col overflow-hidden">
                <div class="adinkra-bg absolute inset-0 pointer-events-none"></div>

                <!-- Messages -->
                <div ref="scrollRef" @scroll.passive="onScroll" class="relative z-10 flex-1 overflow-y-auto" aria-live="polite">
                    <div class="mx-auto max-w-3xl px-4 py-8">

                        <!-- Empty state -->
                        <div v-if="!hasStarted" class="flex flex-col items-center pt-6 sm:pt-14">
                            <img src="/images/tracy-avatar.jpeg" alt="Tracy" class="mb-4 h-20 w-20 rounded-full object-cover shadow-mantota-lg ring-3 ring-mantota-teal/20" />
                            <h1 class="text-xl font-extrabold text-grey-1 sm:text-2xl">Salut, je suis Tracy</h1>
                            <p class="mt-1 text-xs font-semibold text-mantota-teal">Assistante commerciale Mantota</p>
                            <p class="mt-4 text-center text-sm text-grey-2 max-w-sm leading-relaxed">
                                Dis-moi ce que tu cherches. Je trouve les boutiques, je négocie, je crée ta commande.
                            </p>
                            <div class="mt-8 grid w-full max-w-lg grid-cols-2 gap-2.5">
                                <button v-for="s in suggestions" :key="s.text"
                                    @click="sendSuggestion(s.text)"
                                    class="flex items-center gap-2.5 rounded-xl border border-surface-3 bg-white px-3.5 py-3 text-left text-sm font-medium text-grey-3 transition-all hover:border-mantota-teal/20 hover:bg-mantota-teal-pale/30 hover:text-grey-1"
                                >
                                    <svg class="h-5 w-5 text-mantota-teal flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                                        <path v-if="s.svg === 'shirt'" stroke-linecap="round" stroke-linejoin="round" d="M15.75 10.5V6a3.75 3.75 0 10-7.5 0v4.5m11.356-1.993l1.263 12c.07.665-.45 1.243-1.119 1.243H4.25a1.125 1.125 0 01-1.12-1.243l1.264-12A1.125 1.125 0 015.513 7.5h12.974c.576 0 1.059.435 1.119 1.007z"/>
                                        <path v-if="s.svg === 'smartphone'" stroke-linecap="round" stroke-linejoin="round" d="M10.5 1.5H8.25A2.25 2.25 0 006 3.75v16.5a2.25 2.25 0 002.25 2.25h7.5A2.25 2.25 0 0018 20.25V3.75a2.25 2.25 0 00-2.25-2.25H13.5m-3 0V3h3V1.5m-3 0h3m-6 18.75h6"/>
                                        <path v-if="s.svg === 'sparkles'" stroke-linecap="round" stroke-linejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z"/>
                                        <path v-if="s.svg === 'utensils'" stroke-linecap="round" stroke-linejoin="round" d="M12 8.25v-1.5m0 1.5c-1.355 0-2.697.056-4.024.166C6.845 8.51 6 9.473 6 10.608v2.513m6-4.87c1.355 0 2.697.055 4.024.165C17.155 8.51 18 9.473 18 10.608v2.513M15 8.25v-1.5m-6 1.5v-1.5m12 9.75l-1.5.75a3.354 3.354 0 01-3 0 3.354 3.354 0 00-3 0 3.354 3.354 0 01-3 0 3.354 3.354 0 00-3 0 3.354 3.354 0 01-3 0L3 16.5m15-3.38a48.474 48.474 0 00-6-.37c-2.032 0-4.034.125-6 .37"/>
                                    </svg>
                                    <span class="text-xs">{{ s.text }}</span>
                                </button>
                            </div>
                        </div>

                        <!-- Messages list -->
                        <div v-else class="space-y-5 pb-6">
                            <div v-for="(msg, i) in messages" :key="i" class="flex gap-3" :class="msg.sender === 'user' ? 'flex-row-reverse' : ''">
                                <div class="flex-shrink-0 pt-1">
                                    <img v-if="msg.sender === 'tracy'" src="/images/tracy-avatar.jpeg" alt="Tracy" class="h-7 w-7 rounded-full object-cover ring-1 ring-mantota-teal/20" />
                                    <div v-else class="flex h-7 w-7 items-center justify-center rounded-full bg-surface-3 text-[10px] font-bold text-grey-2">
                                        <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z"/></svg>
                                    </div>
                                </div>
                                <div class="flex flex-col gap-0.5 max-w-[80%]" :class="msg.sender === 'user' ? 'items-end' : ''">
                                    <span v-if="msg.sender === 'tracy'" class="text-[10px] font-bold text-mantota-teal flex items-center gap-1">
                                        Tracy
                                        <span class="h-1.5 w-1.5 rounded-full bg-mantota-teal"></span>
                                    </span>
                                    <img v-if="msg.image" :src="msg.image" alt="Image envoyée" class="rounded-xl max-w-[200px] max-h-[200px] object-cover mb-1" />
                                    <div v-if="msg.text || msg.revealing" class="whitespace-pre-wrap rounded-2xl px-3.5 py-2 text-sm leading-relaxed" :class="msg.sender === 'user' ? 'rounded-tr-md bg-mantota-teal text-white' : 'rounded-tl-md bg-surface-1 text-grey-1'">
                                        {{ msg.text }}<span v-if="msg.revealing" class="typing-cursor" aria-hidden="true"></span>
                                    </div>
                                    <div v-if="msg.sender === 'tracy' && msg.cards && msg.cards.length && !msg.revealing" class="mt-2.5 grid grid-cols-1 sm:grid-cols-2 gap-2">
                                        <div v-for="p in msg.cards" :key="p.id" class="rounded-xl border border-surface-3 bg-white p-2.5 min-w-[160px]">
                                            <div class="h-16 flex items-center justify-center rounded-lg overflow-hidden" :class="p.image_url ? '' : 'bg-mantota-teal-pale'">
                                                <img v-if="p.image_url" :src="p.image_url" :alt="p.name" class="h-full w-full object-cover" />
                                                <svg v-else class="h-6 w-6 text-mantota-teal/40" fill="none" viewBox="0 0 24 24" stroke-width="1" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M15.75 10.5V6a3.75 3.75 0 10-7.5 0v4.5m11.356-1.993l1.263 12c.07.665-.45 1.243-1.119 1.243H4.25a1.125 1.125 0 01-1.12-1.243l1.264-12A1.125 1.125 0 015.513 7.5h12.974c.576 0 1.059.435 1.119 1.007z"/></svg>
                                            </div>
                                            <p class="text-[10px] font-bold text-grey-1 truncate mt-1.5">{{ p.name }}</p>
                                            <p class="text-xs font-extrabold text-mantota-teal">{{ p.price }}</p>
                                            <p v-if="p.stock <= 5" class="text-[10px] text-mantota-coral">Stock: {{ p.stock }}</p>
                                            <button @click="buyProduct(p.name)" :disabled="!!buyingProduct || p.stock <= 0" class="mt-1.5 flex w-full items-center justify-center gap-1.5 rounded-lg px-2 py-1.5 text-[10px] font-bold text-white transition disabled:opacity-60 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-mantota-coral/50" :class="p.stock <= 0 ? 'bg-surface-3 text-grey-4 cursor-not-allowed' : 'bg-mantota-coral hover:bg-mantota-coral/90'">
                                                <svg v-if="buyingProduct === p.name" class="h-3 w-3 animate-spin" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg>
                                                {{ p.stock <= 0 ? 'Épuisé' : (buyingProduct === p.name ? 'Envoi…' : 'Commander') }}
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <!-- Typing -->
                            <div v-if="typing" class="flex gap-3">
                                <div class="flex-shrink-0 pt-1">
                                    <img src="/images/tracy-avatar.jpeg" alt="Tracy" class="h-7 w-7 rounded-full object-cover ring-1 ring-mantota-teal/20" />
                                </div>
                                <div class="flex flex-col gap-0.5">
                                    <span class="text-[10px] font-bold text-mantota-teal flex items-center gap-1">
                                        <span class="h-1.5 w-1.5 rounded-full bg-mantota-teal"></span> Tracy
                                    </span>
                                    <div class="flex items-center gap-1.5 rounded-2xl rounded-tl-md bg-mantota-teal-pale border border-mantota-teal/15 px-4 py-3">
                                        <span class="h-2 w-2 rounded-full bg-mantota-teal animate-bounce" style="animation-delay:0s"></span>
                                        <span class="h-2 w-2 rounded-full bg-mantota-teal animate-bounce" style="animation-delay:0.15s"></span>
                                        <span class="h-2 w-2 rounded-full bg-mantota-teal animate-bounce" style="animation-delay:0.3s"></span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Input bar -->
                <div class="relative z-10 border-t border-surface-3 bg-white/80 backdrop-blur-sm">
                    <div class="mx-auto max-w-3xl px-4 py-3">
                        <!-- Image preview -->
                        <div v-if="selectedImage" class="mb-2 flex items-center gap-2 rounded-xl border border-surface-3 bg-surface-1 p-2">
                            <img :src="selectedImage" alt="Aperçu" class="h-12 w-12 rounded-lg object-cover" />
                            <span class="text-xs text-grey-2 flex-1">Image prête à envoyer</span>
                            <button @click="clearImage" class="rounded-lg p-1 text-grey-3 hover:bg-surface-2">
                                <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12"/></svg>
                            </button>
                        </div>
                        <div class="flex items-end gap-2 rounded-2xl border border-surface-3 bg-surface-1 px-4 py-2 transition focus-within:border-mantota-teal/40 focus-within:ring-2 focus-within:ring-mantota-teal/10">
                            <input ref="fileInputRef" type="file" accept="image/*" class="hidden" @change="onFileSelected" />
                            <button @click="fileInputRef?.click()" class="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg text-grey-3 hover:bg-surface-2 hover:text-mantota-teal transition">
                                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M18.375 12.75h-7.5m0 0l3-3m-3 3l3 3m-7.5-3h7.5M3 12a9 9 0 1118 0 9 9 0 01-18 0z"/></svg>
                            </button>
                            <textarea
                                ref="inputRef"
                                v-model="input"
                                rows="1"
                                placeholder="Écris à Tracy..."
                                @input="autogrowInput"
                                @keydown.enter.exact.prevent="send()"
                                class="max-h-[120px] flex-1 resize-none bg-transparent py-1 text-sm leading-relaxed text-grey-1 placeholder:text-grey-4 focus:outline-none"
                            ></textarea>
                            <button
                                @click="send()"
                                :disabled="(!input.trim() && !selectedImage) || typing"
                                class="mb-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-mantota-teal text-white transition enabled:hover:bg-mantota-teal-dark disabled:opacity-30 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-mantota-teal/50"
                            >
                                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke-width="2.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5" /></svg>
                            </button>
                        </div>
                        <p class="mt-1.5 text-center text-[10px] text-grey-4">
                            Chat éphémère — pas de compte requis. Les messages ne sont pas sauvegardés.
                        </p>
                    </div>
                </div>
            </div>
        </div>

        <!-- Checkout Modal -->
        <div v-if="showCheckout" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
            <div class="w-full max-w-sm rounded-2xl bg-white p-5 shadow-2xl">
                <div class="flex items-center justify-between mb-4">
                    <h2 class="text-sm font-extrabold text-grey-1">Commander {{ selectedProduct?.name }}</h2>
                    <button @click="closeCheckout" class="rounded-lg p-1 text-grey-4 hover:bg-surface-1">
                        <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12"/></svg>
                    </button>
                </div>
                <p class="text-xs text-grey-3 mb-4">Renseigne tes coordonnées pour la livraison.</p>
                <div class="space-y-3">
                    <input v-model="checkoutForm.name" type="text" placeholder="Nom complet" class="w-full rounded-xl border border-surface-3 bg-surface-1 px-3.5 py-2.5 text-xs text-grey-1 placeholder:text-grey-4 focus:outline-none focus:border-mantota-teal/50" />
                    <input v-model="checkoutForm.phone" type="tel" placeholder="Téléphone" class="w-full rounded-xl border border-surface-3 bg-surface-1 px-3.5 py-2.5 text-xs text-grey-1 placeholder:text-grey-4 focus:outline-none focus:border-mantota-teal/50" />
                    <input v-model="checkoutForm.email" type="email" placeholder="Email (optionnel)" class="w-full rounded-xl border border-surface-3 bg-surface-1 px-3.5 py-2.5 text-xs text-grey-1 placeholder:text-grey-4 focus:outline-none focus:border-mantota-teal/50" />
                    <input v-model="checkoutForm.city" type="text" placeholder="Ville" class="w-full rounded-xl border border-surface-3 bg-surface-1 px-3.5 py-2.5 text-xs text-grey-1 placeholder:text-grey-4 focus:outline-none focus:border-mantota-teal/50" />
                    <input v-model="checkoutForm.landmark" type="text" placeholder="Point de repère (optionnel)" class="w-full rounded-xl border border-surface-3 bg-surface-1 px-3.5 py-2.5 text-xs text-grey-1 placeholder:text-grey-4 focus:outline-none focus:border-mantota-teal/50" />
                </div>
                <div class="mt-5 flex gap-2">
                    <button @click="closeCheckout" class="flex-1 rounded-xl border border-surface-3 bg-surface-1 py-2.5 text-xs font-bold text-grey-2 hover:bg-surface-2">Annuler</button>
                    <button @click="submitCheckout" :disabled="checkoutLoading" class="flex-1 rounded-xl bg-mantota-teal py-2.5 text-xs font-bold text-white hover:bg-mantota-teal-dark disabled:opacity-50">
                        <span v-if="checkoutLoading">Commande...</span>
                        <span v-else>Commander ({{ selectedProduct?.raw_price?.toLocaleString() }} F)</span>
                    </button>
                </div>
            </div>
        </div>
    </div>
</template>

<style scoped>
.adinkra-bg {
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='80' height='80'%3E%3Cg fill='none' stroke='%230BBFA0' stroke-width='0.8'%3E%3Ccircle cx='40' cy='40' r='16'/%3E%3Ccircle cx='40' cy='40' r='8'/%3E%3Cpath d='M40 24L40 10M40 56L40 70M24 40L10 40M56 40L70 40'/%3E%3Cpath d='M29 29L18 18M51 51L62 62M51 29L62 18M29 51L18 62'/%3E%3Ccircle cx='40' cy='40' r='28' stroke-dasharray='4 5'/%3E%3Cpath d='M40 12 L44 20 L40 18 L36 20 Z'/%3E%3C/g%3E%3C/svg%3E");
    background-size: 80px 80px;
    opacity: 0.08;
}

.ring-3 {
    --tw-ring-offset-shadow: var(--tw-ring-inset) 0 0 0 var(--tw-ring-offset-width) var(--tw-ring-offset-color);
    --tw-ring-shadow: var(--tw-ring-inset) 0 0 0 calc(3px + var(--tw-ring-offset-width)) var(--tw-ring-color);
    box-shadow: var(--tw-ring-offset-shadow), var(--tw-ring-shadow), var(--tw-shadow, 0 0 #0000);
}

.sidebar-scroll::-webkit-scrollbar { width: 3px; height: 3px; }
.sidebar-scroll::-webkit-scrollbar-track { background: transparent; }
.sidebar-scroll::-webkit-scrollbar-thumb { background: rgba(11,191,160,0.15); border-radius: 3px; }

/* Curseur de frappe pendant la révélation progressive des réponses */
.typing-cursor {
    display: inline-block;
    width: 7px;
    height: 1em;
    margin-left: 2px;
    border-radius: 1px;
    background: #0BBFA0;
    vertical-align: text-bottom;
    animation: cursor-blink 0.9s steps(2, start) infinite;
}
@keyframes cursor-blink {
    50% { opacity: 0; }
}

@media (prefers-reduced-motion: reduce) {
    .animate-bounce,
    .typing-cursor { animation: none; }
}
</style>
