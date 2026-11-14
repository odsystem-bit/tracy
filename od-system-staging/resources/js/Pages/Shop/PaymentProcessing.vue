<script setup>
import { ref, onMounted, onUnmounted } from 'vue';

const props = defineProps({
    order_id:   { type: [Number, String], required: true },
    reference:  { type: String, required: true },
    amount_paid: { type: [Number, String], required: true },
    token:      { type: String, required: true },
    status_url: { type: String, required: true },
    success_url: { type: String, required: true },
    cancel_url:  { type: String, required: true },
});

const status = ref('pending'); // pending | paid | failed | cancelled
const attempts = ref(0);
const maxAttempts = 60; // 3 min max
let pollInterval = null;

async function checkStatus() {
    try {
        const url = props.status_url + (props.status_url.includes('?') ? '&' : '?') + 'token=' + encodeURIComponent(props.token);
        const resp = await fetch(url, { headers: { 'Accept': 'application/json' } });
        if (!resp.ok) return;
        const data = await resp.json();
        status.value = data.payment_status ?? 'pending';

        if (status.value === 'paid') {
            clearInterval(pollInterval);
            window.location.href = props.success_url;
        } else if (status.value === 'failed') {
            clearInterval(pollInterval);
        }
    } catch (e) {
        // ignore network errors, keep polling
    }

    attempts.value++;
    if (attempts.value >= maxAttempts) {
        clearInterval(pollInterval);
        status.value = 'timeout';
    }
}

onMounted(() => {
    // First check immediately
    checkStatus();
    // Then poll every 3 seconds
    pollInterval = setInterval(checkStatus, 3000);
});

onUnmounted(() => {
    if (pollInterval) clearInterval(pollInterval);
});

const formattedAmount = new Intl.NumberFormat('fr-FR').format(props.amount_paid);
</script>

<template>
    <div class="min-h-screen bg-surface-1 flex items-center justify-center p-4">
        <div class="w-full max-w-md bg-white rounded-mantota-card shadow-mantota-lg overflow-hidden">

            <!-- Header -->
            <div class="bg-mantota-teal p-6 text-center">
                <div class="mx-auto mb-3 flex h-16 w-16 items-center justify-center rounded-full bg-white/20">
                    <!-- Spinner (pending/timeout) -->
                    <svg v-if="status === 'pending' || status === 'timeout'" class="h-8 w-8 text-white animate-spin" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                    </svg>
                    <!-- Success check -->
                    <svg v-else-if="status === 'paid'" class="h-8 w-8 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
                    </svg>
                    <!-- Failed X -->
                    <svg v-else class="h-8 w-8 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                </div>
                <h1 class="text-xl font-bold text-white">
                    <span v-if="status === 'pending'">Vérification du paiement…</span>
                    <span v-else-if="status === 'paid'">Paiement confirmé !</span>
                    <span v-else-if="status === 'failed'">Paiement échoué</span>
                    <span v-else-if="status === 'timeout'">Délai dépassé</span>
                    <span v-else>Traitement en cours…</span>
                </h1>
                <p class="text-white/80 text-sm mt-1">Commande {{ reference }}</p>
            </div>

            <!-- Body -->
            <div class="p-6 space-y-5">

                <!-- Amount -->
                <div class="rounded-mantota bg-surface-1 border border-surface-3 p-4 flex justify-between items-center">
                    <span class="text-sm text-grey-2">Montant</span>
                    <span class="font-bold text-grey-1">{{ formattedAmount }} FCFA</span>
                </div>

                <!-- Status message -->
                <div v-if="status === 'pending'" class="text-center text-sm text-grey-3">
                    <p>Nous attendons la confirmation de votre paiement.</p>
                    <p class="mt-1 text-xs text-grey-4">Cette page se met à jour automatiquement. Ne la fermez pas.</p>
                </div>

                <div v-else-if="status === 'paid'" class="rounded-mantota bg-mantota-teal-pale border border-mantota-teal/20 p-4 text-sm text-mantota-teal-dark text-center">
                    Paiement confirmé. Redirection en cours…
                </div>

                <div v-else-if="status === 'failed'" class="rounded-mantota bg-red-50 border border-red-200 p-4 text-sm text-red-700 text-center">
                    Le paiement n'a pas abouti. Veuillez réessayer.
                </div>

                <div v-else-if="status === 'timeout'" class="rounded-mantota bg-amber-50 border border-amber-200 p-4 text-sm text-amber-700 text-center">
                    La confirmation prend plus de temps que prévu. Vérifiez votre commande dans quelques minutes.
                </div>

                <!-- Action buttons -->
                <div class="space-y-3">
                    <a
                        v-if="status === 'failed' || status === 'timeout'"
                        :href="cancel_url"
                        class="flex w-full items-center justify-center gap-2 rounded-mantota border border-mantota-teal px-4 py-3 text-sm font-semibold text-mantota-teal-dark transition hover:bg-mantota-teal-pale"
                    >
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M9 15L3 9m0 0l6-6M3 9h12a6 6 0 010 12h-3" />
                        </svg>
                        Retourner au produit
                    </a>

                    <a
                        v-if="status === 'pending'"
                        :href="cancel_url"
                        class="flex w-full items-center justify-center gap-2 rounded-mantota border border-surface-3 px-4 py-2.5 text-sm text-grey-2 transition hover:bg-surface-1"
                    >
                        Annuler et retourner
                    </a>
                </div>
            </div>
        </div>
    </div>
</template>
