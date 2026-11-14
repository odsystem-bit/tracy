<script setup>
import VendorLayout from '../Layouts/VendorLayout.vue';
import { Head, Link } from '@inertiajs/vue3';
import { computed } from 'vue';

const props = defineProps({
    stats: { type: Object, default: () => ({}) },
    recentOrders: { type: Array, default: () => [] },
    topProducts: { type: Array, default: () => [] },
    shopUrl: { type: String, default: '' },
});

const formatPrice = (v) => new Intl.NumberFormat('fr-FR').format(v || 0) + ' FCFA';

const kpis = computed(() => [
    { label: 'Ventes du mois', value: formatPrice(props.stats.monthly_revenue), icon: 'banknotes', color: 'teal' },
    { label: 'Commandes en cours', value: props.stats.pending_orders ?? 0, icon: 'clock', color: 'coral' },
    { label: 'Produits actifs', value: props.stats.active_products ?? 0, icon: 'cube', color: 'teal' },
    { label: 'Solde wallet', value: formatPrice(props.stats.wallet_balance), icon: 'wallet', color: 'teal' },
]);
</script>

<template>
    <Head title="Dashboard" />

    <VendorLayout>
        <div class="space-y-6">
            <!-- Header -->
            <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                <div>
                    <h1 class="text-2xl font-extrabold text-grey-1">Dashboard</h1>
                    <p class="mt-1 text-sm text-grey-2">Vue d'ensemble de votre activite</p>
                </div>
                <div class="flex gap-2">
                    <a v-if="shopUrl" :href="shopUrl" target="_blank" class="btn-mantota-outline">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M13.5 6H5.25A2.25 2.25 0 003 8.25v10.5A2.25 2.25 0 005.25 21h10.5A2.25 2.25 0 0018 18.75V10.5m-10.5 6L21 3m0 0h-5.25M21 3v5.25" />
                        </svg>
                        Voir ma boutique
                    </a>
                    <Link :href="route('vendor.products.create')" class="btn-mantota">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
                        </svg>
                        Ajouter un produit
                    </Link>
                </div>
            </div>

            <!-- KPIs -->
            <div class="grid grid-cols-2 gap-4 lg:grid-cols-4">
                <div v-for="kpi in kpis" :key="kpi.label" class="card-mantota">
                    <div class="flex items-center gap-3">
                        <div class="flex h-10 w-10 items-center justify-center rounded-mantota" :class="kpi.color === 'teal' ? 'bg-mantota-teal-pale text-mantota-teal-dark' : 'bg-orange-50 text-mantota-coral'">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                                <path v-if="kpi.icon === 'banknotes'" stroke-linecap="round" stroke-linejoin="round" d="M2.25 18.75a60.07 60.07 0 0115.797 2.101c.727.198 1.453-.342 1.453-1.096V18.75M3.75 4.5v.75A.75.75 0 013 6h-.75m0 0v-.375c0-.621.504-1.125 1.125-1.125H20.25M2.25 6v9m18-10.5v.75c0 .414.336.75.75.75h.75m-1.5-1.5h.375c.621 0 1.125.504 1.125 1.125V21M4.5 19.5h15M4.5 19.5v-3.375c0-.621.504-1.125 1.125-1.125h12.75c.621 0 1.125.504 1.125 1.125V19.5" />
                                <path v-else-if="kpi.icon === 'clock'" stroke-linecap="round" stroke-linejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" />
                                <path v-else-if="kpi.icon === 'cube'" stroke-linecap="round" stroke-linejoin="round" d="M21 7.5l-9-5.25L3 7.5m18 0l-9 5.25m9-5.25v9l-9 5.25M3 7.5l9 5.25M3 7.5v9l9 5.25m0-9v9" />
                                <path v-else stroke-linecap="round" stroke-linejoin="round" d="M21 12a2.25 2.25 0 00-2.25-2.25H15a3 3 0 11-6 0H5.25A2.25 2.25 0 003 12m18 0v6a2.25 2.25 0 01-2.25 2.25H5.25A2.25 2.25 0 013 18v-6m18 0V9M3 12V9m18 0a2.25 2.25 0 00-2.25-2.25H5.25A2.25 2.25 0 003 9m18 0V6a2.25 2.25 0 00-2.25-2.25H5.25A2.25 2.25 0 003 6v3" />
                            </svg>
                        </div>
                        <div>
                            <p class="text-xs font-semibold text-grey-2">{{ kpi.label }}</p>
                            <p class="text-lg font-extrabold text-grey-1">{{ kpi.value }}</p>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Recent Orders + Top Products -->
            <div class="grid gap-6 lg:grid-cols-2">
                <div class="card-mantota">
                    <div class="mb-4 flex items-center justify-between">
                        <h2 class="text-base font-bold text-grey-1">Commandes recentes</h2>
                        <Link :href="route('vendor.orders.index')" class="text-xs font-semibold text-mantota-teal-dark hover:underline">Voir tout</Link>
                    </div>
                    <div v-if="recentOrders.length" class="space-y-3">
                        <div v-for="order in recentOrders" :key="order.id" class="flex items-center justify-between border-b border-surface-3 pb-3 last:border-0">
                            <div>
                                <p class="text-sm font-semibold text-grey-1">{{ order.reference }}</p>
                                <p class="text-xs text-grey-2">{{ order.customer_name }}</p>
                            </div>
                            <div class="text-right">
                                <p class="text-sm font-bold text-grey-1">{{ formatPrice(order.total) }}</p>
                                <span class="badge-teal" v-if="order.status === 'paid'">Payee</span>
                                <span class="badge-coral" v-else-if="order.status === 'pending'">En attente</span>
                                <span class="badge-grey" v-else>{{ order.status }}</span>
                            </div>
                        </div>
                    </div>
                    <p v-else class="py-8 text-center text-sm text-grey-2">Aucune commande pour le moment</p>
                </div>

                <div class="card-mantota">
                    <div class="mb-4 flex items-center justify-between">
                        <h2 class="text-base font-bold text-grey-1">Top produits</h2>
                        <Link :href="route('vendor.products.index')" class="text-xs font-semibold text-mantota-teal-dark hover:underline">Voir tout</Link>
                    </div>
                    <div v-if="topProducts.length" class="space-y-3">
                        <div v-for="product in topProducts" :key="product.id" class="flex items-center gap-3 border-b border-surface-3 pb-3 last:border-0">
                            <img v-if="product.image_path" :src="`/storage/${product.image_path}`" :alt="product.name" class="h-12 w-12 rounded-lg object-cover" />
                            <div v-else class="flex h-12 w-12 items-center justify-center rounded-lg bg-surface-2 text-grey-4">
                                <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                                    <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 15.75l5.159-5.159a2.25 2.25 0 013.182 0l5.159 5.159m-1.5-1.5l1.409-1.409a2.25 2.25 0 013.182 0l2.909 2.909m-18 3.75h16.5a1.5 1.5 0 001.5-1.5V6a1.5 1.5 0 00-1.5-1.5H3.75A1.5 1.5 0 002.25 6v12a1.5 1.5 0 001.5 1.5zm10.5-11.25h.008v.008h-.008V8.25zm.375 0a.375.375 0 11-.75 0 .375.375 0 01.75 0z" />
                                </svg>
                            </div>
                            <div class="flex-1">
                                <p class="text-sm font-semibold text-grey-1">{{ product.name }}</p>
                                <p class="text-xs text-grey-2">{{ formatPrice(product.price) }}</p>
                            </div>
                            <span class="badge-grey">{{ product.sales_count ?? 0 }} ventes</span>
                        </div>
                    </div>
                    <p v-else class="py-8 text-center text-sm text-grey-2">Aucun produit pour le moment</p>
                </div>
            </div>
        </div>
    </VendorLayout>
</template>
