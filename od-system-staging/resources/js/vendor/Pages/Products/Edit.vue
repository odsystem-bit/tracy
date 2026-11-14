<script setup>
import VendorLayout from '../../Layouts/VendorLayout.vue';
import { Head, Link, useForm } from '@inertiajs/vue3';

const props = defineProps({
    product: { type: Object, required: true },
    categories: { type: Array, default: () => [] },
});

const form = useForm({
    name: props.product.name,
    description: props.product.description ?? '',
    price: props.product.price,
    stock: props.product.stock ?? '',
    category_id: props.product.category_id ?? '',
    image: null,
});

function submit() {
    form.put(route('vendor.products.update', props.product.id), { preserveScroll: true });
}
</script>

<template>
    <Head title="Modifier le Produit" />

    <VendorLayout>
        <div class="max-w-2xl space-y-6">
            <div class="flex items-center gap-4">
                <Link :href="route('vendor.products.index')" class="rounded-lg p-2 text-grey-2 hover:bg-surface-2">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M10.5 19.5L3 12m7.5 7.5L3 12m7.5 7.5L3 12" />
                    </svg>
                </Link>
                <h1 class="text-2xl font-extrabold text-grey-1">Modifier le produit</h1>
            </div>

            <div class="card-mantota">
                <form @submit.prevent="submit" class="space-y-4">
                    <div>
                        <label class="label-mantota">Nom du produit</label>
                        <input v-model="form.name" type="text" class="input-mantota" required />
                    </div>
                    <div>
                        <label class="label-mantota">Description</label>
                        <textarea v-model="form.description" rows="4" class="input-mantota"></textarea>
                    </div>
                    <div class="grid grid-cols-2 gap-4">
                        <div>
                            <label class="label-mantota">Prix (FCFA)</label>
                            <input v-model="form.price" type="number" min="0" class="input-mantota" required />
                        </div>
                        <div>
                            <label class="label-mantota">Stock</label>
                            <input v-model="form.stock" type="number" min="0" class="input-mantota" />
                        </div>
                    </div>
                    <div v-if="categories.length">
                        <label class="label-mantota">Categorie</label>
                        <select v-model="form.category_id" class="input-mantota">
                            <option value="">Choisir...</option>
                            <option v-for="cat in categories" :key="cat.id" :value="cat.id">{{ cat.name }}</option>
                        </select>
                    </div>
                    <div>
                        <label class="label-mantota">Nouvelle image (optionnel)</label>
                        <input @input="form.image = $event.target.files[0]" type="file" accept="image/*" class="block w-full text-sm text-grey-2 file:mr-4 file:rounded-mantota file:border-0 file:bg-mantota-teal-pale file:px-4 file:py-2.5 file:text-sm file:font-semibold file:text-mantota-teal-dark" />
                    </div>
                    <div class="flex gap-3 pt-2">
                        <button type="submit" :disabled="form.processing" class="btn-mantota flex-1">Enregistrer</button>
                        <Link :href="route('vendor.products.index')" class="btn-mantota-ghost">Annuler</Link>
                    </div>
                </form>
            </div>
        </div>
    </VendorLayout>
</template>
