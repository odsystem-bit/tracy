<script setup>
import { ref, computed } from 'vue';
import { router, usePage } from '@inertiajs/vue3';
import Layout from '../Layout.vue';

defineOptions({ layout: Layout });

const props = defineProps({
    gateways: { type: Array, default: () => [] },
    webhookUrl: { type: String, default: '' },
});

const page = usePage();
const flash = computed(() => page.props.flash ?? {});

const AVAILABLE_COUNTRIES = [
    { code: 'BJ', label: 'Benin' },
    { code: 'CI', label: "Cote d'Ivoire" },
    { code: 'SN', label: 'Senegal' },
    { code: 'TG', label: 'Togo' },
    { code: 'BF', label: 'Burkina Faso' },
    { code: 'ML', label: 'Mali' },
];

const editing = ref(null);
const form = ref({});
const copied = ref(false);

function startEdit(gw) {
    editing.value = gw.id;
    form.value = {
        is_active: gw.is_active,
        environment: gw.environment ?? 'sandbox',
        public_key: '',
        secret_key: '',
        webhook_secret: '',
        countries: [...(gw.countries ?? [])],
        payin_fee: gw.payin_fee ?? 0,
        payout_fee: gw.payout_fee ?? 0,
        priority: gw.priority ?? 1,
        supports_payout: gw.supports_payout,
        supports_refund: gw.supports_refund,
    };
}

function cancelEdit() {
    editing.value = null;
    form.value = {};
}

function save(gwId) {
    router.put(route('admin.gateways.update', gwId), form.value, {
        preserveScroll: true,
        onSuccess: () => { editing.value = null; },
    });
}

function copyWebhookUrl() {
    navigator.clipboard.writeText(props.webhookUrl).then(() => {
        copied.value = true;
        setTimeout(() => { copied.value = false; }, 2000);
    }).catch(() => {});
}

function keyState(isSet) {
    return isSet ? 'Definie' : 'Non definie';
}
</script>

<template>
    <div class="space-y-6">
        <!-- Header -->
        <div>
            <h1 class="text-2xl font-bold text-slate-900">Passerelle Moneroo</h1>
            <p class="mt-1 text-sm text-slate-500">
                Moneroo gere les paiements, les retraits (payouts) et les remboursements.
                Configurez les cles API, le webhook, les frais et les pays couverts.
            </p>
        </div>

        <!-- Flash -->
        <div v-if="flash.success" class="rounded-xl border border-teal-200 bg-teal-50 px-4 py-3 text-sm font-medium text-teal-800">
            {{ flash.success }}
        </div>
        <div v-if="flash.error" class="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-medium text-red-800">
            {{ flash.error }}
        </div>

        <!-- Webhook URL (toujours visible) -->
        <div class="rounded-xl border border-slate-200 bg-slate-50 p-4">
            <label class="block text-xs font-semibold uppercase tracking-wide text-slate-500">
                URL Webhook a coller dans le dashboard Moneroo
            </label>
            <div class="mt-2 flex items-center gap-2">
                <code class="flex-1 truncate rounded border border-slate-200 bg-white px-3 py-2 text-xs text-slate-700">{{ webhookUrl }}</code>
                <button
                    type="button"
                    @click="copyWebhookUrl"
                    class="rounded-lg bg-slate-200 px-3 py-2 text-xs font-semibold text-slate-700 transition hover:bg-slate-300"
                >
                    {{ copied ? 'Copie !' : 'Copier' }}
                </button>
            </div>
            <p class="mt-2 text-xs text-slate-500">
                Moneroo signe chaque webhook via HMAC-SHA256 (header <code>X-Moneroo-Signature</code>).
                Le « Secret Webhook » ci-dessous doit correspondre exactement a celui du dashboard Moneroo.
            </p>
        </div>

        <!-- Gateway cards -->
        <div class="grid gap-6 md:grid-cols-2">
            <div
                v-for="gw in gateways"
                :key="gw.id"
                class="rounded-xl border bg-white p-6"
                :class="gw.is_active ? 'border-teal-200' : 'border-slate-200'"
            >
                <!-- Card header -->
                <div class="flex items-center justify-between">
                    <div class="flex items-center gap-3">
                        <div class="flex h-10 w-10 items-center justify-center rounded-lg" :class="gw.is_active ? 'bg-teal-50' : 'bg-slate-100'">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" :class="gw.is_active ? 'text-teal-600' : 'text-slate-400'" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 8.25h19.5M2.25 9h19.5m-16.5 5.25h6m-6 2.25h3m-3.75 3h15a2.25 2.25 0 002.25-2.25V6.75A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25v10.5A2.25 2.25 0 004.5 19.5z" />
                            </svg>
                        </div>
                        <div>
                            <h3 class="text-sm font-bold text-slate-900">{{ gw.name }}</h3>
                            <p class="text-xs text-slate-500">{{ gw.slug }}</p>
                        </div>
                    </div>
                    <span class="inline-flex rounded-full px-2.5 py-0.5 text-xs font-semibold" :class="gw.is_active ? 'bg-teal-50 text-teal-700' : 'bg-slate-100 text-slate-500'">
                        {{ gw.is_active ? 'Actif' : 'Inactif' }}
                    </span>
                </div>

                <!-- View mode -->
                <div v-if="editing !== gw.id" class="mt-5 space-y-2">
                    <div class="flex items-center justify-between text-xs">
                        <span class="text-slate-500">Environnement</span>
                        <span class="font-medium text-slate-700">{{ gw.environment === 'live' ? 'Production (Live)' : 'Sandbox' }}</span>
                    </div>
                    <div class="flex items-center justify-between text-xs">
                        <span class="text-slate-500">Cle publique</span>
                        <span class="font-medium" :class="gw.has_public_key ? 'text-teal-700' : 'text-slate-400'">{{ keyState(gw.has_public_key) }}</span>
                    </div>
                    <div class="flex items-center justify-between text-xs">
                        <span class="text-slate-500">Cle secrete</span>
                        <span class="font-medium" :class="gw.has_secret_key ? 'text-teal-700' : 'text-slate-400'">{{ keyState(gw.has_secret_key) }}</span>
                    </div>
                    <div class="flex items-center justify-between text-xs">
                        <span class="text-slate-500">Secret webhook</span>
                        <span class="font-medium" :class="gw.has_webhook_secret ? 'text-teal-700' : 'text-slate-400'">{{ keyState(gw.has_webhook_secret) }}</span>
                    </div>
                    <div class="flex items-center justify-between text-xs">
                        <span class="text-slate-500">Frais paiement / retrait</span>
                        <span class="font-medium text-slate-700">{{ gw.payin_fee }} % / {{ gw.payout_fee }} %</span>
                    </div>
                    <div class="flex items-center justify-between text-xs">
                        <span class="text-slate-500">Retraits / Remboursements</span>
                        <span class="font-medium text-slate-700">
                            {{ gw.supports_payout ? 'Oui' : 'Non' }} / {{ gw.supports_refund ? 'Oui' : 'Non' }}
                        </span>
                    </div>
                    <div class="flex items-start justify-between gap-3 text-xs">
                        <span class="shrink-0 text-slate-500">Pays</span>
                        <span class="text-right font-medium text-slate-700">{{ (gw.countries ?? []).join(', ') || '--' }}</span>
                    </div>
                    <button @click="startEdit(gw)" class="mt-4 w-full rounded-lg border border-slate-200 px-4 py-2 text-xs font-semibold text-slate-700 transition hover:bg-slate-50">
                        Configurer
                    </button>
                </div>

                <!-- Edit mode -->
                <div v-else class="mt-5 space-y-4">
                    <label class="flex items-center gap-3">
                        <input type="checkbox" v-model="form.is_active" class="h-4 w-4 rounded border-slate-300 text-teal-600 focus:ring-teal-500" />
                        <span class="text-sm text-slate-700">Passerelle active</span>
                    </label>

                    <div>
                        <label class="block text-xs font-medium text-slate-600 mb-1">Environnement</label>
                        <select v-model="form.environment" class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 focus:border-teal-500 focus:ring-teal-500">
                            <option value="sandbox">Sandbox</option>
                            <option value="live">Production (Live)</option>
                        </select>
                    </div>

                    <div>
                        <label class="block text-xs font-medium text-slate-600 mb-1">Cle publique</label>
                        <input type="text" v-model="form.public_key" :placeholder="gw.has_public_key ? 'Deja definie — laisser vide pour conserver' : 'pk_...'" class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 focus:border-teal-500 focus:ring-teal-500" />
                    </div>

                    <div>
                        <label class="block text-xs font-medium text-slate-600 mb-1">Cle secrete</label>
                        <input type="password" autocomplete="new-password" v-model="form.secret_key" :placeholder="gw.has_secret_key ? 'Deja definie — laisser vide pour conserver' : 'sk_...'" class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 focus:border-teal-500 focus:ring-teal-500" />
                    </div>

                    <div>
                        <label class="block text-xs font-medium text-slate-600 mb-1">Secret Webhook</label>
                        <input type="password" autocomplete="new-password" v-model="form.webhook_secret" :placeholder="gw.has_webhook_secret ? 'Deja defini — laisser vide pour conserver' : 'whsec_...'" class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 focus:border-teal-500 focus:ring-teal-500" />
                        <p class="mt-1 text-xs text-slate-500">Generez le secret dans votre dashboard Moneroo et copiez-le ici.</p>
                    </div>

                    <div class="grid grid-cols-2 gap-3">
                        <div>
                            <label class="block text-xs font-medium text-slate-600 mb-1">Frais paiement (%)</label>
                            <input type="number" step="0.01" min="0" max="99" v-model="form.payin_fee" class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 focus:border-teal-500 focus:ring-teal-500" />
                        </div>
                        <div>
                            <label class="block text-xs font-medium text-slate-600 mb-1">Frais retrait (%)</label>
                            <input type="number" step="0.01" min="0" max="99" v-model="form.payout_fee" class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 focus:border-teal-500 focus:ring-teal-500" />
                        </div>
                    </div>

                    <div>
                        <label class="block text-xs font-medium text-slate-600 mb-1">Priorite</label>
                        <input type="number" min="1" max="100" v-model="form.priority" class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 focus:border-teal-500 focus:ring-teal-500" />
                    </div>

                    <div class="space-y-2">
                        <label class="flex items-center gap-3">
                            <input type="checkbox" v-model="form.supports_payout" class="h-4 w-4 rounded border-slate-300 text-teal-600 focus:ring-teal-500" />
                            <span class="text-sm text-slate-700">Retraits (payouts) actives</span>
                        </label>
                        <label class="flex items-center gap-3">
                            <input type="checkbox" v-model="form.supports_refund" class="h-4 w-4 rounded border-slate-300 text-teal-600 focus:ring-teal-500" />
                            <span class="text-sm text-slate-700">Remboursements automatiques actives</span>
                        </label>
                    </div>

                    <div>
                        <label class="block text-xs font-medium text-slate-600 mb-2">Pays couverts</label>
                        <div class="grid grid-cols-2 gap-2">
                            <label v-for="c in AVAILABLE_COUNTRIES" :key="c.code" class="flex items-center gap-2 text-xs text-slate-700">
                                <input type="checkbox" :value="c.code" v-model="form.countries" class="h-4 w-4 rounded border-slate-300 text-teal-600 focus:ring-teal-500" />
                                <span>{{ c.label }}</span>
                            </label>
                        </div>
                    </div>

                    <div class="flex items-center gap-2">
                        <button @click="save(gw.id)" class="flex-1 rounded-lg bg-teal-600 px-4 py-2 text-xs font-semibold text-white shadow-sm transition hover:bg-teal-500">
                            Enregistrer
                        </button>
                        <button @click="cancelEdit" class="flex-1 rounded-lg border border-slate-300 px-4 py-2 text-xs font-semibold text-slate-700 transition hover:bg-slate-50">
                            Annuler
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>
