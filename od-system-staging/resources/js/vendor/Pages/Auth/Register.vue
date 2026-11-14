<script setup>
import { Head, Link, useForm } from '@inertiajs/vue3';

const form = useForm({
    name: '',
    email: '',
    phone: '',
    password: '',
    password_confirmation: '',
    shop_name: '',
});

function submit() {
    form.post(route('vendor.register.post'), {
        onFinish: () => form.reset('password', 'password_confirmation'),
    });
}
</script>

<template>
    <Head title="Devenir Vendeur" />

    <div class="flex min-h-screen items-center justify-center bg-surface-1 px-4 py-8">
        <div class="w-full max-w-md">
            <div class="mb-8 text-center">
                <img src="/images/logo-dark.png" alt="MANTOTA" class="mx-auto h-12 w-auto" />
                <h1 class="mt-4 text-2xl font-extrabold text-grey-1">Devenir Vendeur</h1>
                <p class="mt-1 text-sm text-grey-2">Rejoignez Mantota et commencez a vendre</p>
            </div>

            <div class="card-mantota">
                <form @submit.prevent="submit" class="space-y-4">
                    <div>
                        <label class="label-mantota">Nom complet</label>
                        <input v-model="form.name" type="text" class="input-mantota" placeholder="Jean Dupont" required />
                        <p v-if="form.errors.name" class="mt-1 text-xs text-red-500">{{ form.errors.name }}</p>
                    </div>

                    <div>
                        <label class="label-mantota">Nom de la boutique</label>
                        <input v-model="form.shop_name" type="text" class="input-mantota" placeholder="Ma Boutique" required />
                        <p v-if="form.errors.shop_name" class="mt-1 text-xs text-red-500">{{ form.errors.shop_name }}</p>
                    </div>

                    <div>
                        <label class="label-mantota">Email</label>
                        <input v-model="form.email" type="email" class="input-mantota" placeholder="vous@exemple.com" required />
                        <p v-if="form.errors.email" class="mt-1 text-xs text-red-500">{{ form.errors.email }}</p>
                    </div>

                    <div>
                        <label class="label-mantota">Telephone</label>
                        <input v-model="form.phone" type="tel" class="input-mantota" placeholder="+229 90 00 00 00" required />
                        <p v-if="form.errors.phone" class="mt-1 text-xs text-red-500">{{ form.errors.phone }}</p>
                    </div>

                    <div>
                        <label class="label-mantota">Mot de passe</label>
                        <input v-model="form.password" type="password" class="input-mantota" placeholder="••••••••" required />
                        <p v-if="form.errors.password" class="mt-1 text-xs text-red-500">{{ form.errors.password }}</p>
                    </div>

                    <div>
                        <label class="label-mantota">Confirmer le mot de passe</label>
                        <input v-model="form.password_confirmation" type="password" class="input-mantota" placeholder="••••••••" required />
                    </div>

                    <button type="submit" :disabled="form.processing" class="btn-mantota w-full">
                        <span v-if="form.processing">Creation...</span>
                        <span v-else>Creer mon compte</span>
                    </button>
                </form>

                <div class="mt-6 border-t border-surface-3 pt-4 text-center">
                    <p class="text-sm text-grey-2">Deja vendeur ?</p>
                    <Link :href="route('vendor.login')" class="mt-2 inline-block btn-mantota-outline w-full">Se connecter</Link>
                </div>
            </div>

            <div class="mt-6 text-center">
                <Link :href="route('home')" class="text-xs font-semibold text-grey-2 hover:text-mantota-teal-dark">← Retour au site</Link>
            </div>
        </div>
    </div>
</template>
