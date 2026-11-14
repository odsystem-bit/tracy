<script setup>
import VendorLayout from '../../Layouts/VendorLayout.vue';
import { Head, Link, useForm } from '@inertiajs/vue3';

const props = defineProps({
    products: { type: Array, default: () => [] },
    shopUrl: { type: String, default: '' },
});

const formatPrice = (v) => new Intl.NumberFormat('fr-FR').format(v || 0) + ' FCFA';

const form = useForm({});

function deleteProduct(id) {
    if (confirm('Supprimer ce produit ?')) {
        form.delete(route('vendor.products.destroy', id), { preserveScroll: true });
    }
}
</script>

<template>
    <Head title="Mes Produits" />

    <VendorLayout>
        <div class="space-y-6">
            <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                <div>
                    <h1 class="text-2xl font-extrabold text-grey-1">Mes Produits</h1>
                    <p class="mt-1 text-sm text-grey-2">{{ products.length }} produit(s) au total</p>
                </div>
                <Link :href="route('vendor.products.create')" class="btn-mantota">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
                    </svg>
                    Ajouter un produit
                </Link>
            </div>

            <div v-if="products.length" class="card-mantota p-0 overflow-hidden">
                <div class="overflow-x-auto">
                    <table class="w-full">
                        <thead class="border-b border-surface-3 bg-surface-1">
                            <tr>
                                <th class="px-4 py-3 text-left text-xs font-semibold text-grey-2">Produit</th>
                                <th class="px-4 py-3 text-left text-xs font-semibold text-grey-2">Prix</th>
                                <th class="px-4 py-3 text-left text-xs font-semibold text-grey-2">Stock</th>
                                <th class="px-4 py-3 text-left text-xs font-semibold text-grey-2">Statut</th>
                                <th class="px-4 py-3 text-right text-xs font-semibold text-grey-2">Actions</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-surface-3">
                            <tr v-for="product in products" :key="product.id" class="hover:bg-surface-1 transition-colors">
                                <td class="px-4 py-3">
                                    <div class="flex items-center gap-3">
                                        <img v-if="product.image_path" :src="`/storage/${product.image_path}`" :alt="product.name" class="h-10 w-10 rounded-lg object-cover" />
                                        <div v-else class="flex h-10 w-10 items-center justify-center rounded-lg bg-surface-2 text-grey-4">
                                            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                                                <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 15.75l5.159-5.159a2.25 2.25 0 013.182 0l5.159 5.159m-1.5-1.5l1.409-1.409a2.25 2.25 0 013.182 0l2.909 2.909m-18 3.75h16.5a1.5 1.5 0 001.5-1.5V6a1.5 1.5 0 00-1.5-1.5H3.75A1.5 1.5 0 002.25 6v12a1.5 1.5 0 001.5 1.5z" />
                                            </svg>
                                        </div>
                                        <span class="text-sm font-semibold text-grey-1">{{ product.name }}</span>
                                    </div>
                                </td>
                                <td class="px-4 py-3 text-sm font-bold text-grey-1">{{ formatPrice(product.price) }}</td>
                                <td class="px-4 py-3 text-sm text-grey-2">{{ product.stock ?? 'N/A' }}</td>
                                <td class="px-4 py-3">
                                    <span v-if="product.status === 'active'" class="badge-teal">Actif</span>
                                    <span v-else-if="product.status === 'out_of_stock'" class="badge-coral">Rupture</span>
                                    <span v-else class="badge-grey">{{ product.status }}</span>
                                </td>
                                <td class="px-4 py-3">
                                    <div class="flex justify-end gap-2">
                                        <Link :href="route('vendor.products.edit', product.id)" class="rounded-lg p-2 text-grey-2 hover:bg-surface-2 hover:text-mantota-teal-dark">
                                            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                                                <path stroke-linecap="round" stroke-linejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931z" />
                                            </svg>
                                        </Link>
                                        <button @click="deleteProduct(product.id)" class="rounded-lg p-2 text-grey-2 hover:bg-red-50 hover:text-red-600">
                                            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                                                <path stroke-linecap="round" stroke-linejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
                                            </svg>
                                        </button>
                                    </div>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>

            <div v-else class="card-mantota text-center py-12">
                <div class="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-surface-2 text-grey-4">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M21 7.5l-9-5.25L3 7.5m18 0l-9 5.25m9-5.25v9l-9 5.25M3 7.5l9 5.25M3 7.5v9l9 5.25m0-9v9" />
                    </svg>
                </div>
                <h3 class="mt-4 text-base font-bold text-grey-1">Aucun produit</h3>
                <p class="mt-1 text-sm text-grey-2">Commencez a vendre en ajoutant votre premier produit</p>
                <Link :href="route('vendor.products.create')" class="btn-mantota mt-4">
                    Ajouter un produit
                </Link>
            </div>
        </div>
    </VendorLayout>
</template>
