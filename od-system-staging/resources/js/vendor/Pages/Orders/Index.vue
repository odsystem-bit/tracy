<script setup>
import VendorLayout from '../../Layouts/VendorLayout.vue';
import { Head, Link } from '@inertiajs/vue3';

const props = defineProps({
    orders: { type: Array, default: () => [] },
});

const formatPrice = (v) => new Intl.NumberFormat('fr-FR').format(v || 0) + ' FCFA';

const statusLabels = {
    pending: 'En attente',
    paid: 'Payee',
    shipped: 'Expediee',
    delivered: 'Livree',
    cancelled: 'Annulee',
    disputed: 'Litige',
};
</script>

<template>
    <Head title="Commandes" />

    <VendorLayout>
        <div class="space-y-6">
            <div>
                <h1 class="text-2xl font-extrabold text-grey-1">Commandes</h1>
                <p class="mt-1 text-sm text-grey-2">{{ orders.length }} commande(s)</p>
            </div>

            <div v-if="orders.length" class="card-mantota p-0 overflow-hidden">
                <div class="overflow-x-auto">
                    <table class="w-full">
                        <thead class="border-b border-surface-3 bg-surface-1">
                            <tr>
                                <th class="px-4 py-3 text-left text-xs font-semibold text-grey-2">Reference</th>
                                <th class="px-4 py-3 text-left text-xs font-semibold text-grey-2">Client</th>
                                <th class="px-4 py-3 text-left text-xs font-semibold text-grey-2">Montant</th>
                                <th class="px-4 py-3 text-left text-xs font-semibold text-grey-2">Statut</th>
                                <th class="px-4 py-3 text-left text-xs font-semibold text-grey-2">Date</th>
                                <th class="px-4 py-3"></th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-surface-3">
                            <tr v-for="order in orders" :key="order.id" class="hover:bg-surface-1">
                                <td class="px-4 py-3 text-sm font-semibold text-grey-1">{{ order.reference }}</td>
                                <td class="px-4 py-3 text-sm text-grey-2">{{ order.customer_name }}</td>
                                <td class="px-4 py-3 text-sm font-bold text-grey-1">{{ formatPrice(order.total) }}</td>
                                <td class="px-4 py-3">
                                    <span class="badge-teal" v-if="order.status === 'paid' || order.status === 'delivered'">{{ statusLabels[order.status] }}</span>
                                    <span class="badge-coral" v-else-if="order.status === 'pending' || order.status === 'disputed'">{{ statusLabels[order.status] }}</span>
                                    <span class="badge-grey" v-else>{{ statusLabels[order.status] ?? order.status }}</span>
                                </td>
                                <td class="px-4 py-3 text-sm text-grey-2">{{ order.created_at }}</td>
                                <td class="px-4 py-3 text-right">
                                    <Link :href="route('vendor.orders.show', order.id)" class="text-xs font-semibold text-mantota-teal-dark hover:underline">Details</Link>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>

            <div v-else class="card-mantota text-center py-12">
                <div class="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-surface-2 text-grey-4">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 10.5V6a3.75 3.75 0 10-7.5 0v4.5m11.356-1.993l1.263 12c.07.665-.45 1.243-1.119 1.243H4.25a1.125 1.125 0 01-1.12-1.243l1.264-12A1.125 1.125 0 015.513 7.5h12.974c.576 0 1.059.435 1.119 1.007z" />
                    </svg>
                </div>
                <h3 class="mt-4 text-base font-bold text-grey-1">Aucune commande</h3>
                <p class="mt-1 text-sm text-grey-2">Vos commandes apparaissent ici</p>
            </div>
        </div>
    </VendorLayout>
</template>
