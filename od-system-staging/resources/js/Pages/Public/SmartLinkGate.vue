<script setup>
import { Head } from '@inertiajs/vue3';
import { ref, onMounted } from 'vue';

/**
 * Page intermediaire du parcours d'affiliation (GET /go/{hash}).
 *
 * Collecte un identifiant de device stable puis soumet POST /go/{hash}/click,
 * ou Public\SmartLinkController@processClick execute le pipeline anti-fraude
 * avant de rediriger vers la boutique du vendeur.
 *
 * La soumission utilise un formulaire HTML natif (et non le router Inertia) car
 * la reponse du controleur est un redirect()->away() vers un domaine externe,
 * qu'une requete XHR Inertia ne peut pas suivre.
 */
const props = defineProps({
    hash: { type: String, required: true },
    campaign_title: { type: String, default: 'Offre MANTOTA' },
});

/** Delai minimal avant soumission — le back rejette en dessous de 80 ms (MIN_COLLECT_TIME_MS). */
const MIN_DELAY_MS = 400;
const STORAGE_KEY = 'mantota_device_id';

const form = ref(null);
const deviceId = ref('');
const collectTimeMs = ref(0);
const csrfToken = ref('');
const failed = ref(false);

/** Identifiant aleatoire persistant : c'est la semantique attendue pour la dedup device sur 24 h. */
function randomId() {
    if (window.crypto?.randomUUID) {
        return window.crypto.randomUUID().replace(/-/g, '');
    }
    const bytes = new Uint8Array(16);
    if (window.crypto?.getRandomValues) {
        window.crypto.getRandomValues(bytes);
    } else {
        for (let i = 0; i < bytes.length; i++) bytes[i] = Math.floor(Math.random() * 256);
    }
    return Array.from(bytes, (b) => b.toString(16).padStart(2, '0')).join('');
}

/** Signature du navigateur — repli si le stockage local est indisponible (navigation privee, etc.). */
function browserSignature() {
    const parts = [
        navigator.userAgent || '',
        navigator.language || '',
        String(navigator.hardwareConcurrency || 0),
        `${window.screen?.width || 0}x${window.screen?.height || 0}x${window.screen?.colorDepth || 0}`,
        String(new Date().getTimezoneOffset()),
    ];
    let hash = 0;
    const raw = parts.join('|');
    for (let i = 0; i < raw.length; i++) {
        hash = (hash << 5) - hash + raw.charCodeAt(i);
        hash |= 0;
    }
    return 'sig' + Math.abs(hash).toString(16);
}

function resolveDeviceId() {
    try {
        const stored = window.localStorage.getItem(STORAGE_KEY);
        if (stored) return stored;
        const fresh = randomId();
        window.localStorage.setItem(STORAGE_KEY, fresh);
        return fresh;
    } catch (e) {
        return browserSignature();
    }
}

onMounted(() => {
    const startedAt = performance.now();

    csrfToken.value = document.querySelector('meta[name="csrf-token"]')?.content ?? '';
    deviceId.value = resolveDeviceId();

    const elapsed = performance.now() - startedAt;
    const wait = Math.max(MIN_DELAY_MS - elapsed, 0);

    window.setTimeout(() => {
        collectTimeMs.value = Math.round(performance.now() - startedAt);
        if (form.value) {
            form.value.submit();
        } else {
            failed.value = true;
        }
    }, wait);
});
</script>

<template>
    <Head :title="campaign_title" />

    <div class="flex min-h-[100dvh] items-center justify-center bg-grey-1 px-4">
        <div class="w-full max-w-sm text-center">
            <img src="/images/logo-white.png" alt="MANTOTA" class="mx-auto h-9 w-auto object-contain" style="max-width: 150px" />

            <div class="mt-10 flex justify-center">
                <span class="h-10 w-10 animate-spin rounded-full border-2 border-surface-3 border-t-mantota-teal" />
            </div>

            <p class="mt-8 text-base font-semibold text-white">Redirection en cours…</p>
            <p class="mt-2 text-sm text-grey-4">{{ campaign_title }}</p>

            <form
                ref="form"
                :action="route('smartlink.click', { hash })"
                method="POST"
                class="mt-8"
            >
                <input type="hidden" name="_token" :value="csrfToken" />
                <input type="hidden" name="device_id" :value="deviceId" />
                <input type="hidden" name="collect_time_ms" :value="collectTimeMs" />

                <noscript>
                    <p class="mb-3 text-sm text-grey-4">Activez JavaScript ou cliquez ci-dessous pour continuer.</p>
                </noscript>

                <button
                    type="submit"
                    class="rounded-mantota bg-mantota-teal px-6 py-3 text-sm font-bold text-white shadow-mantota-md transition-all hover:bg-mantota-teal-dark"
                    :class="failed ? '' : 'sr-only'"
                >
                    Continuer vers l'offre
                </button>
            </form>
        </div>
    </div>
</template>
