<script setup>
import { Head, usePage } from '@inertiajs/vue3';
import { computed } from 'vue';
import PublicNavHeader from '@/Components/PublicNavHeader.vue';

const props = defineProps({
    about_mission: { type: String, default: '' },
    about_why: { type: String, default: '' },
});

const page = usePage();
const gs = computed(() => page.props.global_settings || {});
</script>

<template>
    <Head title="À propos — MANTOTA" />

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
                <h1 class="text-2xl font-bold tracking-tight text-grey-1 sm:text-3xl md:text-4xl">À propos de MANTOTA</h1>
                <p class="mx-auto mt-4 max-w-2xl text-base text-grey-2 sm:text-lg">
                    La plateforme de e-commerce intelligente propulsée par Tracy IA. Discuter, vendre, payer — automatiquement.
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

        <!-- ═══ Mission ═══ -->
        <section class="relative mx-auto max-w-4xl px-4 py-10 sm:px-6">
            <div class="adinkra-bg absolute inset-0 pointer-events-none"></div>
            <div class="relative rounded-mantota-card bg-white p-6 shadow-mantota sm:p-10">
                <h2 class="mb-4 text-xl font-bold text-grey-1 sm:text-2xl">Notre mission</h2>
                <p class="leading-relaxed text-grey-2">
                    {{ about_mission || 'MANTOTA est une plateforme de e-commerce intelligente née en Afrique francophone, propulsée par Tracy IA. Notre mission est de démocratiser la vente en ligne en offrant à chaque vendeur une assistante commerciale IA qui gère sa boutique, négocie avec ses clients et automatise ses ventes 24/7. Acheteur gratuit, vendeur freemium — aucune barrière à l\'entrée.' }}
                </p>
            </div>
        </section>

        <!-- ═══ Comment ça marche ═══ -->
        <section class="relative mx-auto max-w-6xl px-4 py-10 sm:px-6">
            <div class="adinkra-bg absolute inset-0 pointer-events-none"></div>
            <div class="relative">
                <h2 class="mb-8 text-center text-2xl font-bold text-grey-1">Comment ça marche</h2>
                <div class="grid gap-6 sm:grid-cols-3">
                    <div class="rounded-mantota-card bg-white p-6 shadow-mantota transition hover:shadow-mantota-md">
                        <div class="mb-4 flex h-12 w-12 items-center justify-center rounded-mantota bg-mantota-teal-pale">
                            <span class="text-xl font-bold text-mantota-teal-dark">1</span>
                        </div>
                        <h3 class="text-sm font-bold text-grey-1">Créez votre boutique</h3>
                        <p class="mt-2 text-xs leading-relaxed text-grey-2">Le vendeur crée sa boutique en ligne, ajoute ses produits et configure ses règles de marge.</p>
                    </div>
                    <div class="rounded-mantota-card bg-white p-6 shadow-mantota transition hover:shadow-mantota-md">
                        <div class="mb-4 flex h-12 w-12 items-center justify-center rounded-mantota bg-mantota-teal-pale">
                            <span class="text-xl font-bold text-mantota-teal-dark">2</span>
                        </div>
                        <h3 class="text-sm font-bold text-grey-1">Tracy IA prend le relais</h3>
                        <p class="mt-2 text-xs leading-relaxed text-grey-2">Tracy discute avec vos clients sur l'app et WhatsApp, négocie les prix et crée les commandes automatiquement.</p>
                    </div>
                    <div class="rounded-mantota-card bg-white p-6 shadow-mantota transition hover:shadow-mantota-md">
                        <div class="mb-4 flex h-12 w-12 items-center justify-center rounded-mantota bg-mantota-teal-pale">
                            <span class="text-xl font-bold text-mantota-teal-dark">3</span>
                        </div>
                        <h3 class="text-sm font-bold text-grey-1">Vendez en toute sécurité</h3>
                        <p class="mt-2 text-xs leading-relaxed text-grey-2">Paiement par séquestre (escrow), suivi automatique des commandes, relances clients gérées par Tracy.</p>
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
                            <p class="mt-1 text-sm text-grey-2">L'IA commerciale au cœur de MANTOTA</p>
                        </div>
                    </div>
                </div>
                <div class="mt-8 grid gap-4 sm:grid-cols-3">
                    <div class="rounded-mantota bg-white p-5 shadow-mantota">
                        <div class="flex h-10 w-10 items-center justify-center rounded-mantota bg-mantota-teal-pale mb-3">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-mantota-teal-dark" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M7.5 8.25h9m-9 3H12m-9.75 1.51c0 1.6 1.123 2.994 2.707 3.227 1.129.166 2.27.293 3.423.379.35.026.67.21.865.501L12 21l2.755-4.133a1.14 1.14 0 01.865-.501 48.172 48.172 0 003.423-.379c1.584-.233 2.707-1.626 2.707-3.228V6.741c0-1.602-1.123-2.995-2.707-3.228A48.394 48.394 0 0012 3c-2.392 0-4.744.175-7.043.513C3.373 3.746 2.25 5.14 2.25 6.741v6.018z" /></svg>
                        </div>
                        <h3 class="text-sm font-bold text-grey-1">Conversation 24/7</h3>
                        <p class="mt-1 text-xs text-grey-2">Tracy répond à vos clients jour et nuit, sur l'app et WhatsApp.</p>
                    </div>
                    <div class="rounded-mantota bg-white p-5 shadow-mantota">
                        <div class="flex h-10 w-10 items-center justify-center rounded-mantota bg-mantota-teal-pale mb-3">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-mantota-teal-dark" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M3.75 3v11.25A2.25 2.25 0 006 16.5h2.25M3.75 3h-1.5m1.5 0h16.5m0 0h1.5m-1.5 0v11.25A2.25 2.25 0 0118 16.5h-2.25m-7.5 0h7.5m-7.5 0l-1 3m8.5-3l1 3m0 0l.5 1.5m-.5-1.5h-9.5m0 0l-.5 1.5M9 11.25v1.5M12 9v3.75m3-6v6" /></svg>
                        </div>
                        <h3 class="text-sm font-bold text-grey-1">Négociation auto</h3>
                        <p class="mt-1 text-xs text-grey-2">Tracy négocie selon vos règles de marge et de remise définies.</p>
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

        <!-- ═══ Nos valeurs ═══ -->
        <section class="relative mx-auto max-w-6xl px-4 py-10 sm:px-6">
            <div class="adinkra-bg absolute inset-0 pointer-events-none"></div>
            <div class="relative">
                <h2 class="mb-8 text-center text-2xl font-bold text-grey-1">Nos valeurs</h2>
                <div class="grid gap-6 sm:grid-cols-2">
                    <div v-for="(v, i) in [
                        { title: 'Transparence', desc: 'Tous les tarifs, frais et commissions sont publics et affichés en temps réel sur la page Tarifs.', icon: 'M2.25 18.75a60.07 60.07 0 0115.797 2.101c.727.198 1.453-.342 1.453-1.096V18.75M3.75 4.5v.75A.75.75 0 013 6h-.75m0 0v-.375c0-.621.504-1.125 1.125-1.125H20.25M2.25 6v9m18-10.5v.75c0 .414.336.75.75.75h.75m-1.5-1.5h.375c.621 0 1.125.504 1.125 1.125v9.75c0 .621-.504 1.125-1.125 1.125h-.375m1.5-1.5H21a.75.75 0 00-.75.75v.75m0 0H3.75m0 0h-.375a1.125 1.125 0 01-1.125-1.125V15m1.5 1.5v-.75A.75.75 0 003 15h-.75M15 10.5a3 3 0 11-6 0 3 3 0 016 0zm3 0h.008v.008H18V10.5zm-12 0h.008v.008H6V10.5z' },
                        { title: 'Intelligence', desc: 'Tracy IA automatise les ventes : conversation, négociation, relances et suivi des commandes.', icon: 'M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 11.733l-.97 3.241-.97-3.241a3.75 3.75 0 00-2.572-2.572l-3.241-.97 3.241-.97a3.75 3.75 0 002.572-2.572l.97-3.241.97 3.241a3.75 3.75 0 002.572 2.572l3.241.97-3.241.97a3.75 3.75 0 00-2.572 2.572z' },
                        { title: 'Accessibilité', desc: 'Acheteur gratuit, vendeur freemium à partir de 0 FCFA. Aucune barrière à l\'entrée.', icon: 'M15.75 10.5V6a3.75 3.75 0 10-7.5 0v4.5m11.356-1.993l1.263 12c.07.665-.45 1.243-1.119 1.243H4.25a1.125 1.125 0 01-1.12-1.243l1.264-12A1.125 1.125 0 015.513 7.5h12.974c.576 0 1.059.435 1.119 1.007z' },
                        { title: 'Innovation africaine', desc: 'Conçu pour la réalité du marché africain — Mobile Money, WhatsApp, logistique adaptée.', icon: 'M12 21a9.004 9.004 0 008.716-6.747M12 21a9.004 9.004 0 01-8.716-6.747M12 21c2.485 0 4.5-4.03 4.5-9S14.485 3 12 3m0 18c-2.485 0-4.5-4.03-4.5-9S9.515 3 12 3m0 0a8.997 8.997 0 017.843 4.582M12 3a8.997 8.997 0 00-7.843 4.582m15.686 0A11.953 11.953 0 0112 10.5c-2.998 0-5.74-1.1-7.843-2.918m15.686 0A8.959 8.959 0 0121 12c0 .778-.099 1.533-.284 2.253m0 0A17.919 17.919 0 0112 16.5c-3.162 0-6.133-.815-8.716-2.247m0 0A9.015 9.015 0 013 12c0-1.605.42-3.113 1.157-4.418' },
                    ]" :key="i" class="flex items-start gap-4 rounded-mantota-card bg-white p-5 shadow-mantota transition hover:shadow-mantota-md">
                        <div class="mt-0.5 flex h-10 w-10 shrink-0 items-center justify-center rounded-mantota bg-mantota-teal-pale">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-mantota-teal-dark" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" :d="v.icon" /></svg>
                        </div>
                        <div>
                            <h3 class="text-sm font-bold text-grey-1">{{ v.title }}</h3>
                            <p class="mt-1 text-sm text-grey-2">{{ v.desc }}</p>
                        </div>
                    </div>
                </div>
            </div>
        </section>

        <!-- ═══ Pourquoi ═══ -->
        <section class="relative mx-auto max-w-4xl px-4 py-10 sm:px-6">
            <div class="adinkra-bg absolute inset-0 pointer-events-none"></div>
            <div class="relative rounded-mantota-card bg-white p-6 shadow-mantota sm:p-10">
                <h2 class="mb-4 text-xl font-bold text-grey-1 sm:text-2xl">Pourquoi MANTOTA ?</h2>
                <p class="leading-relaxed text-grey-2">
                    {{ about_why || 'Dans un marché où la vente en ligne est souvent complexe et coûteuse, MANTOTA apporte la simplicité grâce à Tracy IA. Plus besoin de répondre manuellement à chaque message client, de négocier pendant des heures ou de suivre les commandes sur Excel. Tracy s\'occupe de tout, automatiquement. Vous vous concentrez sur vos produits, Tracy gère le reste.' }}
                </p>
            </div>
        </section>

        <!-- ═══ Contact ═══ -->
        <section class="relative mx-auto max-w-4xl px-4 py-10 sm:px-6">
            <div class="adinkra-bg absolute inset-0 pointer-events-none"></div>
            <div class="relative rounded-mantota-card bg-white p-6 shadow-mantota sm:p-10">
                <h2 class="mb-5 text-lg font-bold text-grey-1 sm:text-xl">Nous contacter</h2>
                <div class="space-y-2 text-sm text-grey-2">
                    <p v-if="gs.contact_email" class="flex items-center gap-2">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-mantota-teal" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M21.75 6.75v10.5a2.25 2.25 0 01-2.25 2.25h-15a2.25 2.25 0 01-2.25-2.25V6.75m19.5 0A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25m19.5 0v.243a2.25 2.25 0 01-1.07 1.916l-7.5 4.615a2.25 2.25 0 01-2.36 0L3.32 8.91a2.25 2.25 0 01-1.07-1.916V6.75" /></svg>
                        <span><strong class="text-grey-1">Email :</strong> {{ gs.contact_email }}</span>
                    </p>
                    <p v-if="gs.whatsapp_phone" class="flex items-center gap-2">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-mantota-teal" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M2.25 6.75c0 8.284 6.716 15 15 15h2.25a2.25 2.25 0 002.25-2.25v-1.372c0-.516-.351-.966-.852-1.091l-4.423-1.106c-.44-.11-.902.055-1.173.417l-.97 1.293c-.282.376-.769.542-1.21.38a12.035 12.035 0 01-7.143-7.143c-.162-.441.004-.928.38-1.21l1.293-.97c.363-.271.527-.734.417-1.173L6.963 3.102a1.125 1.125 0 00-1.091-.852H4.5A2.25 2.25 0 002.25 4.5v2.25z" /></svg>
                        <span><strong class="text-grey-1">WhatsApp :</strong> {{ gs.whatsapp_phone }}</span>
                    </p>
                    <p v-if="gs.physical_address" class="flex items-center gap-2">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-mantota-teal" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M15 10.5a3 3 0 11-6 0 3 3 0 016 0z" /><path stroke-linecap="round" stroke-linejoin="round" d="M19.5 10.5c0 7.142-7.5 11.25-7.5 11.25S4.5 17.642 4.5 10.5a7.5 7.5 0 1115 0z" /></svg>
                        <span><strong class="text-grey-1">Adresse :</strong> {{ gs.physical_address }}</span>
                    </p>
                    <p v-if="gs.rccm" class="flex items-center gap-2">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-mantota-teal" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" /></svg>
                        <span><strong class="text-grey-1">RCCM :</strong> {{ gs.rccm }}</span>
                    </p>
                    <p v-if="gs.ifu" class="flex items-center gap-2">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-mantota-teal" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" /></svg>
                        <span><strong class="text-grey-1">IFU :</strong> {{ gs.ifu }}</span>
                    </p>
                </div>
                <div class="mt-6">
                    <a :href="route('support.create')" class="inline-flex items-center gap-2 rounded-mantota bg-mantota-teal px-5 py-3 text-sm font-bold text-white transition hover:bg-mantota-teal-dark active:scale-[0.97]">
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
