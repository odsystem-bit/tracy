<script setup>
import { Head, usePage } from '@inertiajs/vue3';
import { computed } from 'vue';
import PublicNavHeader from '@/Components/PublicNavHeader.vue';

const page = usePage();
const gs = computed(() => page.props.global_settings || {});
</script>

<template>
    <Head title="Conditions Générales de Vente — MANTOTA" />

    <div class="min-h-screen bg-surface-1 text-grey-1">
        <!-- ═══ Nav Header ═══ -->
        <PublicNavHeader />

        <main class="relative mx-auto max-w-4xl px-4 py-10 sm:px-6">
            <div class="adinkra-bg absolute inset-0 pointer-events-none"></div>
            <div class="relative overflow-hidden rounded-mantota-card border border-surface-3 bg-white shadow-mantota">
                <div class="px-6 py-8 sm:px-10 sm:py-12">
                    <h1 class="mb-2 text-3xl font-bold text-grey-1">Conditions Générales de Vente</h1>
                    <p class="mb-8 text-sm text-grey-2">Dernière mise à jour : Mars 2025</p>

                    <div class="prose prose-slate max-w-none prose-headings:text-grey-1 prose-p:text-grey-2 prose-li:text-grey-2">
                        <h2>1. Objet</h2>
                        <p>Les presentes conditions generales de vente (ci-apres "CGV") regissent l'ensemble des relations commerciales entre la societe {{ gs.company_name || 'MANTOTA' }}, immatriculee sous le RCCM {{ gs.rccm || 'N/A' }} et l'IFU {{ gs.ifu || 'N/A' }}, dont le siege social est situe a {{ gs.physical_address || 'N/A' }}, et toute personne physique ou morale (ci-apres "l'Utilisateur") accedant a la plateforme.</p>

                        <h2>2. Acces a la plateforme</h2>
                        <p>L'acces a la plateforme est ouvert a toute personne disposant d'une connexion Internet. L'inscription en tant que Vendeur ou Createur de Contenu est soumise a l'acceptation des presentes CGV. La plateforme se reserve le droit de refuser l'inscription de tout utilisateur sans avoir a motiver sa decision.</p>
                        <p>L'utilisateur s'engage a fournir des informations exactes et a jour lors de son inscription. Toute utilisation frauduleuse du compte pourra entrainer la suspension ou la suppression immediate du compte.</p>

                        <h2>3. Services proposés</h2>
                        <p>La plateforme MANTOTA propose un service de e-commerce intelligent propulsé par Tracy IA, une assistante commerciale conversationnelle. Les services incluent notamment :</p>
                        <ul>
                            <li>La création et la gestion de boutiques en ligne par les vendeurs</li>
                            <li>L'assistant IA Tracy qui discute avec les clients, négocie les prix et crée les commandes automatiquement</li>
                            <li>Le suivi des performances et des ventes en temps réel</li>
                            <li>La gestion des paiements par séquestre (escrow) et des litiges</li>
                            <li>L'intégration WhatsApp pour une communication 24/7 avec les clients</li>
                        </ul>

                        <h2>4. Tarification et paiement</h2>
                        <p>Les tarifs applicables sont indiqués sur la page Tarifs de la plateforme. L'acheteur est toujours gratuit. Le vendeur dispose d'un modèle freemium (Free, Starter, Standard, Pro) avec des fonctionnalités croissantes. Une commission de transaction de 2-5% s'applique sur chaque vente.</p>
                        <p>Les paiements sont sécurisés par séquestre (escrow) : les fonds de l'acheteur sont bloqués jusqu'à confirmation de réception du produit. Les fonds sont ensuite libérés au vendeur. Tracy IA gère automatiquement ce processus.</p>

                        <h2>5. Retrait des fonds</h2>
                        <p>Les utilisateurs peuvent demander le retrait de leurs fonds disponibles sous reserve d'atteindre le montant minimum de retrait fixe par la plateforme. Les demandes de retrait sont traitees dans un delai raisonnable. Des frais de retrait peuvent s'appliquer conformement aux conditions en vigueur.</p>

                        <h2>6. Obligations des utilisateurs</h2>
                        <p>Chaque utilisateur s'engage a :</p>
                        <ul>
                            <li>Respecter les lois et reglements en vigueur</li>
                            <li>Ne pas utiliser la plateforme a des fins frauduleuses ou illicites</li>
                            <li>Ne pas manipuler artificiellement les metriques de performance</li>
                            <li>Respecter les droits de propriete intellectuelle de tiers</li>
                            <li>Maintenir la confidentialite de ses identifiants de connexion</li>
                        </ul>

                        <h2>7. Responsabilite</h2>
                        <p>La plateforme met en oeuvre les moyens necessaires pour assurer un service de qualite. Toutefois, la plateforme ne saurait etre tenue responsable des dommages directs ou indirects resultant de l'utilisation du service, notamment en cas d'interruption temporaire du service pour maintenance ou pour toute autre raison technique.</p>

                        <h2>8. Propriete intellectuelle</h2>
                        <p>L'ensemble des elements constituant la plateforme (textes, images, logos, logiciels, base de donnees) est protege par les dispositions legales en vigueur relatives a la propriete intellectuelle. Toute reproduction, representation ou exploitation non autorisee est strictement interdite.</p>

                        <h2>9. Protection des donnees personnelles</h2>
                        <p>La collecte et le traitement des donnees personnelles sont effectues conformement a notre Politique de confidentialite, accessible depuis la plateforme. L'utilisateur dispose d'un droit d'acces, de rectification et de suppression de ses donnees personnelles.</p>

                        <h2>10. Modification des CGV</h2>
                        <p>La plateforme se reserve le droit de modifier les presentes CGV a tout moment. Les utilisateurs seront informes de toute modification substantielle. La poursuite de l'utilisation de la plateforme apres modification vaut acceptation des nouvelles conditions.</p>

                        <h2>11. Contact</h2>
                        <p>Pour toute question relative aux presentes CGV, vous pouvez nous contacter a l'adresse email {{ gs.contact_email || 'contact@mantota.com' }} ou via notre formulaire de support.</p>
                    </div>
                </div>
            </div>
        </main>

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
