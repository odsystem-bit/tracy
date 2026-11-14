<script setup>
import { Head, router, usePage, Link } from '@inertiajs/vue3';
import { computed, ref, onMounted, nextTick } from 'vue';

const props = defineProps({
    vendor:   { type: Object, required: true },
    products: { type: Array, default: () => [] },
});

const page = usePage();
const flashSuccess = computed(() => page.props.flash?.success ?? null);

// ──────────────────────────────────────────────
//  Partage du lien boutique
// ──────────────────────────────────────────────
const shareCopied = ref(false);

async function copyShopLink() {
    const url = window.location.href.split('?')[0];
    try {
        await navigator.clipboard.writeText(url);
    } catch {
        const ta = document.createElement('textarea');
        ta.value = url;
        document.body.appendChild(ta);
        ta.select();
        document.execCommand('copy');
        document.body.removeChild(ta);
    }
    shareCopied.value = true;
    setTimeout(() => { shareCopied.value = false; }, 2500);
}

async function nativeShare() {
    const url = window.location.href.split('?')[0];
    const shareData = {
        title: `Boutique ${props.vendor.shop_name || props.vendor.business_name || props.vendor.name}`,
        text: `Decouvrez la boutique de ${props.vendor.shop_name || props.vendor.business_name || props.vendor.name} sur MANTOTA`,
        url,
    };
    if (navigator.share) {
        try { await navigator.share(shareData); } catch {}
    } else {
        copyShopLink();
    }
}

const canNativeShare = computed(() => typeof navigator !== 'undefined' && !!navigator.share);

// ──────────────────────────────────────────────
//  Produit cible via ?product=ID (SmartLink)
// ──────────────────────────────────────────────
const highlightedProductId = ref(null);

const sortedProducts = computed(() => {
    if (!highlightedProductId.value) return props.products;
    return [...props.products].sort((a, b) => {
        if (a.id === highlightedProductId.value) return -1;
        if (b.id === highlightedProductId.value) return 1;
        return 0;
    });
});

onMounted(() => {
    const params = new URLSearchParams(window.location.search);
    const pid = params.get('product');
    if (pid) {
        highlightedProductId.value = parseInt(pid, 10);
        nextTick(() => {
            const el = document.getElementById('product-' + pid);
            if (el) {
                el.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        });
    }
});

function formatCurrency(amount) {
    const v = parseFloat(amount);
    if (!v || v < 0) return '0 FCFA';
    return new Intl.NumberFormat('fr-FR', { style: 'decimal', minimumFractionDigits: 0, maximumFractionDigits: 0 }).format(v) + ' FCFA';
}

// ──────────────────────────────────────────────
//  Image helpers
// ──────────────────────────────────────────────
function getImages(product) {
    if (product.images?.length) return product.images;
    if (product.image_path) return [{ path: product.image_path }];
    return [];
}

const carouselIndexes = ref({});

function carouselIndex(productId) {
    return carouselIndexes.value[productId] || 0;
}
function carouselPrev(product) {
    const imgs = getImages(product);
    if (!imgs.length) return;
    const cur = carouselIndex(product.id);
    carouselIndexes.value[product.id] = cur > 0 ? cur - 1 : imgs.length - 1;
}
function carouselNext(product) {
    const imgs = getImages(product);
    if (!imgs.length) return;
    const cur = carouselIndex(product.id);
    carouselIndexes.value[product.id] = cur < imgs.length - 1 ? cur + 1 : 0;
}

// ──────────────────────────────────────────────
//  Display format → CSS classes
// ──────────────────────────────────────────────
const displayFormat = computed(() => props.vendor.shop_display_format || 'square');

const imageContainerClass = computed(() => {
    switch (displayFormat.value) {
        case 'landscape': return 'aspect-video';
        case 'portrait':  return 'aspect-[3/4]';
        default:          return 'aspect-square';
    }
});

// Filtre produits
const activeFilter = ref('all');
const filteredProducts = computed(() => {
    if (activeFilter.value === 'all') return sortedProducts.value;
    return sortedProducts.value.filter(p => p.type === activeFilter.value);
});
</script>

<template>
    <Head :title="`Boutique ${vendor.business_name || vendor.name}`" />

    <div class="min-h-screen bg-surface-1 text-grey-1">

        <!-- ═══════════════════════════════════════════
             Hero — Mantota branding
        ═══════════════════════════════════════════ -->
        <header class="relative overflow-hidden bg-white border-b border-surface-3">
            <!-- Accent teal decoratif -->
            <div class="absolute inset-0 opacity-[0.07]">
                <div class="absolute left-1/4 top-0 h-[400px] w-[400px] rounded-full bg-mantota-teal blur-[100px]" />
            </div>

            <div class="relative mx-auto max-w-6xl px-4 py-12 sm:px-6 sm:py-16">
                <!-- Retour accueil -->
                <a :href="route('home')" class="mb-6 inline-flex items-center gap-2 text-sm font-semibold text-grey-2 transition hover:text-mantota-teal-dark">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18" /></svg>
                    MANTOTA
                </a>

                <div class="flex flex-col items-center text-center sm:flex-row sm:items-start sm:text-left sm:gap-8">
                    <!-- Logo vendeur -->
                    <div class="mx-auto flex h-20 w-20 shrink-0 items-center justify-center rounded-mantota-card bg-mantota-teal-pale ring-1 ring-mantota-teal/20 mb-4 overflow-hidden sm:mb-0">
                        <img v-if="vendor.shop_logo_path" :src="`/storage/${vendor.shop_logo_path}`" :alt="vendor.shop_name || vendor.business_name || vendor.name" class="h-full w-full object-cover" />
                        <span v-else class="text-3xl font-bold text-mantota-teal-dark">
                            {{ (vendor.shop_name || vendor.business_name || vendor.name)?.charAt(0).toUpperCase() }}
                        </span>
                    </div>

                    <div class="flex-1">
                        <h1 class="text-2xl font-bold tracking-tight text-grey-1 sm:text-3xl">
                            {{ vendor.shop_name || vendor.business_name || vendor.name }}
                        </h1>
                        <p class="mt-2 text-base text-grey-2">
                            Decouvrez nos produits et services
                        </p>

                        <!-- Stats rapides -->
                        <div class="mt-6 flex flex-wrap items-center gap-4 sm:gap-6">
                            <div class="flex items-center gap-2">
                                <span class="inline-flex h-8 w-8 items-center justify-center rounded-full bg-mantota-teal-pale text-mantota-teal-dark">
                                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M15.75 10.5V6a3.75 3.75 0 10-7.5 0v4.5m11.356-1.993l1.263 12c.07.665-.45 1.243-1.119 1.243H4.25a1.125 1.125 0 01-1.12-1.243l1.264-12A1.125 1.125 0 015.513 7.5h12.974c.576 0 1.059.435 1.119 1.007z" /></svg>
                                </span>
                                <span class="text-sm font-semibold text-grey-1">{{ products.length }}</span>
                                <span class="text-xs text-grey-2">Produit{{ products.length > 1 ? 's' : '' }}</span>
                            </div>
                            <div class="h-6 w-px bg-surface-3" />
                            <div class="flex items-center gap-2">
                                <span class="inline-flex h-8 w-8 items-center justify-center rounded-full bg-surface-2 text-grey-2">
                                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M21 7.5l-9-5.25L3 7.5m18 0l-9 5.25m9-5.25v9l-9 5.25M3 7.5l9 5.25M3 7.5v9l9 5.25m0-9v9" /></svg>
                                </span>
                                <span class="text-sm font-semibold text-grey-1">{{ products.filter(p => p.type === 'physical').length }}</span>
                                <span class="text-xs text-grey-2">Physique{{ products.filter(p => p.type === 'physical').length > 1 ? 's' : '' }}</span>
                            </div>
                            <div class="h-6 w-px bg-surface-3" />
                            <div class="flex items-center gap-2">
                                <span class="inline-flex h-8 w-8 items-center justify-center rounded-full bg-mantota-teal-pale text-mantota-teal-dark">
                                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M12 16.5V9.75m0 0l3 3m-3-3l-3 3M6.75 19.5a4.5 4.5 0 01-1.41-8.775 5.25 5.25 0 0110.233-2.33 3 3 0 013.758 3.848A3.752 3.752 0 0118 19.5H6.75z" /></svg>
                                </span>
                                <span class="text-sm font-semibold text-grey-1">{{ products.filter(p => p.type === 'digital').length }}</span>
                                <span class="text-xs text-grey-2">Digital{{ products.filter(p => p.type === 'digital').length > 1 ? 'aux' : '' }}</span>
                            </div>
                        </div>
                    </div>

                    <!-- Bouton partage -->
                    <div class="mt-4 sm:mt-0 shrink-0">
                        <button
                            @click="canNativeShare ? nativeShare() : copyShopLink()"
                            class="inline-flex items-center gap-2 rounded-mantota border-2 border-mantota-teal bg-white px-4 py-2.5 text-sm font-bold text-mantota-teal-dark transition hover:bg-mantota-teal-pale active:scale-[0.98]"
                        >
                            <svg v-if="!shareCopied" xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M7.217 10.907a2.25 2.25 0 100 2.186m0-2.186c.18.324.283.696.283 1.093s-.103.77-.283 1.093m0-2.186l9.566-5.314m-9.566 7.5l9.566 5.314m0 0a2.25 2.25 0 103.935 2.186 2.25 2.25 0 00-3.935-2.186zm0-12.814a2.25 2.25 0 103.933-2.185 2.25 2.25 0 00-3.933 2.185z" /></svg>
                            <svg v-else xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-mantota-teal" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M16.704 4.153a.75.75 0 01.143 1.052l-8 10.5a.75.75 0 01-1.127.075l-4.5-4.5a.75.75 0 011.06-1.06l3.894 3.893 7.48-9.817a.75.75 0 011.05-.143z" clip-rule="evenodd" /></svg>
                            {{ shareCopied ? 'Lien copie !' : 'Partager' }}
                        </button>
                    </div>
                </div>
            </div>
        </header>

        <!-- ═══════════════════════════════════════════
             Filtres + Produits
        ═══════════════════════════════════════════ -->
        <main class="mx-auto max-w-6xl px-4 py-10 sm:px-6">

            <!-- Flash succes -->
            <div
                v-if="flashSuccess"
                class="mb-6 flex items-center gap-3 rounded-mantota border border-mantota-teal/30 bg-mantota-teal-pale px-5 py-4 text-sm text-mantota-teal-dark"
            >
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 shrink-0 text-mantota-teal" viewBox="0 0 20 20" fill="currentColor">
                    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
                </svg>
                <span>{{ flashSuccess }}</span>
            </div>

            <!-- Filtres type produit -->
            <div v-if="products.length" class="mb-6 flex gap-2">
                <button
                    @click="activeFilter = 'all'"
                    class="rounded-mantota px-4 py-2 text-sm font-semibold transition"
                    :class="activeFilter === 'all' ? 'bg-mantota-teal text-white' : 'bg-white text-grey-2 hover:bg-surface-2'"
                >
                    Tous ({{ products.length }})
                </button>
                <button
                    v-if="products.filter(p => p.type === 'physical').length"
                    @click="activeFilter = 'physical'"
                    class="rounded-mantota px-4 py-2 text-sm font-semibold transition"
                    :class="activeFilter === 'physical' ? 'bg-mantota-teal text-white' : 'bg-white text-grey-2 hover:bg-surface-2'"
                >
                    Physiques ({{ products.filter(p => p.type === 'physical').length }})
                </button>
                <button
                    v-if="products.filter(p => p.type === 'digital').length"
                    @click="activeFilter = 'digital'"
                    class="rounded-mantota px-4 py-2 text-sm font-semibold transition"
                    :class="activeFilter === 'digital' ? 'bg-mantota-teal text-white' : 'bg-white text-grey-2 hover:bg-surface-2'"
                >
                    Digitaux ({{ products.filter(p => p.type === 'digital').length }})
                </button>
            </div>

            <div v-if="filteredProducts.length" class="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
                <div
                    v-for="product in filteredProducts"
                    :key="product.id"
                    :id="'product-' + product.id"
                    class="group flex flex-col rounded-mantota-card bg-white shadow-mantota transition hover:shadow-mantota-md hover:-translate-y-1"
                    :class="highlightedProductId === product.id ? 'ring-2 ring-mantota-teal' : ''"
                >
                    <!-- ── Image section ── -->
                    <div class="relative overflow-hidden rounded-t-mantota-card bg-surface-2" :class="imageContainerClass">
                        <template v-if="getImages(product).length">
                            <img
                                :src="`/storage/${getImages(product)[carouselIndex(product.id)].path}`"
                                :alt="product.name"
                                class="h-full w-full object-cover transition group-hover:scale-105"
                            />
                            <template v-if="getImages(product).length > 1">
                                <button
                                    @click.prevent="carouselPrev(product)"
                                    class="absolute left-2 top-1/2 -translate-y-1/2 flex h-7 w-7 items-center justify-center rounded-full bg-white/80 text-grey-1 shadow opacity-0 transition group-hover:opacity-100 hover:bg-white"
                                >
                                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke-width="2.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M15.75 19.5L8.25 12l7.5-7.5" /></svg>
                                </button>
                                <button
                                    @click.prevent="carouselNext(product)"
                                    class="absolute right-2 top-1/2 -translate-y-1/2 flex h-7 w-7 items-center justify-center rounded-full bg-white/80 text-grey-1 shadow opacity-0 transition group-hover:opacity-100 hover:bg-white"
                                >
                                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke-width="2.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" /></svg>
                                </button>
                                <div class="absolute bottom-2 left-1/2 -translate-x-1/2 flex gap-1.5">
                                    <span
                                        v-for="(_, idx) in getImages(product)"
                                        :key="idx"
                                        class="h-1.5 w-1.5 rounded-full transition"
                                        :class="idx === carouselIndex(product.id) ? 'bg-white' : 'bg-white/50'"
                                    />
                                </div>
                            </template>
                        </template>
                        <div v-else class="flex h-full w-full items-center justify-center">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-14 w-14 text-surface-4" fill="none" viewBox="0 0 24 24" stroke-width="0.75" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 15.75l5.159-5.159a2.25 2.25 0 013.182 0l5.159 5.159m-1.5-1.5l1.409-1.409a2.25 2.25 0 013.182 0l2.909 2.909M2.25 18V6a2.25 2.25 0 012.25-2.25h15A2.25 2.25 0 0121.75 6v12A2.25 2.25 0 0119.5 20.25H4.5A2.25 2.25 0 012.25 18z" />
                            </svg>
                        </div>

                        <!-- Badge type -->
                        <div class="absolute left-3 top-3 z-10">
                            <span
                                class="inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-semibold backdrop-blur-sm"
                                :class="product.type === 'physical'
                                    ? 'bg-grey-1/80 text-white'
                                    : 'bg-mantota-teal/90 text-white'"
                            >
                                <svg v-if="product.type === 'physical'" xmlns="http://www.w3.org/2000/svg" class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
                                    <path stroke-linecap="round" stroke-linejoin="round" d="M21 7.5l-9-5.25L3 7.5m18 0l-9 5.25m9-5.25v9l-9 5.25M3 7.5l9 5.25M3 7.5v9l9 5.25m0-9v9" />
                                </svg>
                                <svg v-else xmlns="http://www.w3.org/2000/svg" class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
                                    <path stroke-linecap="round" stroke-linejoin="round" d="M12 16.5V9.75m0 0l3 3m-3-3l-3 3M6.75 19.5a4.5 4.5 0 01-1.41-8.775 5.25 5.25 0 0110.233-2.33 3 3 0 013.758 3.848A3.752 3.752 0 0118 19.5H6.75z" />
                                </svg>
                                {{ product.type === 'physical' ? 'Physique' : 'Digital' }}
                            </span>
                        </div>

                        <!-- Image count badge -->
                        <div v-if="getImages(product).length > 1" class="absolute right-3 top-3 z-10">
                            <span class="inline-flex items-center gap-1 rounded-full bg-black/50 px-2 py-0.5 text-xs font-medium text-white backdrop-blur-sm">
                                <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
                                    <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 15.75l5.159-5.159a2.25 2.25 0 013.182 0l5.159 5.159m-1.5-1.5l1.409-1.409a2.25 2.25 0 013.182 0l2.909 2.909M2.25 18V6a2.25 2.25 0 012.25-2.25h15A2.25 2.25 0 0121.75 6v12A2.25 2.25 0 0119.5 20.25H4.5A2.25 2.25 0 012.25 18z" />
                                </svg>
                                {{ getImages(product).length }}
                            </span>
                        </div>
                    </div>

                    <!-- Contenu -->
                    <div class="flex flex-1 flex-col p-5">
                        <Link :href="route('shop.product', { vendorSlug: vendor.slug, product: product.id })" class="block">
                            <h3 class="text-base font-bold text-grey-1 line-clamp-2 hover:text-mantota-teal-dark transition">{{ product.name }}</h3>
                        </Link>
                        <p class="mt-1.5 text-sm text-grey-2 line-clamp-3">{{ product.description }}</p>

                        <div class="mt-auto pt-5">
                            <div class="flex items-center justify-between mb-4">
                                <span class="text-lg font-bold text-mantota-teal-dark">{{ formatCurrency(product.price) }}</span>
                                <span v-if="product.type === 'physical' && product.stock !== null" class="text-xs font-semibold" :class="product.stock > 0 ? 'text-mantota-teal' : 'text-mantota-coral'">
                                    {{ product.stock > 0 ? product.stock + ' en stock' : 'Rupture' }}
                                </span>
                            </div>
                            <div class="flex gap-2">
                                <Link
                                    :href="route('shop.product', { vendorSlug: vendor.slug, product: product.id })"
                                    class="flex flex-1 items-center justify-center gap-2 rounded-mantota border-2 border-surface-4 bg-white px-4 py-3 text-sm font-bold text-grey-1 transition hover:border-mantota-teal hover:text-mantota-teal-dark active:scale-[0.98]"
                                >
                                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z" /><path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /></svg>
                                    Voir
                                </Link>
                                <Link
                                    :href="route('shop.checkout.show', product.id)"
                                    class="flex flex-1 items-center justify-center gap-2 rounded-mantota bg-mantota-teal px-4 py-3 text-sm font-bold text-white transition hover:bg-mantota-teal-dark active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed"
                                    :class="{ 'pointer-events-none opacity-50': product.type === 'physical' && product.stock === 0 }"
                                >
                                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
                                        <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 3h1.386c.51 0 .955.343 1.087.835l.383 1.437M7.5 14.25a3 3 0 00-3 3h15.75m-12.75-3h11.218c1.121-2.3 2.1-4.684 2.924-7.138a60.114 60.114 0 00-16.536-1.84M7.5 14.25L5.106 5.272M6 20.25a.75.75 0 11-1.5 0 .75.75 0 011.5 0zm12.75 0a.75.75 0 11-1.5 0 .75.75 0 011.5 0z" />
                                    </svg>
                                    {{ product.type === 'physical' && product.stock === 0 ? 'Indispo.' : 'Commander' }}
                                </Link>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Etat vide -->
            <div v-else class="py-24 text-center">
                <div class="mx-auto flex h-20 w-20 items-center justify-center rounded-mantota-card bg-surface-2">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-10 w-10 text-surface-4" fill="none" viewBox="0 0 24 24" stroke-width="1" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 10.5V6a3.75 3.75 0 10-7.5 0v4.5m11.356-1.993l1.263 12c.07.665-.45 1.243-1.119 1.243H4.25a1.125 1.125 0 01-1.12-1.243l1.264-12A1.125 1.125 0 015.513 7.5h12.974c.576 0 1.059.435 1.119 1.007zM8.625 10.5a.375.375 0 11-.75 0 .375.375 0 01.75 0zm7.5 0a.375.375 0 11-.75 0 .375.375 0 01.75 0z" />
                    </svg>
                </div>
                <h2 class="mt-6 text-xl font-bold text-grey-1">Boutique en preparation</h2>
                <p class="mt-2 text-sm text-grey-2">Ce vendeur n'a pas encore ajoute de produits.</p>
            </div>
        </main>

        <!-- ═══════════════════════════════════════════
             Footer — Mantota
        ═══════════════════════════════════════════ -->
        <footer class="border-t border-surface-3 bg-white py-8">
            <div class="mx-auto max-w-6xl px-4 sm:px-6 text-center">
                <p class="text-xs text-grey-2">
                    Propulse par
                    <span class="font-bold text-mantota-teal-dark">MANTOTA</span>
                    — Assistante commerciale IA
                </p>
            </div>
        </footer>
    </div>
</template>
