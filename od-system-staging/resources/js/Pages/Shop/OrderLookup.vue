<script setup>
import { Head, router, usePage } from '@inertiajs/vue3';
import { ref, computed } from 'vue';

const page = usePage();
const errors = computed(() => page.props.errors || {});

const form = ref({
    identifier: '',
    reference: '',
});

const submitting = ref(false);

function submit() {
    submitting.value = true;
    router.post(route('order.lookup.submit'), form.value, {
        preserveScroll: true,
        onFinish: () => { submitting.value = false; },
    });
}
</script>

<template>
    <Head title="Retrouver ma commande" />

    <div class="min-h-screen bg-surface-1 text-grey-1">
        <!-- Header -->
        <header class="relative overflow-hidden bg-white border-b border-surface-3">
            <div class="absolute inset-0 opacity-[0.07]">
                <div class="absolute left-1/4 top-0 h-[400px] w-[400px] rounded-full bg-mantota-teal blur-[100px]" />
            </div>
            <div class="relative mx-auto max-w-2xl px-4 py-12 sm:px-6 sm:py-16 text-center">
                <a :href="route('home')" class="mb-6 inline-flex items-center gap-2 text-sm font-semibold text-grey-2 transition hover:text-mantota-teal-dark">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18" /></svg>
                    MANTOTA
                </a>
                <div class="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-mantota-card bg-mantota-teal-pale ring-1 ring-mantota-teal/20">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8 text-mantota-teal-dark" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
                    </svg>
                </div>
                <h1 class="text-2xl font-bold tracking-tight text-grey-1 sm:text-3xl">Retrouver ma commande</h1>
                <p class="mt-3 text-base text-grey-2">Entrez votre email ou numéro de téléphone et la référence de votre commande pour la suivre.</p>
            </div>
        </header>

        <!-- Form -->
        <main class="mx-auto max-w-md px-4 py-10 sm:px-6">
            <form @submit.prevent="submit" class="rounded-mantota-card bg-white p-6 shadow-mantota sm:p-8">
                <!-- Identifier -->
                <div class="mb-5">
                    <label for="identifier" class="block text-sm font-semibold text-grey-1 mb-2">Email ou téléphone</label>
                    <input
                        id="identifier"
                        v-model="form.identifier"
                        type="text"
                        required
                        placeholder="ex: jean@email.com ou +229 51 00 00 00"
                        class="w-full rounded-mantota border border-surface-4 bg-surface-1 px-4 py-3 text-sm text-grey-1 placeholder:text-surface-4 focus:border-mantota-teal focus:ring-2 focus:ring-mantota-teal/20 focus:outline-none transition"
                        :class="{ 'border-mantota-coral focus:border-mantota-coral focus:ring-mantota-coral/20': errors.identifier }"
                    />
                    <p v-if="errors.identifier" class="mt-1.5 text-xs text-mantota-coral">{{ errors.identifier }}</p>
                </div>

                <!-- Reference -->
                <div class="mb-6">
                    <label for="reference" class="block text-sm font-semibold text-grey-1 mb-2">Référence de commande</label>
                    <input
                        id="reference"
                        v-model="form.reference"
                        type="text"
                        required
                        placeholder="ex: MNT-2024-00123"
                        class="w-full rounded-mantota border border-surface-4 bg-surface-1 px-4 py-3 text-sm text-grey-1 placeholder:text-surface-4 focus:border-mantota-teal focus:ring-2 focus:ring-mantota-teal/20 focus:outline-none transition"
                        :class="{ 'border-mantota-coral focus:border-mantota-coral focus:ring-mantota-coral/20': errors.reference }"
                    />
                    <p v-if="errors.reference" class="mt-1.5 text-xs text-mantota-coral">{{ errors.reference }}</p>
                </div>

                <!-- Submit -->
                <button
                    type="submit"
                    :disabled="submitting"
                    class="flex w-full items-center justify-center gap-2 rounded-mantota bg-mantota-teal px-4 py-3 text-sm font-bold text-white transition hover:bg-mantota-teal-dark active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    <svg v-if="!submitting" xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" /></svg>
                    <svg v-else class="h-4 w-4 animate-spin" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg>
                    {{ submitting ? 'Recherche...' : 'Trouver ma commande' }}
                </button>
            </form>

            <!-- Help -->
            <div class="mt-6 rounded-mantota border border-surface-3 bg-white p-5 text-center">
                <p class="text-sm text-grey-2">
                    Pas de référence ? Vérifiez votre boîte mail ou
                    <a :href="route('home')" class="font-semibold text-mantota-teal-dark hover:underline">contactez le support</a>.
                </p>
            </div>
        </main>

        <!-- Footer -->
        <footer class="border-t border-surface-3 bg-white py-8">
            <div class="mx-auto max-w-6xl px-4 sm:px-6 text-center">
                <p class="text-xs text-grey-2">
                    Propulsé par
                    <span class="font-bold text-mantota-teal-dark">MANTOTA</span>
                    — Assistante commerciale IA
                </p>
            </div>
        </footer>
    </div>
</template>
