<script setup>
import { Head, usePage } from '@inertiajs/vue3';
import { computed } from 'vue';
import PublicNavHeader from '@/Components/PublicNavHeader.vue';

const page = usePage();
const gs = computed(() => page.props.global_settings || {});
</script>

<template>
    <Head title="Politique de Confidentialité — MANTOTA" />

    <div class="min-h-screen bg-surface-1 text-grey-1">
        <!-- ═══ Nav Header ═══ -->
        <PublicNavHeader />

        <main class="relative mx-auto max-w-4xl px-4 py-10 sm:px-6">
            <div class="adinkra-bg absolute inset-0 pointer-events-none"></div>
            <div class="relative overflow-hidden rounded-mantota-card border border-surface-3 bg-white shadow-mantota">
                <div class="px-6 py-8 sm:px-10 sm:py-12">
                    <h1 class="mb-2 text-3xl font-bold text-grey-1">Politique de Confidentialité</h1>
                    <p class="mb-8 text-sm text-grey-2">Dernière mise à jour : Mars 2025</p>

                    <div class="prose prose-slate max-w-none prose-headings:text-grey-1 prose-p:text-grey-2 prose-li:text-grey-2">
                        <h2>1. Introduction</h2>
                        <p>La societe {{ gs.company_name || 'MANTOTA' }} accorde une grande importance a la protection des donnees personnelles de ses utilisateurs. La presente politique de confidentialite a pour objet d'informer les utilisateurs de la plateforme sur la maniere dont leurs donnees personnelles sont collectees, traitees et protegees.</p>

                        <h2>2. Données collectées</h2>
                        <p>Dans le cadre de l'utilisation de la plateforme, nous sommes amenés à collecter les catégories de données suivantes :</p>
                        <ul>
                            <li><strong>Données d'identification :</strong> nom, prénom, adresse email, numéro de téléphone</li>
                            <li><strong>Données de connexion :</strong> adresse IP, type de navigateur, pages consultées, horodatage</li>
                            <li><strong>Données de conversation :</strong> messages échangés avec Tracy IA (pour améliorer la qualité des réponses et la négociation automatique)</li>
                            <li><strong>Données financières :</strong> informations relatives aux transactions, historique des paiements et retraits</li>
                            <li><strong>Données professionnelles :</strong> informations relatives à l'activité commerciale (pour les vendeurs) ou à l'audience (pour les créateurs de contenu)</li>
                        </ul>

                        <h2>3. Finalites du traitement</h2>
                        <p>Les donnees collectees sont traitees pour les finalites suivantes :</p>
                        <ul>
                            <li>La gestion des comptes utilisateurs et l'authentification</li>
                            <li>La fourniture et l'amelioration des services de la plateforme</li>
                            <li>Le traitement des transactions financieres</li>
                            <li>La communication avec les utilisateurs (notifications, support)</li>
                            <li>Le respect des obligations legales et reglementaires</li>
                            <li>La prevention de la fraude et la securite de la plateforme</li>
                        </ul>

                        <h2>4. Base legale du traitement</h2>
                        <p>Le traitement des donnees personnelles repose sur les bases legales suivantes :</p>
                        <ul>
                            <li>L'execution du contrat liant l'utilisateur a la plateforme</li>
                            <li>Le consentement de l'utilisateur</li>
                            <li>L'interet legitime de la plateforme</li>
                            <li>Le respect d'obligations legales</li>
                        </ul>

                        <h2>5. Destinataires des donnees</h2>
                        <p>Les donnees personnelles peuvent etre communiquees aux destinataires suivants :</p>
                        <ul>
                            <li>Les equipes internes de la plateforme (support, technique, finance)</li>
                            <li>Les prestataires de services de paiement</li>
                            <li>Les autorites competentes en cas de requisition legale</li>
                        </ul>
                        <p>Les donnees ne sont jamais vendues a des tiers a des fins commerciales.</p>

                        <h2>6. Duree de conservation</h2>
                        <p>Les donnees personnelles sont conservees pendant la duree necessaire a l'accomplissement des finalites pour lesquelles elles ont ete collectees. A l'issue de cette duree, les donnees sont supprimees ou anonymisees de maniere irreversible.</p>

                        <h2>7. Securite des donnees</h2>
                        <p>La plateforme met en oeuvre des mesures techniques et organisationnelles appropriees pour proteger les donnees personnelles contre tout acces non autorise, toute modification, divulgation ou destruction. Ces mesures incluent le chiffrement des donnees sensibles, la securisation des communications et le controle des acces.</p>

                        <h2>8. Droits des utilisateurs</h2>
                        <p>Conformement a la reglementation en vigueur, chaque utilisateur dispose des droits suivants :</p>
                        <ul>
                            <li><strong>Droit d'acces :</strong> obtenir la confirmation du traitement de ses donnees et en recevoir une copie</li>
                            <li><strong>Droit de rectification :</strong> demander la correction de donnees inexactes ou incompletes</li>
                            <li><strong>Droit a l'effacement :</strong> demander la suppression de ses donnees dans les cas prevus par la loi</li>
                            <li><strong>Droit a la portabilite :</strong> recevoir ses donnees dans un format structure et couramment utilise</li>
                            <li><strong>Droit d'opposition :</strong> s'opposer au traitement de ses donnees pour des motifs legitimes</li>
                        </ul>
                        <p>Pour exercer ces droits, l'utilisateur peut nous contacter a l'adresse {{ gs.contact_email || 'contact@mantota.com' }}.</p>

                        <h2>9. Cookies</h2>
                        <p>La plateforme utilise des cookies necessaires au bon fonctionnement du service (cookies de session, cookies d'authentification). Ces cookies sont essentiels et ne necessitent pas de consentement prealable. Aucun cookie de tracking publicitaire n'est utilise.</p>

                        <h2>10. Modification de la politique</h2>
                        <p>La presente politique de confidentialite peut etre modifiee a tout moment. Les utilisateurs seront informes de toute modification substantielle. La date de derniere mise a jour est indiquee en haut de ce document.</p>

                        <h2>11. Contact</h2>
                        <p>Pour toute question relative a la protection de vos donnees personnelles, vous pouvez nous contacter :</p>
                        <ul>
                            <li>Par email : {{ gs.contact_email || 'contact@mantota.com' }}</li>
                            <li>Par courrier : {{ gs.physical_address || 'Adresse du siege social' }}</li>
                        </ul>
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
