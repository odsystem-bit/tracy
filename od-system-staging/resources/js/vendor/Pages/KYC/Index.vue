<script setup>
import VendorLayout from '../../Layouts/VendorLayout.vue';
import { Head, useForm } from '@inertiajs/vue3';

const props = defineProps({
    kyc_status: { type: String, default: 'not_submitted' },
    kyc_document_front: { type: String, default: null },
    kyc_document_back: { type: String, default: null },
});

const form = useForm({ document_front: null, document_back: null });

function submit() {
    form.post(route('vendor.kyc.store'), { preserveScroll: true });
}

const statusInfo = {
    not_submitted: { label: 'Non soumis', class: 'badge-grey' },
    pending: { label: 'En cours de verification', class: 'badge-coral' },
    approved: { label: 'Verifie', class: 'badge-teal' },
    rejected: { label: 'Rejete', class: 'badge-coral' },
};
</script>

<template>
    <Head title="Verification KYC" />
    <VendorLayout>
        <div class="max-w-2xl space-y-6">
            <div>
                <h1 class="text-2xl font-extrabold text-grey-1">Verification d'identite (KYC)</h1>
                <p class="mt-1 text-sm text-grey-2">Verifiez votre identite pour debloquer toutes les fonctionnalites</p>
            </div>

            <div class="card-mantota">
                <div class="flex items-center justify-between">
                    <p class="text-sm font-semibold text-grey-2">Statut actuel</p>
                    <span :class="statusInfo[kyc_status]?.class ?? 'badge-grey'">{{ statusInfo[kyc_status]?.label ?? kyc_status }}</span>
                </div>
            </div>

            <div v-if="kyc_status === 'not_submitted' || kyc_status === 'rejected'" class="card-mantota">
                <h2 class="mb-4 text-base font-bold text-grey-1">Soumettre vos documents</h2>
                <form @submit.prevent="submit" class="space-y-4">
                    <div>
                        <label class="label-mantota">Recto de la piece d'identite</label>
                        <input @input="form.document_front = $event.target.files[0]" type="file" accept="image/jpeg,image/png,image/webp,application/pdf" class="block w-full text-sm text-grey-2 file:mr-4 file:rounded-mantota file:border-0 file:bg-mantota-teal-pale file:px-4 file:py-2.5 file:font-semibold file:text-mantota-teal-dark" required />
                    </div>
                    <div>
                        <label class="label-mantota">Verso de la piece d'identite</label>
                        <input @input="form.document_back = $event.target.files[0]" type="file" accept="image/jpeg,image/png,image/webp,application/pdf" class="block w-full text-sm text-grey-2 file:mr-4 file:rounded-mantota file:border-0 file:bg-mantota-teal-pale file:px-4 file:py-2.5 file:font-semibold file:text-mantota-teal-dark" required />
                    </div>
                    <button type="submit" :disabled="form.processing" class="btn-mantota">Soumettre</button>
                </form>
            </div>

            <div v-else class="card-mantota text-center py-8">
                <p class="text-sm text-grey-2">Vos documents ont ete soumis. Vous serez notifie du resultat.</p>
            </div>
        </div>
    </VendorLayout>
</template>
