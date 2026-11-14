<script setup>
import { Head, Link, router } from '@inertiajs/vue3';
import { computed } from 'vue';
import Layout from '../Layout.vue';

defineOptions({ layout: Layout });

const props = defineProps({
    campaign:          { type: Object, required: true },
    paidClicks:        { type: Number, default: 0 },
    totalClicks:       { type: Number, default: 0 },
    influencerStats:   { type: Array, default: () => [] },
    invalidReasons:    { type: [Array, Object], default: () => [] },
    topCountries:      { type: [Array, Object], default: () => [] },
    vpnBlocked:        { type: Number, default: 0 },
    deviceDuplicates:  { type: Number, default: 0 },
    botsBlocked:       { type: Number, default: 0 },
    uniqueDevices:     { type: Number, default: 0 },
    recentFraudClicks: { type: [Array, Object], default: () => [] },
});

function toList(value) {
    if (Array.isArray(value)) return value;
    if (value && typeof value === 'object') return Object.values(value);
    return [];
}

const invalidReasonList = computed(() => toList(props.invalidReasons));
const topCountryList = computed(() => toList(props.topCountries));
const fraudClickList = computed(() => toList(props.recentFraudClicks));

const invalidClicks = computed(() => Math.max(0, props.totalClicks - props.paidClicks));

const validRate = computed(() => {
    if (!props.totalClicks) return 0;
    return Math.round((props.paidClicks / props.totalClicks) * 1000) / 10;
});

const influencerList = computed(() => toList(props.influencerStats));

const totalPaidOut = computed(() =>
    influencerList.value.reduce((sum, i) => sum + Number(i.total_paid || 0), 0)
);

function fmtMoney(value) {
    return new Intl.NumberFormat('fr-FR').format(Math.round(Number(value || 0))) + ' FCFA';
}

function fmtNumber(value) {
    return new Intl.NumberFormat('fr-FR').format(Number(value || 0));
}

function fmtDate(value) {
    if (!value) return '--';
    const d = new Date(value);
    return Number.isNaN(d.getTime()) ? '--' : d.toLocaleString('fr-FR');
}

const statusClass = computed(() => {
    switch (props.campaign?.status) {
        case 'active':    return 'bg-teal-50 text-teal-700';
        case 'paused':    return 'bg-amber-50 text-amber-700';
        case 'completed': return 'bg-slate-100 text-slate-600';
        default:          return 'bg-slate-100 text-slate-600';
    }
});

function togglePause() {
    router.post(route('admin.campaigns.toggle-pause', props.campaign.id), {}, {
        preserveScroll: true,
    });
}
</script>

<template>
    <div class="space-y-6">
        <Head :title="`Campagne — ${campaign.title}`" />

        <!-- Header -->
        <div class="flex flex-wrap items-start justify-between gap-4">
            <div>
                <Link :href="route('admin.campaigns.index')" class="text-xs font-medium text-slate-500 hover:text-slate-700">
                    &larr; Retour aux campagnes
                </Link>
                <h1 class="mt-1 text-2xl font-bold text-slate-900">{{ campaign.title }}</h1>
                <div class="mt-2 flex flex-wrap items-center gap-2">
                    <span class="inline-flex rounded-full px-2.5 py-0.5 text-xs font-semibold" :class="statusClass">
                        {{ campaign.status }}
                    </span>
                    <a
                        v-if="campaign.target_url"
                        :href="campaign.target_url"
                        target="_blank"
                        rel="noopener noreferrer"
                        class="truncate text-xs text-teal-700 hover:underline"
                    >
                        {{ campaign.target_url }}
                    </a>
                </div>
            </div>
            <div class="flex items-center gap-2">
                <button
                    @click="togglePause"
                    class="rounded-lg border border-slate-300 px-4 py-2 text-xs font-semibold text-slate-700 transition hover:bg-slate-50"
                >
                    {{ campaign.status === 'paused' ? 'Reactiver' : 'Mettre en pause' }}
                </button>
                <Link
                    :href="route('admin.campaigns.edit', campaign.id)"
                    class="rounded-lg bg-teal-600 px-4 py-2 text-xs font-semibold text-white shadow-sm transition hover:bg-teal-500"
                >
                    Modifier
                </Link>
            </div>
        </div>

        <!-- KPIs -->
        <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <div class="rounded-xl border border-slate-200 bg-white p-4">
                <p class="text-xs font-medium text-slate-500">Clics totaux</p>
                <p class="mt-1 text-2xl font-bold text-slate-900">{{ fmtNumber(totalClicks) }}</p>
            </div>
            <div class="rounded-xl border border-teal-200 bg-white p-4">
                <p class="text-xs font-medium text-slate-500">Clics payes</p>
                <p class="mt-1 text-2xl font-bold text-teal-700">{{ fmtNumber(paidClicks) }}</p>
                <p class="mt-1 text-xs text-slate-500">{{ validRate }} % valides</p>
            </div>
            <div class="rounded-xl border border-red-200 bg-white p-4">
                <p class="text-xs font-medium text-slate-500">Clics invalides</p>
                <p class="mt-1 text-2xl font-bold text-red-600">{{ fmtNumber(invalidClicks) }}</p>
            </div>
            <div class="rounded-xl border border-slate-200 bg-white p-4">
                <p class="text-xs font-medium text-slate-500">Total verse</p>
                <p class="mt-1 text-2xl font-bold text-slate-900">{{ fmtMoney(totalPaidOut) }}</p>
            </div>
        </div>

        <!-- Anti-fraude -->
        <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <div class="rounded-xl border border-slate-200 bg-white p-4">
                <p class="text-xs font-medium text-slate-500">VPN bloques</p>
                <p class="mt-1 text-xl font-bold text-slate-900">{{ fmtNumber(vpnBlocked) }}</p>
            </div>
            <div class="rounded-xl border border-slate-200 bg-white p-4">
                <p class="text-xs font-medium text-slate-500">Doublons appareil</p>
                <p class="mt-1 text-xl font-bold text-slate-900">{{ fmtNumber(deviceDuplicates) }}</p>
            </div>
            <div class="rounded-xl border border-slate-200 bg-white p-4">
                <p class="text-xs font-medium text-slate-500">Bots bloques</p>
                <p class="mt-1 text-xl font-bold text-slate-900">{{ fmtNumber(botsBlocked) }}</p>
            </div>
            <div class="rounded-xl border border-slate-200 bg-white p-4">
                <p class="text-xs font-medium text-slate-500">Appareils uniques</p>
                <p class="mt-1 text-xl font-bold text-slate-900">{{ fmtNumber(uniqueDevices) }}</p>
            </div>
        </div>

        <!-- Performance par createur -->
        <div class="rounded-xl border border-slate-200 bg-white">
            <div class="border-b border-slate-200 px-5 py-4">
                <h2 class="text-sm font-bold text-slate-900">Performance par createur</h2>
            </div>
            <div v-if="!influencerList.length" class="px-5 py-8 text-center text-sm text-slate-500">
                Aucun createur n'a encore genere de clic sur cette campagne.
            </div>
            <div v-else class="overflow-x-auto">
                <table class="min-w-full divide-y divide-slate-200 text-sm">
                    <thead class="bg-slate-50">
                        <tr>
                            <th class="px-5 py-3 text-left text-xs font-semibold text-slate-600">Createur</th>
                            <th class="px-5 py-3 text-right text-xs font-semibold text-slate-600">Clics</th>
                            <th class="px-5 py-3 text-right text-xs font-semibold text-slate-600">Payes</th>
                            <th class="px-5 py-3 text-right text-xs font-semibold text-slate-600">Commandes</th>
                            <th class="px-5 py-3 text-right text-xs font-semibold text-slate-600">CPC</th>
                            <th class="px-5 py-3 text-right text-xs font-semibold text-slate-600">CPA</th>
                            <th class="px-5 py-3 text-right text-xs font-semibold text-slate-600">Total</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-slate-100">
                        <tr v-for="inf in influencerList" :key="inf.influencer_id" class="hover:bg-slate-50">
                            <td class="px-5 py-3">
                                <div class="font-medium text-slate-900">{{ inf.influencer_name }}</div>
                                <div class="text-xs text-slate-500">{{ inf.influencer_tier }}</div>
                            </td>
                            <td class="px-5 py-3 text-right text-slate-700">{{ fmtNumber(inf.total_clicks) }}</td>
                            <td class="px-5 py-3 text-right font-medium text-teal-700">{{ fmtNumber(inf.paid_clicks) }}</td>
                            <td class="px-5 py-3 text-right text-slate-700">{{ fmtNumber(inf.orders_count) }}</td>
                            <td class="px-5 py-3 text-right text-slate-700">{{ fmtMoney(inf.cpc_earnings) }}</td>
                            <td class="px-5 py-3 text-right text-slate-700">{{ fmtMoney(inf.cpa_earnings) }}</td>
                            <td class="px-5 py-3 text-right font-bold text-slate-900">{{ fmtMoney(inf.total_paid) }}</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>

        <div class="grid gap-6 lg:grid-cols-2">
            <!-- Raisons d'invalidite -->
            <div class="rounded-xl border border-slate-200 bg-white">
                <div class="border-b border-slate-200 px-5 py-4">
                    <h2 class="text-sm font-bold text-slate-900">Raisons d'invalidite</h2>
                </div>
                <div v-if="!invalidReasonList.length" class="px-5 py-8 text-center text-sm text-slate-500">
                    Aucun clic invalide.
                </div>
                <ul v-else class="divide-y divide-slate-100">
                    <li v-for="(r, i) in invalidReasonList" :key="i" class="flex items-center justify-between px-5 py-3 text-sm">
                        <span class="text-slate-700">{{ r.invalid_reason ?? r.reason ?? 'Inconnu' }}</span>
                        <span class="font-semibold text-slate-900">{{ fmtNumber(r.total ?? r.count ?? 0) }}</span>
                    </li>
                </ul>
            </div>

            <!-- Top pays -->
            <div class="rounded-xl border border-slate-200 bg-white">
                <div class="border-b border-slate-200 px-5 py-4">
                    <h2 class="text-sm font-bold text-slate-900">Top pays</h2>
                </div>
                <div v-if="!topCountryList.length" class="px-5 py-8 text-center text-sm text-slate-500">
                    Aucune donnee de pays.
                </div>
                <ul v-else class="divide-y divide-slate-100">
                    <li v-for="(c, i) in topCountryList" :key="i" class="flex items-center justify-between px-5 py-3 text-sm">
                        <span class="text-slate-700">{{ c.clicker_country ?? c.country ?? 'Inconnu' }}</span>
                        <span class="font-semibold text-slate-900">{{ fmtNumber(c.total ?? c.count ?? 0) }}</span>
                    </li>
                </ul>
            </div>
        </div>

        <!-- Clics frauduleux recents -->
        <div class="rounded-xl border border-slate-200 bg-white">
            <div class="border-b border-slate-200 px-5 py-4">
                <h2 class="text-sm font-bold text-slate-900">Clics frauduleux recents</h2>
            </div>
            <div v-if="!fraudClickList.length" class="px-5 py-8 text-center text-sm text-slate-500">
                Aucun clic frauduleux detecte.
            </div>
            <div v-else class="overflow-x-auto">
                <table class="min-w-full divide-y divide-slate-200 text-sm">
                    <thead class="bg-slate-50">
                        <tr>
                            <th class="px-5 py-3 text-left text-xs font-semibold text-slate-600">Date</th>
                            <th class="px-5 py-3 text-left text-xs font-semibold text-slate-600">IP</th>
                            <th class="px-5 py-3 text-left text-xs font-semibold text-slate-600">Pays</th>
                            <th class="px-5 py-3 text-left text-xs font-semibold text-slate-600">VPN</th>
                            <th class="px-5 py-3 text-left text-xs font-semibold text-slate-600">Raison</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-slate-100">
                        <tr v-for="(c, i) in fraudClickList" :key="i" class="hover:bg-slate-50">
                            <td class="px-5 py-3 text-slate-600">{{ fmtDate(c.created_at) }}</td>
                            <td class="px-5 py-3 font-mono text-xs text-slate-700">{{ c.ip_address ?? '--' }}</td>
                            <td class="px-5 py-3 text-slate-700">{{ c.clicker_country ?? '--' }}</td>
                            <td class="px-5 py-3">
                                <span v-if="c.is_vpn" class="inline-flex rounded-full bg-red-50 px-2 py-0.5 text-xs font-semibold text-red-700">Oui</span>
                                <span v-else class="text-xs text-slate-400">Non</span>
                            </td>
                            <td class="px-5 py-3 text-slate-700">{{ c.invalid_reason ?? '--' }}</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</template>
