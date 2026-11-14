<script setup>
import { Head } from '@inertiajs/vue3';
import { ref, computed } from 'vue';
import PublicNavHeader from '@/Components/PublicNavHeader.vue';

const props = defineProps({
    min_cpc:                { type: Number, default: 25 },
    withdrawal_fee_percent: { type: Number, default: 20 },
    min_withdrawal_amount:  { type: Number, default: 1000 },
    ugc_studio_fee_percent: { type: Number, default: 15 },
    tier_thresholds:        { type: Object, default: () => ({ argent: 25000, or: 100000 }) },
});

function fmt(n) {
    return new Intl.NumberFormat('fr-FR').format(n);
}

const billingCycle = ref('monthly');

const vendorPlans = [
    { name: 'Free', priceMonthly: 0, priceAnnual: 0, tagline: 'Pour démarrer', features: ['1 boutique en ligne', 'Jusqu\'à 10 produits', 'Paiement par séquestre (escrow)', 'Tracy sur app + WhatsApp essai', '50 conversations/mois', 'Mode hybride 60s', 'Suivi de commandes'], cta: 'Commencer', highlighted: false },
    { name: 'Starter', priceMonthly: 2500, priceAnnual: 25500, annualDiscount: 15, tagline: 'Petits vendeurs', features: ['1 boutique', 'Jusqu\'à 50 produits', 'Tracy active + WhatsApp illimité', 'Mode hybride 30s', '10 relances/jour', 'Négociation automatique', 'Statistiques de vente'], cta: 'Choisir Starter', highlighted: false },
    { name: 'Standard', priceMonthly: 12000, priceAnnual: 115200, annualDiscount: 20, tagline: 'Pour grandir', features: ['3 boutiques', 'Jusqu\'à 200 produits', 'Tracy + WhatsApp auto 24/7', 'Relances illimitées', 'Synchronisation catalogue WhatsApp', 'Campagnes marketing IA (bientôt)', 'Priorité support'], cta: 'Choisir Standard', highlighted: true },
    { name: 'Pro', priceMonthly: 25000, priceAnnual: 225000, annualDiscount: 25, tagline: 'Pour les pros', features: ['Boutiques illimitées', 'Tracy + WhatsApp auto complet', 'Analytics avancés', 'Campagnes marketing illimitées (bientôt)', 'Support dédié priorité max', 'API d\'intégration', 'Multi-devises'], cta: 'Choisir Pro', highlighted: false },
];

function displayPrice(plan) {
    if (plan.priceMonthly === 0) return 'Gratuit';
    const price = billingCycle.value === 'monthly' ? plan.priceMonthly : plan.priceAnnual;
    return fmt(price);
}

function displayPeriod(plan) {
    if (plan.priceMonthly === 0) return '';
    return billingCycle.value === 'monthly' ? '/mois' : '/an';
}
</script>

<template>
    <Head title="Tarifs — MANTOTA" />

    <div class="min-h-screen bg-surface-1 text-grey-1">

        <!-- ═══ Nav Header ═══ -->
        <PublicNavHeader />

        <!-- ═══ Hero Header ═══ -->
        <header class="relative overflow-hidden bg-white border-b border-surface-3">
            <div class="adinkra-bg absolute inset-0 pointer-events-none"></div>
            <div class="absolute left-1/4 top-0 h-[400px] w-[400px] rounded-full bg-mantota-teal opacity-[0.07] blur-[100px]" />
            <div class="relative mx-auto max-w-6xl px-4 py-12 sm:px-6 sm:py-16 text-center">
                <!-- Logos MANTOTA + Tracy -->
                <div class="mb-6 flex items-center justify-center gap-4">
                    <img src="/images/mantota-logo.png" alt="MANTOTA" class="h-12 w-12 rounded-xl" />
                    <div class="h-8 w-px bg-surface-3"></div>
                    <div class="relative">
                        <img src="/images/tracy-avatar.jpeg" alt="Tracy IA" class="h-10 w-10 rounded-full object-cover ring-2 ring-mantota-teal/30" />
                        <span class="absolute -bottom-0.5 -right-0.5 h-3 w-3 rounded-full bg-mantota-teal ring-2 ring-white"></span>
                    </div>
                </div>
                <h1 class="text-2xl font-bold tracking-tight text-grey-1 sm:text-3xl md:text-4xl">Tarifs transparents</h1>
                <p class="mx-auto mt-4 max-w-2xl text-base text-grey-2 sm:text-lg">
                    Acheteur gratuit, vendeur freemium. Aucun frais caché.
                    Tracy IA gère votre boutique, négocie avec vos clients et automatise vos ventes.
                </p>

                <!-- Toggle Mensuel / Annuel -->
                <div class="mt-8 inline-flex items-center gap-1 rounded-mantoto-card border border-surface-3 bg-surface-1 p-1">
                    <button
                        @click="billingCycle = 'monthly'"
                        class="rounded-mantoto px-4 py-2 text-sm font-bold transition"
                        :class="billingCycle === 'monthly' ? 'bg-mantota-teal text-white' : 'text-grey-2 hover:text-grey-1'"
                    >Mensuel</button>
                    <button
                        @click="billingCycle = 'annual'"
                        class="rounded-mantoto px-4 py-2 text-sm font-bold transition flex items-center gap-1.5"
                        :class="billingCycle === 'annual' ? 'bg-mantota-teal text-white' : 'text-grey-2 hover:text-grey-1'"
                    >
                        Annuel
                        <span class="rounded-full bg-mantota-teal-pale px-2 py-0.5 text-[10px] font-bold text-mantota-teal-dark" :class="billingCycle === 'annual' ? 'bg-white/20 text-white' : ''">-15 à -25%</span>
                    </button>
                </div>
            </div>
        </header>

        <!-- ═══ Acheteur — Gratuit ═══ -->
        <section class="mx-auto max-w-6xl px-4 py-10 sm:px-6">
            <div class="relative rounded-mantota-card bg-white p-6 shadow-mantota sm:p-8 overflow-hidden">
                <div class="adinkra-bg absolute inset-0 pointer-events-none"></div>
                <div class="relative flex flex-col items-center text-center sm:flex-row sm:text-left sm:justify-between gap-6">
                    <div class="flex items-center gap-4">
                        <div class="flex h-14 w-14 shrink-0 items-center justify-center rounded-mantota bg-mantota-teal-pale ring-1 ring-mantota-teal/20">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-7 w-7 text-mantota-teal-dark" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M15.75 10.5V6a3.75 3.75 0 10-7.5 0v4.5m11.356-1.993l1.263 12c.07.665-.45 1.243-1.119 1.243H4.25a1.125 1.125 0 01-1.12-1.243l1.264-12A1.125 1.125 0 015.513 7.5h12.974c.576 0 1.059.435 1.119 1.007z" /></svg>
                        </div>
                        <div>
                            <h2 class="text-xl font-bold text-grey-1">Acheteur</h2>
                            <p class="mt-1 text-sm text-grey-2">Toujours gratuit, aucune commission pour l'acheteur</p>
                        </div>
                    </div>
                    <div class="text-center sm:text-right">
                        <span class="text-3xl font-bold text-mantota-teal-dark">0 FCFA</span>
                        <p class="text-xs text-grey-2 mt-1">Paiement sécurisé par séquestre</p>
                    </div>
                </div>
            </div>
        </section>

        <!-- ═══ Vendeur — Plans Freemium ═══ -->
        <section class="relative mx-auto max-w-6xl px-4 py-6 sm:px-6">
            <div class="adinkra-bg absolute inset-0 pointer-events-none"></div>
            <div class="relative mb-8 text-center">
                <h2 class="text-2xl font-bold text-grey-1">Plans Vendeur</h2>
                <p class="mt-2 text-sm text-grey-2">Choisissez le plan qui correspond à votre activité. Changez ou annulez à tout moment.</p>
            </div>

            <div class="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
                <div
                    v-for="plan in vendorPlans"
                    :key="plan.name"
                    class="flex flex-col rounded-mantota-card bg-white p-6 shadow-mantota transition hover:shadow-mantota-md"
                    :class="plan.highlighted ? 'ring-2 ring-mantota-teal' : ''"
                >
                    <div v-if="plan.highlighted" class="mb-3">
                        <span class="inline-flex items-center gap-1 rounded-full bg-mantota-teal px-3 py-1 text-xs font-bold text-white">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3" fill="currentColor" viewBox="0 0 20 20"><path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" /></svg>
                            Populaire
                        </span>
                    </div>

                    <h3 class="text-lg font-bold text-grey-1">{{ plan.name }}</h3>
                    <p class="text-xs text-grey-2 mt-0.5">{{ plan.tagline }}</p>

                    <div class="mt-4 mb-5">
                        <span class="text-2xl font-bold text-mantota-teal-dark">{{ displayPrice(plan) }}</span>
                        <span v-if="displayPeriod(plan)" class="text-sm text-grey-2">{{ displayPeriod(plan) }}</span>
                        <span v-if="plan.priceMonthly !== 0" class="text-sm text-grey-2"> FCFA</span>
                        <div v-if="billingCycle === 'annual' && plan.annualDiscount" class="mt-1">
                            <span class="inline-flex items-center rounded-full bg-mantota-teal-pale px-2 py-0.5 text-[10px] font-bold text-mantota-teal-dark">
                                -{{ plan.annualDiscount }}% vs mensuel
                            </span>
                        </div>
                    </div>

                    <ul class="flex-1 space-y-2.5">
                        <li v-for="feature in plan.features" :key="feature" class="flex items-start gap-2 text-sm text-grey-2">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 shrink-0 text-mantota-teal mt-0.5" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                            {{ feature }}
                        </li>
                    </ul>

                    <button
                        class="mt-6 w-full rounded-mantota px-4 py-3 text-sm font-bold transition active:scale-[0.98]"
                        :class="plan.highlighted ? 'bg-mantota-teal text-white hover:bg-mantota-teal-dark' : 'border-2 border-surface-4 text-grey-1 hover:border-mantota-teal hover:text-mantota-teal-dark'"
                    >
                        {{ plan.cta }}
                    </button>
                </div>
            </div>
        </section>

        <!-- ═══ Partenaire — Bientôt disponible ═══ -->
        <section class="mx-auto max-w-6xl px-4 py-6 sm:px-6">
            <div class="relative rounded-mantota-card bg-white p-6 shadow-mantota sm:p-8 overflow-hidden">
                <div class="adinkra-bg absolute inset-0 pointer-events-none"></div>
                <div class="relative flex flex-col items-center text-center sm:flex-row sm:text-left sm:justify-between gap-6">
                    <div class="flex items-center gap-4">
                        <div class="flex h-14 w-14 shrink-0 items-center justify-center rounded-mantota bg-surface-1 ring-1 ring-surface-3">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-7 w-7 text-grey-2" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M18 18.72a9.094 9.094 0 003.741-.479 3 3 0 00-4.682-2.72m.94 3.198l.001.031c0 .225-.012.447-.037.666A11.944 11.944 0 0112 21c-2.17 0-4.207-.576-5.963-1.584A6.062 6.062 0 016 18.719m12 0a5.971 5.971 0 00-.941-3.197m0 0A5.995 5.995 0 0012 12.75a5.995 5.995 0 00-5.058 2.772m0 0a3 3 0 00-4.681 2.72 8.986 8.986 0 003.74.477m.94-3.197a5.971 5.971 0 00-.94 3.197M15 6.75a3 3 0 11-6 0 3 3 0 016 0zm6 3a2.25 2.25 0 11-4.5 0 2.25 2.25 0 014.5 0zm-13.5 0a2.25 2.25 0 11-4.5 0 2.25 2.25 0 014.5 0z" /></svg>
                        </div>
                        <div>
                            <div class="flex items-center gap-2">
                                <h2 class="text-xl font-bold text-grey-1">Partenaire (Créateur de contenu)</h2>
                                <span class="inline-flex items-center rounded-full bg-surface-1 px-2.5 py-0.5 text-xs font-bold text-grey-2">Bientôt disponible</span>
                            </div>
                            <p class="mt-1 text-sm text-grey-2">Gratuit + commission sur clics et ventes générées</p>
                        </div>
                    </div>
                    <div class="text-center sm:text-right">
                        <span class="text-3xl font-bold text-grey-2">0 FCFA</span>
                        <p class="text-xs text-grey-2 mt-1">Commission sur performance</p>
                    </div>
                </div>
            </div>
        </section>

        <!-- ═══ Tracy IA ═══ -->
        <section class="relative mx-auto max-w-6xl px-4 py-10 sm:px-6">
            <div class="adinkra-bg absolute inset-0 pointer-events-none"></div>
            <div class="relative rounded-mantota-card bg-gradient-to-br from-mantota-teal-pale to-surface-1 p-6 sm:p-10">
                <div class="flex flex-col items-center gap-6 sm:flex-row sm:justify-between">
                    <div class="flex items-center gap-5">
                        <div class="relative shrink-0">
                            <img src="/images/tracy-avatar.jpeg" alt="Tracy" class="h-16 w-16 rounded-full object-cover ring-2 ring-mantota-teal/30" />
                            <span class="absolute -bottom-0.5 -right-0.5 h-3.5 w-3.5 rounded-full bg-mantota-teal ring-2 ring-white"></span>
                        </div>
                        <div>
                            <h2 class="text-xl font-bold text-grey-1">Tracy IA</h2>
                            <p class="mt-1 text-sm text-grey-2">Votre assistante commerciale IA intégrée</p>
                        </div>
                    </div>
                    <div class="text-center sm:text-right">
                        <p class="text-sm text-grey-2">Disponible sur tous les plans</p>
                        <p class="text-xs text-grey-2 mt-1">Free : 50 conv/mois · Pro : auto 24/7</p>
                    </div>
                </div>

                <div class="mt-8 grid gap-4 sm:grid-cols-3">
                    <div class="rounded-mantota bg-white p-5 shadow-mantota">
                        <div class="flex h-10 w-10 items-center justify-center rounded-mantota bg-mantota-teal-pale mb-3">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-mantota-teal-dark" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M7.5 8.25h9m-9 3H12m-9.75 1.51c0 1.6 1.123 2.994 2.707 3.227 1.129.166 2.27.293 3.423.379.35.026.67.21.865.501L12 21l2.755-4.133a1.14 1.14 0 01.865-.501 48.172 48.172 0 003.423-.379c1.584-.233 2.707-1.626 2.707-3.228V6.741c0-1.602-1.123-2.995-2.707-3.228A48.394 48.394 0 0012 3c-2.392 0-4.744.175-7.043.513C3.373 3.746 2.25 5.14 2.25 6.741v6.018z" /></svg>
                        </div>
                        <h3 class="text-sm font-bold text-grey-1">Répond aux clients</h3>
                        <p class="mt-1 text-xs text-grey-2">Tracy discute avec vos clients 24/7, répond aux questions sur vos produits.</p>
                    </div>
                    <div class="rounded-mantota bg-white p-5 shadow-mantota">
                        <div class="flex h-10 w-10 items-center justify-center rounded-mantota bg-mantota-teal-pale mb-3">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-mantota-teal-dark" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M3.75 3v11.25A2.25 2.25 0 006 16.5h2.25M3.75 3h-1.5m1.5 0h16.5m0 0h1.5m-1.5 0v11.25A2.25 2.25 0 0118 16.5h-2.25m-7.5 0h7.5m-7.5 0l-1 3m8.5-3l1 3m0 0l.5 1.5m-.5-1.5h-9.5m0 0l-.5 1.5M9 11.25v1.5M12 9v3.75m3-6v6" /></svg>
                        </div>
                        <h3 class="text-sm font-bold text-grey-1">Négocie les prix</h3>
                        <p class="mt-1 text-xs text-grey-2">Tracy négocie avec vos clients selon vos règles de marge et de remise.</p>
                    </div>
                    <div class="rounded-mantota bg-white p-5 shadow-mantota">
                        <div class="flex h-10 w-10 items-center justify-center rounded-mantota bg-mantota-teal-pale mb-3">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-mantota-teal-dark" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" /></svg>
                        </div>
                        <h3 class="text-sm font-bold text-grey-1">Sécurise les ventes</h3>
                        <p class="mt-1 text-xs text-grey-2">Paiement par séquestre, création de commandes, suivi automatique.</p>
                    </div>
                </div>
            </div>
        </section>

        <!-- ═══ Frais de transaction ═══ -->
        <section class="relative mx-auto max-w-6xl px-4 py-10 sm:px-6">
            <div class="adinkra-bg absolute inset-0 pointer-events-none"></div>
            <div class="relative mb-6 text-center">
                <h2 class="text-2xl font-bold text-grey-1">Frais de transaction</h2>
                <p class="mt-2 text-sm text-grey-2">Des frais transparents, mis à jour en temps réel par l'administration.</p>
            </div>

            <div class="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
                <div class="rounded-mantota-card bg-white p-6 shadow-mantota">
                    <div class="flex items-center gap-3 mb-4">
                        <div class="flex h-10 w-10 items-center justify-center rounded-mantota bg-mantota-teal-pale">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-mantota-teal-dark" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M2.25 8.25h19.5M2.25 9h19.5m-16.5 5.25h6m-6 2.25h3m-3.75 3h15a2.25 2.25 0 002.25-2.25V6.75A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25v10.5A2.25 2.25 0 004.5 19.5z" /></svg>
                        </div>
                        <h3 class="text-base font-bold text-grey-1">Retrait</h3>
                    </div>
                    <div class="space-y-2">
                        <div class="flex justify-between text-sm">
                            <span class="text-grey-2">Frais de retrait</span>
                            <span class="font-bold text-grey-1">{{ withdrawal_fee_percent }}%</span>
                        </div>
                        <div class="flex justify-between text-sm">
                            <span class="text-grey-2">Montant minimum</span>
                            <span class="font-bold text-grey-1">{{ fmt(min_withdrawal_amount) }} FCFA</span>
                        </div>
                    </div>
                    <div class="mt-4 rounded-mantota bg-surface-1 px-4 py-3">
                        <p class="text-xs text-grey-2">
                            <strong class="text-grey-1">Exemple :</strong> Pour {{ fmt(10000) }} FCFA → frais {{ fmt(10000 * withdrawal_fee_percent / 100) }} FCFA → vous recevez {{ fmt(10000 - 10000 * withdrawal_fee_percent / 100) }} FCFA.
                        </p>
                    </div>
                </div>

                <div class="rounded-mantota-card bg-white p-6 shadow-mantota">
                    <div class="flex items-center gap-3 mb-4">
                        <div class="flex h-10 w-10 items-center justify-center rounded-mantota bg-mantota-teal-pale">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-mantota-teal-dark" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M2.25 3h1.386c.51 0 .955.343 1.087.835l.383 1.437M7.5 14.25a3 3 0 00-3 3h15.75m-12.75-3h11.218c1.121-2.3 2.1-4.684 2.924-7.138a60.114 60.114 0 00-16.536-1.84M7.5 14.25L5.106 5.272M6 20.25a.75.75 0 11-1.5 0 .75.75 0 011.5 0zm12.75 0a.75.75 0 11-1.5 0 .75.75 0 011.5 0z" /></svg>
                        </div>
                        <h3 class="text-base font-bold text-grey-1">E-commerce</h3>
                    </div>
                    <div class="space-y-2">
                        <div class="flex justify-between text-sm">
                            <span class="text-grey-2">Commission transaction</span>
                            <span class="font-bold text-grey-1">2-5%</span>
                        </div>
                        <div class="flex justify-between text-sm">
                            <span class="text-grey-2">Paiement sécurisé</span>
                            <span class="font-bold text-mantota-teal-dark">Escrow</span>
                        </div>
                    </div>
                    <div class="mt-4 rounded-mantota bg-surface-1 px-4 py-3">
                        <p class="text-xs text-grey-2">
                            Commission plateforme sur chaque vente. Paiement sous séquestre — le vendeur est payé après confirmation de livraison.
                        </p>
                    </div>
                </div>

                <div class="relative rounded-mantota-card bg-white p-6 shadow-mantota overflow-hidden">
                    <div class="adinkra-bg absolute inset-0 pointer-events-none"></div>
                    <div class="relative">
                        <div class="flex items-center gap-3 mb-4">
                            <div class="flex h-10 w-10 items-center justify-center rounded-mantota bg-surface-1">
                                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-grey-2" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" /></svg>
                            </div>
                            <div class="flex items-center gap-2">
                                <h3 class="text-base font-bold text-grey-1">Campagnes IA</h3>
                                <span class="inline-flex items-center rounded-full bg-surface-1 px-2 py-0.5 text-[10px] font-bold text-grey-2">Bientôt</span>
                            </div>
                        </div>
                        <div class="space-y-2">
                            <div class="flex justify-between text-sm">
                                <span class="text-grey-2">CPC minimum</span>
                                <span class="font-bold text-grey-1">{{ fmt(min_cpc) }} FCFA</span>
                            </div>
                            <div class="flex justify-between text-sm">
                                <span class="text-grey-2">Commission UGC</span>
                                <span class="font-bold text-grey-1">{{ ugc_studio_fee_percent }}%</span>
                            </div>
                        </div>
                        <div class="mt-4 rounded-mantota bg-surface-1 px-4 py-3">
                            <p class="text-xs text-grey-2">
                                Lancez des campagnes marketing avec Tracy IA. Vous ne payez que les clics qualifiés.
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        </section>

        <!-- ═══ CTA ═══ -->
        <section class="relative mx-auto max-w-6xl px-4 py-12 sm:px-6 text-center">
            <div class="adinkra-bg absolute inset-0 pointer-events-none"></div>
            <div class="relative rounded-mantota-card bg-white p-8 shadow-mantota">
                <h2 class="text-xl font-bold text-grey-1">Prêt à commencer ?</h2>
                <p class="mt-2 text-sm text-grey-2">Discutez avec Tracy IA ou téléchargez l'app MANTOTA.</p>
                <div class="mt-6 flex flex-col items-center justify-center gap-3 sm:flex-row">
                    <a :href="route('home')" class="inline-flex items-center gap-2 rounded-mantota bg-mantota-teal px-6 py-3 text-sm font-bold text-white transition hover:bg-mantota-teal-dark active:scale-[0.98]">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M7.5 8.25h9m-9 3H12m-9.75 1.51c0 1.6 1.123 2.994 2.707 3.227 1.129.166 2.27.293 3.423.379.35.026.67.21.865.501L12 21l2.755-4.133a1.14 1.14 0 01.865-.501 48.172 48.172 0 003.423-.379c1.584-.233 2.707-1.626 2.707-3.228V6.741c0-1.602-1.123-2.995-2.707-3.228A48.394 48.394 0 0012 3c-2.392 0-4.744.175-7.043.513C3.373 3.746 2.25 5.14 2.25 6.741v6.018z" /></svg>
                        Discuter avec Tracy
                    </a>
                    <a :href="route('support.create')" class="inline-flex items-center gap-2 rounded-mantota border-2 border-surface-4 bg-white px-6 py-3 text-sm font-bold text-grey-1 transition hover:border-mantota-teal hover:text-mantota-teal-dark active:scale-[0.98]">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M9.879 7.519c1.171-1.025 3.071-1.025 4.242 0 1.172 1.025 1.172 2.687 0 3.712-.203.179-.43.326-.67.442-.745.361-1.45.999-1.45 1.827v.75M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9 5.25h.008v.008H12v-.008z" /></svg>
                        Contacter le support
                    </a>
                </div>
            </div>
        </section>

        <!-- ═══ Footer ═══ -->
        <footer class="relative border-t border-surface-3 bg-white overflow-hidden">
            <div class="adinkra-bg absolute inset-0 pointer-events-none"></div>
            <div class="relative mx-auto max-w-6xl px-4 py-6 sm:px-6">
                <div class="flex flex-col items-center justify-between gap-4 sm:flex-row">
                    <div class="flex items-center gap-2">
                        <img src="/images/mantota-logo.png" alt="Mantota" class="h-8 w-8 rounded-xl" />
                        <span class="text-sm font-bold text-grey-1">MANTOTA</span>
                    </div>
                    <div class="flex flex-wrap items-center gap-x-4 gap-y-2">
                        <a :href="route('about')" class="inline-flex items-center gap-1 text-xs text-grey-2 hover:text-mantota-teal transition">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.852l.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z" /></svg>
                            À propos
                        </a>
                        <a :href="route('tarifs')" class="inline-flex items-center gap-1 text-xs text-grey-2 hover:text-mantota-teal transition">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M2.25 18.75a60.07 60.07 0 0115.797 2.101c.727.198 1.453-.342 1.453-1.096V18.75M3.75 4.5v.75A.75.75 0 013 6h-.75m0 0v-.375c0-.621.504-1.125 1.125-1.125H20.25M2.25 6v9m18-10.5v.75c0 .414.336.75.75.75h.75m-1.5-1.5h.375c.621 0 1.125.504 1.125 1.125v9.75c0 .621-.504 1.125-1.125 1.125h-.375m1.5-1.5H21a.75.75 0 00-.75.75v.75m0 0H3.75m0 0h-.375a1.125 1.125 0 01-1.125-1.125V15m1.5 1.5v-.75A.75.75 0 003 15h-.75M15 10.5a3 3 0 11-6 0 3 3 0 016 0zm3 0h.008v.008H18V10.5zm-12 0h.008v.008H6V10.5z" /></svg>
                            Tarifs
                        </a>
                        <a :href="route('documentation')" class="inline-flex items-center gap-1 text-xs text-grey-2 hover:text-mantota-teal transition">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 016-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0018 18a8.967 8.967 0 00-6 2.292m0-14.25v14.25" /></svg>
                            Documentation
                        </a>
                        <a :href="route('support.create')" class="inline-flex items-center gap-1 text-xs text-grey-2 hover:text-mantota-teal transition">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M9.879 7.519c1.171-1.025 3.071-1.025 4.242 0 1.172 1.025 1.172 2.687 0 3.712-.203.179-.43.326-.67.442-.745.361-1.45.999-1.45 1.827v.75M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9 5.25h.008v.008H12v-.008z" /></svg>
                            Support
                        </a>
                        <a :href="route('legal.terms')" class="inline-flex items-center gap-1 text-xs text-grey-2 hover:text-mantota-teal transition">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" /></svg>
                            CGV
                        </a>
                        <a :href="route('legal.privacy')" class="inline-flex items-center gap-1 text-xs text-grey-2 hover:text-mantota-teal transition">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" /></svg>
                            Confidentialité
                        </a>
                    </div>
                </div>
            </div>
        </footer>
    </div>
</template>

<style scoped>
.adinkra-bg {
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='80' height='80'%3E%3Cg fill='none' stroke='%230BBFA0' stroke-width='0.8'%3E%3Ccircle cx='40' cy='40' r='16'/%3E%3Ccircle cx='40' cy='40' r='8'/%3E%3Cpath d='M40 24L40 10M40 56L40 70M24 40L10 40M56 40L70 40'/%3E%3Cpath d='M29 29L18 18M51 51L62 62M51 29L62 18M29 51L18 62'/%3E%3Ccircle cx='40' cy='40' r='28' stroke-dasharray='4 5'/%3E%3Cpath d='M40 12 L44 20 L40 18 L36 20 Z'/%3E%3C/g%3E%3C/svg%3E");
    background-size: 80px 80px;
    opacity: 0.08;
}
</style>
