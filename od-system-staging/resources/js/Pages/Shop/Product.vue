<script setup>
import { Head, Link, router } from '@inertiajs/vue3';
import { ref, computed } from 'vue';

const props = defineProps({
    vendor:  { type: Object, required: true },
    product: { type: Object, required: true },
    related: { type: Array, default: () => [] },
});

// ── Share ──
const shareCopied = ref(false);

async function copyProductLink() {
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
        title: props.product.name,
        text: `${props.product.name} — ${formatCurrency(props.product.price)}`,
        url,
    };
    if (navigator.share) {
        try { await navigator.share(shareData); } catch {}
    } else {
        copyProductLink();
    }
}

const canNativeShare = computed(() => typeof navigator !== 'undefined' && !!navigator.share);

// ── Currency ──
function formatCurrency(amount) {
    const v = parseFloat(amount);
    if (!v || v < 0) return '0 FCFA';
    return new Intl.NumberFormat('fr-FR', { style: 'decimal', minimumFractionDigits: 0, maximumFractionDigits: 0 }).format(v) + ' FCFA';
}

// ── Images ──
function getImages() {
    if (props.product.images?.length) return props.product.images;
    if (props.product.image_path) return [{ path: props.product.image_path }];
    return [];
}

const currentImageIndex = ref(0);

const images = computed(() => getImages());

function imagePrev() {
    if (!images.value.length) return;
    currentImageIndex.value = currentImageIndex.value > 0 ? currentImageIndex.value - 1 : images.value.length - 1;
}
function imageNext() {
    if (!images.value.length) return;
    currentImageIndex.value = currentImageIndex.value < images.value.length - 1 ? currentImageIndex.value + 1 : 0;
}

const isOutOfStock = computed(() => props.product.type === 'physical' && props.product.stock === 0);
</script>

<template>
    <Head :title="`${product.name} — ${vendor.shop_name || vendor.business_name || vendor.name}`" />

    <div class="min-h-screen bg-surface-1 text-grey-1">
        <!-- ═══ Header — MANTOTA branding ═══ -->
        <header class="relative overflow-hidden bg-white border-b border-surface-3">
            <div class="absolute inset-0 opacity-[0.07]">
                <div class="absolute left-1/4 top-0 h-[400px] w-[400px] rounded-full bg-mantota-teal blur-[100px]" />
            </div>
            <div class="relative mx-auto max-w-6xl px-4 py-6 sm:px-6">
                <!-- Breadcrumb -->
                <nav class="mb-4 flex items-center gap-2 text-sm">
                    <a :href="route('home')" class="font-semibold text-grey-2 transition hover:text-mantota-teal-dark">MANTOTA</a>
                    <span class="text-surface-4">/</span>
                    <Link :href="route('shop.show', vendor.slug)" class="font-semibold text-grey-2 transition hover:text-mantota-teal-dark">
                        {{ vendor.shop_name || vendor.business_name || vendor.name }}
                    </Link>
                    <span class="text-surface-4">/</span>
                    <span class="font-semibold text-grey-1">{{ product.name }}</span>
                </nav>

                <!-- Vendor bar -->
                <div class="flex items-center justify-between">
                    <Link :href="route('shop.show', vendor.slug)" class="flex items-center gap-3 group">
                        <div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-mantota bg-mantota-teal-pale ring-1 ring-mantota-teal/20 overflow-hidden">
                            <img v-if="vendor.shop_logo_path" :src="`/storage/${vendor.shop_logo_path}`" :alt="vendor.shop_name || vendor.name" class="h-full w-full object-cover" />
                            <span v-else class="text-sm font-bold text-mantota-teal-dark">
                                {{ (vendor.shop_name || vendor.business_name || vendor.name)?.charAt(0).toUpperCase() }}
                            </span>
                        </div>
                        <div>
                            <div class="text-sm font-bold text-grey-1 group-hover:text-mantota-teal-dark transition">{{ vendor.shop_name || vendor.business_name || vendor.name }}</div>
                            <div class="text-xs text-grey-2">Voir la boutique</div>
                        </div>
                    </Link>

                    <!-- Share buttons -->
                    <div class="flex items-center gap-2">
                        <button
                            @click="canNativeShare ? nativeShare() : copyProductLink()"
                            class="inline-flex items-center gap-2 rounded-mantota border-2 border-mantota-teal bg-white px-4 py-2 text-sm font-bold text-mantota-teal-dark transition hover:bg-mantota-teal-pale active:scale-[0.98]"
                        >
                            <svg v-if="!shareCopied" xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M7.217 10.907a2.25 2.25 0 100 2.186m0-2.186c.18.324.283.696.283 1.093s-.103.77-.283 1.093m0-2.186l9.566-5.314m-9.566 7.5l9.566 5.314m0 0a2.25 2.25 0 103.935 2.186 2.25 2.25 0 00-3.935-2.186zm0-12.814a2.25 2.25 0 103.933-2.185 2.25 2.25 0 00-3.933 2.185z" /></svg>
                            <svg v-else xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-mantota-teal" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M16.704 4.153a.75.75 0 01.143 1.052l-8 10.5a.75.75 0 01-1.127.075l-4.5-4.5a.75.75 0 011.06-1.06l3.894 3.893 7.48-9.817a.75.75 0 011.05-.143z" clip-rule="evenodd" /></svg>
                            {{ shareCopied ? 'Lien copié !' : 'Partager' }}
                        </button>
                    </div>
                </div>
            </div>
        </header>

        <!-- ═══ Product detail ═══ -->
        <main class="mx-auto max-w-6xl px-4 py-10 sm:px-6">
            <div class="grid gap-8 lg:grid-cols-2">
                <!-- ── Images ── -->
                <div>
                    <div class="relative overflow-hidden rounded-mantota-card bg-surface-2 aspect-square shadow-mantota">
                        <template v-if="images.length">
                            <img
                                :src="`/storage/${images[currentImageIndex]?.path}`"
                                :alt="product.name"
                                class="h-full w-full object-cover"
                            />
                            <template v-if="images.length > 1">
                                <button @click.prevent="imagePrev" class="absolute left-3 top-1/2 -translate-y-1/2 flex h-9 w-9 items-center justify-center rounded-full bg-white/80 text-grey-1 shadow hover:bg-white transition">
                                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke-width="2.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M15.75 19.5L8.25 12l7.5-7.5" /></svg>
                                </button>
                                <button @click.prevent="imageNext" class="absolute right-3 top-1/2 -translate-y-1/2 flex h-9 w-9 items-center justify-center rounded-full bg-white/80 text-grey-1 shadow hover:bg-white transition">
                                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke-width="2.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" /></svg>
                                </button>
                                <div class="absolute bottom-3 left-1/2 -translate-x-1/2 flex gap-1.5">
                                    <span v-for="(_, idx) in images" :key="idx" class="h-2 w-2 rounded-full transition" :class="idx === currentImageIndex ? 'bg-white' : 'bg-white/50'" />
                                </div>
                            </template>
                        </template>
                        <div v-else class="flex h-full w-full items-center justify-center">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-20 w-20 text-surface-4" fill="none" viewBox="0 0 24 24" stroke-width="0.75" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 15.75l5.159-5.159a2.25 2.25 0 013.182 0l5.159 5.159m-1.5-1.5l1.409-1.409a2.25 2.25 0 013.182 0l2.909 2.909M2.25 18V6a2.25 2.25 0 012.25-2.25h15A2.25 2.25 0 0121.75 6v12A2.25 2.25 0 0119.5 20.25H4.5A2.25 2.25 0 012.25 18z" />
                            </svg>
                        </div>

                        <!-- Badge type -->
                        <div class="absolute left-3 top-3 z-10">
                            <span class="inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-semibold backdrop-blur-sm" :class="product.type === 'physical' ? 'bg-grey-1/80 text-white' : 'bg-mantota-teal/90 text-white'">
                                {{ product.type === 'physical' ? 'Physique' : 'Digital' }}
                            </span>
                        </div>
                    </div>

                    <!-- Thumbnails -->
                    <div v-if="images.length > 1" class="mt-4 flex gap-2">
                        <button
                            v-for="(img, idx) in images"
                            :key="idx"
                            @click="currentImageIndex = idx"
                            class="h-16 w-16 overflow-hidden rounded-mantota border-2 transition"
                            :class="idx === currentImageIndex ? 'border-mantota-teal' : 'border-surface-3 hover:border-surface-4'"
                        >
                            <img :src="`/storage/${img.path}`" :alt="`Image ${idx + 1}`" class="h-full w-full object-cover" />
                        </button>
                    </div>
                </div>

                <!-- ── Info ── -->
                <div class="flex flex-col">
                    <h1 class="text-2xl font-bold tracking-tight text-grey-1 sm:text-3xl">{{ product.name }}</h1>

                    <div class="mt-4 flex items-baseline gap-3">
                        <span class="text-3xl font-bold text-mantota-teal-dark">{{ formatCurrency(product.price) }}</span>
                        <span v-if="product.type === 'physical' && product.stock !== null" class="text-sm font-semibold" :class="product.stock > 0 ? 'text-mantota-teal' : 'text-mantota-coral'">
                            {{ product.stock > 0 ? `${product.stock} en stock` : 'Rupture de stock' }}
                        </span>
                    </div>

                    <!-- Description -->
                    <div class="mt-6 prose prose-sm max-w-none text-grey-2" v-if="product.description">
                        <p class="whitespace-pre-line">{{ product.description }}</p>
                    </div>

                    <!-- Trust badges -->
                    <div class="mt-6 space-y-3 rounded-mantota-card bg-white p-5 shadow-mantota">
                        <div class="flex items-center gap-3 text-sm text-grey-2">
                            <span class="flex h-8 w-8 items-center justify-center rounded-full bg-mantota-teal-pale text-mantota-teal-dark">
                                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                            </span>
                            Paiement sécurisé par séquestre (escrow)
                        </div>
                        <div class="flex items-center gap-3 text-sm text-grey-2">
                            <span class="flex h-8 w-8 items-center justify-center rounded-full bg-mantota-teal-pale text-mantota-teal-dark">
                                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M8.25 18.75a1.5 1.5 0 01-3 0m3 0a1.5 1.5 0 00-3 0m3 0h6m-9 0H3.375a1.125 1.125 0 01-1.125-1.125V14.25m17.25 4.5a1.5 1.5 0 01-3 0m3 0a1.5 1.5 0 00-3 0m3 0h1.125c.621 0 1.129-.504 1.09-1.124a17.902 17.902 0 00-3.213-9.193 2.056 2.056 0 00-1.58-.86H14.25M16.5 18.75h-6m6 0V10.5m-6 8.25V10.5m6 0V7.5a1.5 1.5 0 00-1.5-1.5H9.75a1.5 1.5 0 00-1.5 1.5v3m6 0h-6" /></svg>
                            </span>
                            Livraison rapide ou téléchargement immédiat
                        </div>
                        <div class="flex items-center gap-3 text-sm text-grey-2">
                            <span class="flex h-8 w-8 items-center justify-center rounded-full bg-mantota-teal-pale text-mantota-teal-dark">
                                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                            </span>
                            Remboursement si non-livraison
                        </div>
                    </div>

                    <!-- CTA -->
                    <div class="mt-6">
                        <Link
                            :href="route('shop.checkout.show', product.id)"
                            class="flex w-full items-center justify-center gap-2 rounded-mantota bg-mantota-teal px-6 py-4 text-base font-bold text-white transition hover:bg-mantota-teal-dark active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed"
                            :class="{ 'pointer-events-none opacity-50': isOutOfStock }"
                        >
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 3h1.386c.51 0 .955.343 1.087.835l.383 1.437M7.5 14.25a3 3 0 00-3 3h15.75m-12.75-3h11.218c1.121-2.3 2.1-4.684 2.924-7.138a60.114 60.114 0 00-16.536-1.84M7.5 14.25L5.106 5.272M6 20.25a.75.75 0 11-1.5 0 .75.75 0 011.5 0zm12.75 0a.75.75 0 11-1.5 0 .75.75 0 011.5 0z" />
                            </svg>
                            {{ isOutOfStock ? 'Indisponible' : 'Commander maintenant' }}
                        </Link>
                    </div>
                </div>
            </div>

            <!-- ═══ Related products ═══ -->
            <section v-if="related.length" class="mt-16">
                <h2 class="text-xl font-bold text-grey-1 mb-6">Autres produits de cette boutique</h2>
                <div class="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
                    <Link
                        v-for="rel in related"
                        :key="rel.id"
                        :href="route('shop.product', { vendorSlug: vendor.slug, product: rel.id })"
                        class="group flex flex-col rounded-mantota-card bg-white shadow-mantota transition hover:shadow-mantota-md hover:-translate-y-1"
                    >
                        <div class="relative overflow-hidden rounded-t-mantota-card bg-surface-2 aspect-square">
                            <img
                                v-if="rel.images?.length"
                                :src="`/storage/${rel.images[0].path}`"
                                :alt="rel.name"
                                class="h-full w-full object-cover transition group-hover:scale-105"
                            />
                            <div v-else class="flex h-full w-full items-center justify-center">
                                <svg xmlns="http://www.w3.org/2000/svg" class="h-10 w-10 text-surface-4" fill="none" viewBox="0 0 24 24" stroke-width="0.75" stroke="currentColor">
                                    <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 15.75l5.159-5.159a2.25 2.25 0 013.182 0l5.159 5.159m-1.5-1.5l1.409-1.409a2.25 2.25 0 013.182 0l2.909 2.909M2.25 18V6a2.25 2.25 0 012.25-2.25h15A2.25 2.25 0 0121.75 6v12A2.25 2.25 0 0119.5 20.25H4.5A2.25 2.25 0 012.25 18z" />
                                </svg>
                            </div>
                        </div>
                        <div class="p-4">
                            <h3 class="text-sm font-bold text-grey-1 line-clamp-2">{{ rel.name }}</h3>
                            <span class="mt-2 block text-base font-bold text-mantota-teal-dark">{{ formatCurrency(rel.price) }}</span>
                        </div>
                    </Link>
                </div>
            </section>
        </main>

        <!-- ═══ Footer ═══ -->
        <footer class="border-t border-surface-3 bg-white py-8">
            <div class="mx-auto max-w-6xl px-4 sm:px-6 text-center">
                <p class="text-xs text-grey-2">
                    Propulsé par
                    <span class="font-bold text-mantota-teal-dark">MANTOTA</span>
                    — Assistante commerciale IA
                </p>
            </div>
        </footer>
    </div>
</template>
