<script setup>
import VendorLayout from '../../Layouts/VendorLayout.vue';
import { Head, Link } from '@inertiajs/vue3';

const props = defineProps({ order: { type: Object, required: true } });
const formatPrice = (v) => new Intl.NumberFormat('fr-FR').format(v || 0) + ' FCFA';
</script>

<template>
    <Head title="Commande" />

    <VendorLayout>
        <div class="max-w-3xl space-y-6">
            <div class="flex items-center gap-4">
                <Link :href="route('vendor.orders.index')" class="rounded-lg p-2 text-grey-2 hover:bg-surface-2">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M10.5 19.5L3 12m7.5 7.5L3 12m7.5 7.5L3 12" />
                    </svg>
                </Link>
                <h1 class="text-2xl font-extrabold text-grey-1">Commande {{ order.reference }}</h1>
            </div>

            <div class="card-mantota">
                <dl class="grid grid-cols-2 gap-4">
                    <div><dt class="text-xs font-semibold text-grey-2">Client</dt><dd class="text-sm font-bold text-grey-1">{{ order.customer_name }}</dd></div>
                    <div><dt class="text-xs font-semibold text-grey-2">Date</dt><dd class="text-sm font-bold text-grey-1">{{ order.created_at }}</dd></div>
                    <div><dt class="text-xs font-semibold text-grey-2">Montant</dt><dd class="text-sm font-bold text-grey-1">{{ formatPrice(order.total) }}</dd></div>
                    <div><dt class="text-xs font-semibold text-grey-2">Statut</dt><dd><span class="badge-teal">{{ order.status }}</span></dd></div>
                </dl>
            </div>

            <div v-if="order.items?.length" class="card-mantota">
                <h2 class="mb-4 text-base font-bold text-grey-1">Articles</h2>
                <div class="space-y-3">
                    <div v-for="item in order.items" :key="item.id" class="flex items-center justify-between border-b border-surface-3 pb-3 last:border-0">
                        <div>
                            <p class="text-sm font-semibold text-grey-1">{{ item.name }}</p>
                            <p class="text-xs text-grey-2">Quantite: {{ item.quantity }}</p>
                        </div>
                        <p class="text-sm font-bold text-grey-1">{{ formatPrice(item.price * item.quantity) }}</p>
                    </div>
                </div>
            </div>
        </div>
    </VendorLayout>
</template>
