<script setup>
import { Head, Link, useForm } from '@inertiajs/vue3';

const form = useForm({
    email: '',
    password: '',
    remember: false,
});

function submit() {
    form.post(route('vendor.login.post'), {
        onFinish: () => form.reset('password'),
    });
}
</script>

<template>
    <Head title="Connexion Vendeur" />

    <div class="flex min-h-screen items-center justify-center bg-surface-1 px-4">
        <div class="w-full max-w-md">
            <div class="mb-8 text-center">
                <img src="/images/logo-dark.png" alt="MANTOTA" class="mx-auto h-12 w-auto" />
                <h1 class="mt-4 text-2xl font-extrabold text-grey-1">Espace Vendeur</h1>
                <p class="mt-1 text-sm text-grey-2">Connectez-vous pour gerer votre boutique</p>
            </div>

            <div class="card-mantota">
                <form @submit.prevent="submit" class="space-y-4">
                    <div>
                        <label class="label-mantota">Email</label>
                        <input v-model="form.email" type="email" class="input-mantota" placeholder="vous@exemple.com" required />
                        <p v-if="form.errors.email" class="mt-1 text-xs text-red-500">{{ form.errors.email }}</p>
                    </div>

                    <div>
                        <label class="label-mantota">Mot de passe</label>
                        <input v-model="form.password" type="password" class="input-mantota" placeholder="••••••••" required />
                        <p v-if="form.errors.password" class="mt-1 text-xs text-red-500">{{ form.errors.password }}</p>
                    </div>

                    <div class="flex items-center justify-between">
                        <label class="flex items-center gap-2 text-sm text-grey-2">
                            <input v-model="form.remember" type="checkbox" class="rounded border-surface-4 text-mantota-teal focus:ring-mantota-teal" />
                            Se souvenir de moi
                        </label>
                        <Link :href="route('vendor.password.request')" class="text-xs font-semibold text-mantota-teal-dark hover:underline">Mot de passe oublie ?</Link>
                    </div>

                    <button type="submit" :disabled="form.processing" class="btn-mantota w-full">
                        <span v-if="form.processing">Connexion...</span>
                        <span v-else>Se connecter</span>
                    </button>
                </form>

                <div class="mt-6 border-t border-surface-3 pt-4 text-center">
                    <p class="text-sm text-grey-2">Pas encore vendeur ?</p>
                    <Link :href="route('vendor.register')" class="mt-2 inline-block btn-mantota-outline w-full">Creer un compte</Link>
                </div>
            </div>

            <div class="mt-6 text-center">
                <Link :href="route('home')" class="text-xs font-semibold text-grey-2 hover:text-mantota-teal-dark">← Retour au site</Link>
            </div>
        </div>
    </div>
</template>
