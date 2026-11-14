<script setup>
import { ref, computed } from 'vue';
import { usePage } from '@inertiajs/vue3';

const page = usePage();
const gs = computed(() => page.props.global_settings || {});
const mobileMenuOpen = ref(false);

const navLinks = [
    { label: 'Accueil', route: 'home' },
    { label: 'À propos', route: 'about' },
    { label: 'Tarifs', route: 'tarifs' },
    { label: 'Documentation', route: 'documentation' },
    { label: 'Support', route: 'support.create' },
];
</script>

<template>
    <nav class="sticky top-0 z-50 border-b border-surface-3 bg-white/90 backdrop-blur-xl">
        <div class="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6">
            <!-- Left: MANTOTA logo -->
            <a :href="route('home')" class="flex items-center gap-2.5">
                <img src="/images/mantota-logo.png" alt="MANTOTA" class="h-9 w-9 rounded-xl" />
                <span class="text-base font-extrabold tracking-tight text-grey-1 hidden sm:inline">MANTOTA</span>
            </a>

            <!-- Center: Nav links (desktop) -->
            <div class="hidden items-center gap-5 md:flex">
                <a
                    v-for="link in navLinks"
                    :key="link.route"
                    :href="route(link.route)"
                    class="text-sm font-semibold text-grey-2 transition-colors hover:text-mantota-teal-dark"
                >{{ link.label }}</a>
            </div>

            <!-- Right: Tracy avatar -->
            <div class="flex items-center gap-3">
                <a :href="route('home')" class="hidden items-center gap-2 rounded-mantota px-3 py-1.5 text-sm font-semibold text-grey-2 transition-colors hover:bg-surface-1 sm:inline-flex">
                    <span class="text-xs text-grey-2">Discuter avec</span>
                    <div class="relative">
                        <img src="/images/tracy-avatar.jpeg" alt="Tracy" class="h-7 w-7 rounded-full object-cover ring-2 ring-mantota-teal/30" />
                        <span class="absolute -bottom-0.5 -right-0.5 h-2.5 w-2.5 rounded-full bg-mantota-teal ring-2 ring-white"></span>
                    </div>
                    <span class="text-xs font-bold text-grey-1">Tracy</span>
                </a>

                <!-- Mobile menu button -->
                <button @click="mobileMenuOpen = !mobileMenuOpen" class="rounded-lg p-2 text-grey-2 hover:bg-surface-1 md:hidden">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                        <path v-if="!mobileMenuOpen" stroke-linecap="round" stroke-linejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5" />
                        <path v-else stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                </button>
            </div>
        </div>

        <!-- Mobile menu -->
        <Transition
            enter-active-class="transition duration-200 ease-out"
            enter-from-class="opacity-0 -translate-y-2"
            enter-to-class="opacity-100 translate-y-0"
            leave-active-class="transition duration-150 ease-in"
            leave-from-class="opacity-100 translate-y-0"
            leave-to-class="opacity-0 -translate-y-2"
        >
            <div v-if="mobileMenuOpen" class="border-t border-surface-3 bg-white/95 backdrop-blur-xl md:hidden">
                <div class="space-y-1 px-4 py-4">
                    <a
                        v-for="link in navLinks"
                        :key="link.route"
                        :href="route(link.route)"
                        @click="mobileMenuOpen = false"
                        class="block rounded-mantota px-3 py-2 text-sm font-semibold text-grey-2 hover:bg-surface-1 hover:text-grey-1"
                    >{{ link.label }}</a>
                    <div class="mt-3 flex items-center gap-2 border-t border-surface-3 pt-3">
                        <img src="/images/tracy-avatar.jpeg" alt="Tracy" class="h-8 w-8 rounded-full object-cover ring-2 ring-mantota-teal/30" />
                        <div>
                            <p class="text-xs font-bold text-grey-1">Tracy IA</p>
                            <p class="text-[10px] text-mantota-teal font-semibold">En ligne</p>
                        </div>
                    </div>
                </div>
            </div>
        </Transition>
    </nav>
</template>
