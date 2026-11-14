<script setup>
import VendorLayout from '../../Layouts/VendorLayout.vue';
import { Head, Link, useForm } from '@inertiajs/vue3';

const props = defineProps({
    balance: { type: Number, default: 0 },
    pending: { type: Number, default: 0 },
    transactions: { type: Array, default: () => [] },
});

const formatPrice = (v) => new Intl.NumberFormat('fr-FR').format(v || 0) + ' FCFA';

const form = useForm({ amount: '' });
function withdraw() {
    form.post(route('vendor.wallet.withdraw'), { preserveScroll: true, onSuccess: () => form.reset() });
}
</script>

<template>
    <Head title="Wallet" />

    <VendorLayout>
        <div class="space-y-6">
            <h1 class="text-2xl font-extrabold text-grey-1">Wallet</h1>

            <div class="grid gap-4 sm:grid-cols-2">
                <div class="card-mantota">
                    <p class="text-xs font-semibold text-grey-2">Solde disponible</p>
                    <p class="mt-2 text-3xl font-extrabold text-mantota-teal-dark">{{ formatPrice(balance) }}</p>
                </div>
                <div class="card-mantota">
                    <p class="text-xs font-semibold text-grey-2">En attente</p>
                    <p class="mt-2 text-3xl font-extrabold text-mantota-coral">{{ formatPrice(pending) }}</p>
                </div>
            </div>

            <div class="card-mantota">
                <h2 class="mb-4 text-base font-bold text-grey-1">Demander un retrait</h2>
                <form @submit.prevent="withdraw" class="flex gap-3">
                    <input v-model="form.amount" type="number" min="1000" class="input-mantota flex-1" placeholder="Montant en FCFA" required />
                    <button type="submit" :disabled="form.processing" class="btn-mantota">Retirer</button>
                </form>
                <p v-if="form.errors.amount" class="mt-2 text-xs text-red-500">{{ form.errors.amount }}</p>
            </div>

            <div class="card-mantota">
                <h2 class="mb-4 text-base font-bold text-grey-1">Historique des transactions</h2>
                <div v-if="transactions.length" class="space-y-3">
                    <div v-for="tx in transactions" :key="tx.id" class="flex items-center justify-between border-b border-surface-3 pb-3 last:border-0">
                        <div>
                            <p class="text-sm font-semibold text-grey-1">{{ tx.type }}</p>
                            <p class="text-xs text-grey-2">{{ tx.created_at }}</p>
                        </div>
                        <p class="text-sm font-bold" :class="tx.amount >= 0 ? 'text-mantota-teal-dark' : 'text-red-500'">
                            {{ tx.amount >= 0 ? '+' : '' }}{{ formatPrice(tx.amount) }}
                        </p>
                    </div>
                </div>
                <p v-else class="py-8 text-center text-sm text-grey-2">Aucune transaction</p>
            </div>
        </div>
    </VendorLayout>
</template>
