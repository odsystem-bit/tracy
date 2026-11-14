<script setup>
import { Head, Link, useForm } from '@inertiajs/vue3';
const form = useForm({ email: '' });
function submit() { form.post(route('vendor.password.email')); }
</script>
<template>
    <Head title="Mot de passe oublie" />
    <div class="flex min-h-screen items-center justify-center bg-surface-1 px-4">
        <div class="w-full max-w-md">
            <div class="mb-8 text-center">
                <img src="/images/logo-dark.png" alt="MANTOTA" class="mx-auto h-12 w-auto" />
                <h1 class="mt-4 text-2xl font-extrabold text-grey-1">Mot de passe oublie</h1>
            </div>
            <div class="card-mantota">
                <form @submit.prevent="submit" class="space-y-4">
                    <div>
                        <label class="label-mantota">Email</label>
                        <input v-model="form.email" type="email" class="input-mantota" required />
                    </div>
                    <button type="submit" :disabled="form.processing" class="btn-mantota w-full">Envoyer le lien</button>
                </form>
                <div class="mt-4 text-center">
                    <Link :href="route('vendor.login')" class="text-xs font-semibold text-mantota-teal-dark hover:underline">← Retour a la connexion</Link>
                </div>
            </div>
        </div>
    </div>
</template>
