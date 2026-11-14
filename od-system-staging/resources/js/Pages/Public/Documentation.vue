<script setup>
import { Head, usePage } from '@inertiajs/vue3';
import { computed, ref } from 'vue';
import PublicNavHeader from '@/Components/PublicNavHeader.vue';

const props = defineProps({
    doc_vendor_intro: { type: String, default: '' },
    doc_influencer_intro: { type: String, default: '' },
    doc_general_intro: { type: String, default: '' },
});

const page = usePage();
const gs = computed(() => page.props.global_settings || {});
const activeTab = ref('vendeur');

const tabs = [
    { key: 'vendeur', label: 'Vendeurs', icon: 'M2.25 3h1.386c.51 0 .955.343 1.087.835l.383 1.437M7.5 14.25a3 3 0 00-3 3h15.75m-12.75-3h11.218c1.121-2.3 2.1-4.684 2.924-7.138a60.114 60.114 0 00-16.536-1.84M7.5 14.25L5.106 5.272M6 20.25a.75.75 0 11-1.5 0 .75.75 0 011.5 0zm12.75 0a.75.75 0 11-1.5 0 .75.75 0 011.5 0z' },
    { key: 'acheteur', label: 'Acheteurs', icon: 'M15.75 10.5V6a3.75 3.75 0 10-7.5 0v4.5m11.356-1.993l1.263 12c.07.665-.45 1.243-1.119 1.243H4.25a1.125 1.125 0 01-1.12-1.243l1.264-12A1.125 1.125 0 015.513 7.5h12.974c.576 0 1.059.435 1.119 1.007z' },
    { key: 'tracy', label: 'Tracy IA', icon: 'M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z' },
    { key: 'general', label: 'Général', icon: 'M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.852l.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z' },
];
</script>

<template>
    <Head title="Documentation — MANTOTA" />

    <div class="min-h-screen bg-surface-1 text-grey-1">

        <!-- ═══ Nav Header ═══ -->
        <PublicNavHeader />

        <!-- ═══ Hero Header ═══ -->
        <header class="relative overflow-hidden bg-white border-b border-surface-3">
            <div class="adinkra-bg absolute inset-0 pointer-events-none"></div>
            <div class="absolute right-1/4 top-0 h-[400px] w-[400px] rounded-full bg-mantota-teal opacity-[0.07] blur-[100px]" />
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
                <h1 class="text-2xl font-bold tracking-tight text-grey-1 sm:text-3xl md:text-4xl">Documentation</h1>
                <p class="mx-auto mt-4 max-w-2xl text-base text-grey-2 sm:text-lg">
                    Tout ce que vous devez savoir pour utiliser MANTOTA et Tracy IA efficacement.
                </p>
                <!-- Version badges -->
                <div class="mt-6 flex items-center justify-center gap-3">
                    <span class="inline-flex items-center gap-1.5 rounded-full bg-mantota-teal-pale px-3 py-1 text-xs font-bold text-mantota-teal-dark">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M9 17.25v1.007a3 3 0 01-.879 2.122L7.5 21h9l-.621-.621A3 3 0 0115 18.257V17.25m6-12V15a2.25 2.25 0 01-2.25 2.25H5.25A2.25 2.25 0 013 15V5.25m18 0A2.25 2.25 0 0018.75 3H5.25A2.25 2.25 0 003 5.25m18 0V12a2.25 2.25 0 01-2.25 2.25H5.25A2.25 2.25 0 013 12V5.25" /></svg>
                        Web v2.0
                    </span>
                    <span class="inline-flex items-center gap-1.5 rounded-full bg-surface-2 px-3 py-1 text-xs font-bold text-grey-2">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M10.5 1.5H8.25A2.25 2.25 0 006 3.75v16.5a2.25 2.25 0 002.25 2.25h7.5A2.25 2.25 0 0018 20.25V3.75a2.25 2.25 0 00-2.25-2.25H13.5m-3 0V3h3V1.5m-3 0h3m-3 18.75h3" /></svg>
                        APK v1.0
                    </span>
                </div>
            </div>
        </header>

        <!-- ═══ Tabs + Content ═══ -->
        <section class="relative mx-auto max-w-5xl px-4 py-10 sm:px-6">
            <div class="adinkra-bg absolute inset-0 pointer-events-none"></div>
            <div class="relative">
                <!-- Tab bar -->
                <div class="mb-8 flex justify-center">
                    <div class="inline-flex rounded-mantota border border-surface-3 bg-white p-1 shadow-mantota">
                        <button
                            v-for="t in tabs"
                            :key="t.key"
                            @click="activeTab = t.key"
                            :class="[
                                'inline-flex items-center gap-1.5 rounded-mantota px-4 py-2 text-sm font-medium transition-all sm:px-5',
                                activeTab === t.key
                                    ? 'bg-mantota-teal text-white shadow-sm'
                                    : 'text-grey-2 hover:text-mantota-teal-dark',
                            ]"
                        >
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" :d="t.icon" /></svg>
                            <span class="hidden sm:inline">{{ t.label }}</span>
                        </button>
                    </div>
                </div>

                <!-- ═══ VENDEUR ═══ -->
                <div v-if="activeTab === 'vendeur'" class="space-y-5">
                    <p v-if="doc_vendor_intro" class="mb-4 text-sm leading-relaxed text-grey-2">{{ doc_vendor_intro }}</p>

                    <div v-for="(s, i) in [
                        { title: '1. Créer un compte vendeur', items: ['Rendez-vous sur la page d\'inscription vendeur.', 'Fournissez : Nom complet, email, Nom de la boutique (slug unique), Mot de passe (min. 8 caractères).', 'Après inscription, votre compte doit être vérifié (KYC) par l\'administration.'] },
                        { title: '2. Ajouter des produits', items: ['Depuis votre tableau de bord, allez dans Produits > Nouveau produit.', 'Ajoutez un nom, une description, un prix et des images.', 'Définissez le pourcentage de commission que le créateur de contenu recevra sur chaque vente.', 'Choisissez le type : physique (avec livraison) ou digital.'] },
                        { title: '3. Configurer Tracy IA', items: ['Depuis votre tableau de bord, allez dans Paramètres > Tracy IA.', 'Définissez vos règles de marge minimum et maximum.', 'Configurez les remises autorisées (par produit ou globale).', 'Activez WhatsApp pour permettre à Tracy de discuter avec vos clients sur WhatsApp.', 'Choisissez le mode hybride : automatique (Tracy gère tout) ou manuel (vous validez chaque commande).'] },
                        { title: '4. Suivre les performances', items: ['Nombre de conversations gérées par Tracy.', 'Taux de conversion : conversations → commandes.', 'Commandes et ventes générées.', 'Revenu total et commissions payées.', 'Budget restant et dépenses.'] },
                    ]" :key="i" class="rounded-mantota-card bg-white shadow-mantota overflow-hidden">
                        <div class="border-b border-surface-3 bg-mantota-teal-pale px-6 py-4">
                            <h2 class="text-base font-bold text-grey-1">{{ s.title }}</h2>
                        </div>
                        <div class="p-6">
                            <ul class="ml-4 list-disc space-y-2 text-sm leading-relaxed text-grey-2">
                                <li v-for="(item, j) in s.items" :key="j">{{ item }}</li>
                            </ul>
                        </div>
                    </div>
                </div>

                <!-- ═══ ACHETEUR ═══ -->
                <div v-if="activeTab === 'acheteur'" class="space-y-5">
                    <div v-for="(s, i) in [
                        { title: '1. Créer un compte acheteur', items: ['L\'inscription est gratuite et ouverte à tous.', 'Fournissez : Nom, email, mot de passe.', 'Aucune vérification KYC requise pour les acheteurs.'] },
                        { title: '2. Parcourir les boutiques', items: ['Découvrez les boutiques et produits disponibles sur MANTOTA.', 'Utilisez les filtres par catégorie, prix et popularité.', 'Ajoutez vos produits favoris au panier.'] },
                        { title: '3. Discuter avec Tracy IA', items: ['Tracy IA est disponible 24/7 pour répondre à vos questions.', 'Posez des questions sur les produits, demandez des remises.', 'Tracy négocie automatiquement avec vous selon les règles du vendeur.', 'Vous pouvez aussi contacter le vendeur directement si besoin.'] },
                        { title: '4. Passer commande', items: ['Tracy crée la commande automatiquement après negotiation.', 'Le paiement est sécurisé par séquestre (escrow).', 'Vos fonds sont libérés au vendeur seulement après réception du produit.', 'Suivez votre commande en temps réel depuis votre dashboard.'] },
                        { title: '5. Ouvrir un litige', items: ['Si vous rencontrez un problème avec une commande, ouvrez un litige.', 'Fournissez des preuves (photos, messages).', 'L\'équipe MANTOTA trananche sous 48h.', 'Le remboursement est automatique si le litige est validé.'] },
                    ]" :key="i" class="rounded-mantota-card bg-white shadow-mantota overflow-hidden">
                        <div class="border-b border-surface-3 bg-mantota-teal-pale px-6 py-4">
                            <h2 class="text-base font-bold text-grey-1">{{ s.title }}</h2>
                        </div>
                        <div class="p-6">
                            <ul class="ml-4 list-disc space-y-2 text-sm leading-relaxed text-grey-2">
                                <li v-for="(item, j) in s.items" :key="j">{{ item }}</li>
                            </ul>
                        </div>
                    </div>
                </div>

                <!-- ═══ TRACY IA ═══ -->
                <div v-if="activeTab === 'tracy'" class="space-y-5">
                    <div class="rounded-mantota-card bg-gradient-to-br from-mantota-teal-pale to-surface-1 p-6 sm:p-8">
                        <div class="flex items-center gap-4">
                            <img src="/images/tracy-avatar.jpeg" alt="Tracy" class="h-14 w-14 rounded-full object-cover ring-2 ring-mantota-teal/30" />
                            <div>
                                <h2 class="text-lg font-bold text-grey-1">Tracy IA</h2>
                                <p class="text-sm text-grey-2">L'assistante commerciale intelligente de MANTOTA</p>
                            </div>
                        </div>
                    </div>

                    <div v-for="(s, i) in [
                        { title: 'Qu\'est-ce que Tracy IA ?', items: ['Tracy est une IA conversationnelle intégrée à MANTOTA.', 'Elle discute avec les clients sur l\'app et WhatsApp.', 'Elle négocie les prix selon les règles définies par le vendeur.', 'Elle crée les commandes et gère le suivi automatiquement.'] },
                        { title: 'Configurer Tracy', items: ['Allez dans Paramètres > Tracy IA depuis votre dashboard vendeur.', 'Définissez votre marge minimum (prix plancher).', 'Définissez votre remise maximum autorisée (ex: 10%).', 'Choisissez le mode hybride : 60s (Free), 30s (Starter), auto 24/7 (Standard/Pro).', 'Activez WhatsApp pour permettre à Tracy de répondre sur WhatsApp.'] },
                        { title: 'Mode hybride', items: ['Le mode hybride détermine le temps d\'attente avant que Tracy ne prenne la relance.', 'Free : 60 secondes — Tracy attend 60s avant de répondre.', 'Starter : 30 secondes — réponse plus rapide.', 'Standard/Pro : Auto 24/7 — Tracy gère tout en continu.', 'Vous pouvez toujours reprendre la main à tout moment.'] },
                        { title: 'Relances automatiques', items: ['Tracy relance automatiquement les clients qui abandonnent leur panier.', 'Free : 0 relance/jour.', 'Starter : 10 relances/jour.', 'Standard/Pro : relances illimitées.', 'Les relances sont envoyées via WhatsApp ou notification app.'] },
                        { title: 'Limites par plan', items: ['Free : 50 conversations/mois, hybride 60s, 0 relance.', 'Starter : conversations illimitées, WhatsApp illimité, hybride 30s, 10 relances/jour.', 'Standard : Tracy + WhatsApp auto 24/7, relances illimitées, sync catalogue.', 'Pro : Tout Standard + analytics + campagnes IA + priorité support.'] },
                    ]" :key="i" class="rounded-mantota-card bg-white shadow-mantota overflow-hidden">
                        <div class="border-b border-surface-3 bg-mantota-teal-pale px-6 py-4">
                            <h2 class="text-base font-bold text-grey-1">{{ s.title }}</h2>
                        </div>
                        <div class="p-6">
                            <ul class="ml-4 list-disc space-y-2 text-sm leading-relaxed text-grey-2">
                                <li v-for="(item, j) in s.items" :key="j">{{ item }}</li>
                            </ul>
                        </div>
                    </div>
                </div>

                <!-- ═══ GÉNÉRAL ═══ -->
                <div v-if="activeTab === 'general'" class="space-y-5">
                    <p v-if="doc_general_intro" class="mb-4 text-sm leading-relaxed text-grey-2">{{ doc_general_intro }}</p>

                    <div v-for="(s, i) in [
                        { title: 'Modèle de paiement', items: ['Acheteur : toujours gratuit.', 'Vendeur : freemium (Free, Starter, Standard, Pro).', 'Commission de transaction : 2-5% par vente.', 'Frais de retrait : 5-10% (à revoir).', 'Consultez la page Tarifs pour les montants exacts et à jour.'] },
                        { title: 'Vérification KYC', items: ['Vendeurs : obligatoire avant de vendre.', 'Acheteurs : non requis.', 'Soumettez une pièce d\'identité valide. Vérification sous 24 à 48 heures.'] },
                        { title: 'Support et assistance', items: ['Ticket de support : depuis votre dashboard ou la page support publique.', gs.whatsapp_phone ? 'WhatsApp : ' + gs.whatsapp_phone : null, gs.contact_email ? 'Email : ' + gs.contact_email : null].filter(Boolean) },
                        { title: 'Sécurité et anti-fraude', items: ['Paiement par séquestre (escrow) : les fonds sont bloqués jusqu\'à réception.', 'Tracy IA vérifie les conversations et détecte les comportements suspects.', 'Système de litige : les acheteurs peuvent ouvrir un litige sur les commandes problématiques.', 'Géolocalisation : vérification de l\'adresse de livraison.'] },
                        { title: 'Partenaire — Bientôt disponible', items: ['Le programme partenaire permettra à des tiers de promouvoir MANTOTA.', 'Commission sur clics et ventes générées.', 'Inscriptions ouvertes prochainement.'] },
                    ]" :key="i" class="rounded-mantota-card bg-white shadow-mantota overflow-hidden">
                        <div class="border-b border-surface-3 bg-surface-2 px-6 py-4">
                            <h2 class="text-base font-bold text-grey-1">{{ s.title }}</h2>
                        </div>
                        <div class="p-6">
                            <ul class="ml-4 list-disc space-y-2 text-sm leading-relaxed text-grey-2">
                                <li v-for="(item, j) in s.items" :key="j">{{ item }}</li>
                            </ul>
                        </div>
                    </div>
                </div>

                <!-- CTA -->
                <div class="mt-10 text-center">
                    <p class="mb-4 text-sm text-grey-2">Vous avez encore des questions ?</p>
                    <a :href="route('support.create')" class="inline-flex items-center gap-2 rounded-mantota bg-mantota-teal px-6 py-3 text-sm font-bold text-white transition hover:bg-mantota-teal-dark active:scale-[0.97]">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M8.625 12a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H8.25m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H12m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0h-.375M21 12c0 4.556-4.03 8.25-9 8.25a9.764 9.764 0 01-2.555-.337A5.972 5.972 0 015.41 20.97a5.969 5.969 0 01-.474-.065 4.48 4.48 0 00.978-2.025c.09-.457-.133-.901-.467-1.226C3.93 16.178 3 14.189 3 12c0-4.556 4.03-8.25 9-8.25s9 3.694 9 8.25z" /></svg>
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
