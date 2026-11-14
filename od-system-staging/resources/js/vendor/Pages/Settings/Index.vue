<script setup>
import VendorLayout from '../../Layouts/VendorLayout.vue';
import { Head, useForm } from '@inertiajs/vue3';

const props = defineProps({
    vendor: { type: Object, required: true },
    shopUrl: { type: String, default: '' },
});

const form = useForm({
    name: props.vendor.name ?? '',
    email: props.vendor.email ?? '',
    phone: props.vendor.phone ?? '',
    shop_name: props.vendor.shop_name ?? '',
    shop_description: props.vendor.shop_description ?? '',
});

function submit() {
    form.put(route('vendor.settings.update'), { preserveScroll: true });
}

function copyShopLink() {
    navigator.clipboard.writeText(props.shopUrl);
}
</script>

<template>
    <Head title="Parametres" />

    <VendorLayout>
        <div class="max-w-2xl space-y-6">
            <h1 class="text-2xl font-extrabold text-grey-1">Parametres</h1>

            <div v-if="shopUrl" class="card-mantota bg-mantota-teal-pale">
                <div class="flex items-center justify-between">
                    <div>
                        <p class="text-xs font-semibold text-mantota-teal-dark">Lien de votre boutique</p>
                        <p class="mt-1 text-sm font-bold text-grey-1 break-all">{{ shopUrl }}</p>
                    </div>
                    <button @click="copyShopLink" class="btn-mantota flex-shrink-0">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 17.25v3.375c0 .621-.504 1.125-1.125 1.125h-9.75a1.125 1.125 0 01-1.125-1.125V7.875c0-.621.504-1.125 1.125-1.125H6.75a9.06 9.06 0 011.5.124m7.5 10.376h3.375c.621 0 1.125-.504 1.125-1.125V11.25c0-4.46-3.243-8.161-7.5-8.876a9.06 9.06 0 00-1.5-.124H9.375c-.621 0-1.125.504-1.125 1.125v3.5m7.5 10.375H9.375a1.125 1.125 0 01-1.125-1.125v-9.25m12 6.625v-1.875a3.375 3.375 0 00-3.375-3.375h-1.5a1.125 1.125 0 01-1.125-1.125v-1.5a3.375 3.375 0 00-3.375-3.375H9.75" />
                        </svg>
                        Copier
                    </button>
                </div>
            </div>

            <div class="card-mantota">
                <form @submit.prevent="submit" class="space-y-4">
                    <div>
                        <label class="label-mantota">Nom complet</label>
                        <input v-model="form.name" type="text" class="input-mantota" required />
                    </div>
                    <div class="grid grid-cols-2 gap-4">
                        <div>
                            <label class="label-mantota">Email</label>
                            <input v-model="form.email" type="email" class="input-mantota" required />
                        </div>
                        <div>
                            <label class="label-mantota">Telephone</label>
                            <input v-model="form.phone" type="tel" class="input-mantota" />
                        </div>
                    </div>
                    <div>
                        <label class="label-mantota">Nom de la boutique</label>
                        <input v-model="form.shop_name" type="text" class="input-mantota" />
                    </div>
                    <div>
                        <label class="label-mantota">Description de la boutique</label>
                        <textarea v-model="form.shop_description" rows="3" class="input-mantota"></textarea>
                    </div>
                    <button type="submit" :disabled="form.processing" class="btn-mantota">Enregistrer</button>
                </form>
            </div>
        </div>
    </VendorLayout>
</template>
