<script setup>
import { Head, Link, useForm } from '@inertiajs/vue3';
const props = defineProps({ token: String, email: String });
const form = useForm({ token: props.token, email: props.email, password: '', password_confirmation: '' });
function submit() { form.post(route('vendor.password.update'), { onFinish: () => form.reset('password', 'password_confirmation') }); }
</script>
<template>
    <Head title="Nouveau mot de passe" />
    <div class="flex min-h-screen items-center justify-center bg-surface-1 px-4">
        <div class="w-full max-w-md">
            <div class="mb-8 text-center">
                <img src="/images/logo-dark.png" alt="MANTOTA" class="mx-auto h-12 w-auto" />
                <h1 class="mt-4 text-2xl font-extrabold text-grey-1">Nouveau mot de passe</h1>
            </div>
            <div class="card-mantota">
                <form @submit.prevent="submit" class="space-y-4">
                    <div><label class="label-mantota">Email</label><input v-model="form.email" type="email" class="input-mantota" required /></div>
                    <div><label class="label-mantota">Mot de passe</label><input v-model="form.password" type="password" class="input-mantota" required /></div>
                    <div><label class="label-mantota">Confirmer</label><input v-model="form.password_confirmation" type="password" class="input-mantota" required /></div>
                    <button type="submit" :disabled="form.processing" class="btn-mantota w-full">Reinitialiser</button>
                </form>
            </div>
        </div>
    </div>
</template>
