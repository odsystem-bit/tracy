<script setup>
import { ref, computed } from 'vue';
import { Link, router, usePage } from '@inertiajs/vue3';
import NotificationBell from '../../Components/NotificationBell.vue';

const page = usePage();
const gs = computed(() => page.props.global_settings || {});
const mobileOpen = ref(false);
const currentUrl = computed(() => page.url);

const isImpersonating = computed(() => page.props.admin_impersonating ?? false);

const navItems = [
    { label: 'Dashboard', route: 'vendor.dashboard', icon: 'home' },
    { label: 'Produits', route: 'vendor.products.index', icon: 'cube' },
    { label: 'Commandes', route: 'vendor.orders.index', icon: 'shopping-bag' },
    { label: 'Campagnes', route: 'vendor.campaigns.index', icon: 'megaphone' },
    { label: 'Wallet', route: 'vendor.wallet.index', icon: 'wallet' },
    { label: 'Studios', route: 'vendor.studios.index', icon: 'film' },
    { label: 'KYC', route: 'vendor.kyc.index', icon: 'badge-check' },
    { label: 'Parametres', route: 'vendor.settings.index', icon: 'cog' },
];

function stopImpersonating() {
    router.post(route('admin.impersonate.stop'));
}

const icons = {
    home: 'M2.25 12l8.954-8.955c.44-.439 1.152-.439 1.591 0L21.75 12M4.5 9.75v10.125c0 .621.504 1.125 1.125 1.125H9.75v-4.875c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21h4.125c.621 0 1.125-.504 1.125-1.125V9.75M8.25 21h8.25',
    cube: 'M21 7.5l-9-5.25L3 7.5m18 0l-9 5.25m9-5.25v9l-9 5.25M3 7.5l9 5.25M3 7.5v9l9 5.25m0-9v9',
    'shopping-bag': 'M15.75 10.5V6a3.75 3.75 0 10-7.5 0v4.5m11.356-1.993l1.263 12c.07.665-.45 1.243-1.119 1.243H4.25a1.125 1.125 0 01-1.12-1.243l1.264-12A1.125 1.125 0 015.513 7.5h12.974c.576 0 1.059.435 1.119 1.007zM8.625 10.5a.375.375 0 11-.75 0 .375.375 0 01.75 0zm7.5 0a.375.375 0 11-.75 0 .375.375 0 01.75 0z',
    megaphone: 'M10.34 15.84c-.688-.06-1.386-.09-2.09-.09H7.5a4.5 4.5 0 110-9h.75c.704 0 1.402-.03 2.09-.09m0 9.18c.253.962.584 1.892.985 2.783.247.55.06 1.21-.463 1.511l-.657.38c-.551.318-1.26.117-1.527-.461a7.013 7.013 0 01-.985-2.783m0-9.18c-.253-.962-.584-1.892-.985-2.783-.247-.55-.06-1.21.463-1.511l.657-.38c.551-.318 1.26-.117 1.527.461a7.013 7.013 0 01.985 2.783m0 9.18c.832.246 1.704.378 2.59.378h.09c.85 0 1.673-.122 2.455-.35m-6.645-9.18c.832-.246 1.704-.378 2.59-.378h.09c.85 0 1.673.122 2.455.35',
    wallet: 'M21 12a2.25 2.25 0 00-2.25-2.25H15a3 3 0 11-6 0H5.25A2.25 2.25 0 003 12m18 0v6a2.25 2.25 0 01-2.25 2.25H5.25A2.25 2.25 0 013 18v-6m18 0V9M3 12V9m18 0a2.25 2.25 0 00-2.25-2.25H5.25A2.25 2.25 0 003 9m18 0V6a2.25 2.25 0 00-2.25-2.25H5.25A2.25 2.25 0 003 6v3',
    film: 'M3.375 19.5h17.25m-17.25 0a1.125 1.125 0 01-1.125-1.125V3.375c0-.621.504-1.125 1.125-1.125h17.25c.621 0 1.125.504 1.125 1.125v15c0 .621-.504 1.125-1.125 1.125m-17.25 0h17.25m-17.25 0a1.125 1.125 0 01-1.125-1.125V3.375c0-.621.504-1.125 1.125-1.125h17.25c.621 0 1.125.504 1.125 1.125v15c0 .621-.504 1.125-1.125 1.125M6.75 6.75h.008v.008H6.75V6.75zm0 10.5h.008v.008H6.75v-.008zm10.5-10.5h.008v.008h-.008V6.75zm0 10.5h.008v.008h-.008v-.008z',
    'badge-check': 'M9 12.75L11.25 15 15 9.75M21 12c0 1.268-.63 2.39-1.593 3.068a3.745 3.745 0 01-1.043 3.296 3.745 3.745 0 01-3.296 1.043A3.745 3.745 0 0112 21c-1.268 0-2.39-.63-3.068-1.593a3.746 3.746 0 01-3.296-1.043 3.745 3.745 0 01-1.043-3.296A3.745 3.745 0 013 12c0-1.268.63-2.39 1.593-3.068a3.745 3.745 0 011.043-3.296 3.746 3.746 0 013.296-1.043A3.746 3.746 0 0112 3c1.268 0 2.39.63 3.068 1.593a3.746 3.746 0 013.296 1.043 3.746 3.746 0 011.043 3.296A3.745 3.745 0 0121 12z',
    cog: 'M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.324.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 011.37.49l1.296 2.247a1.125 1.125 0 01-.26 1.431l-1.003.827c-.293.241-.438.613-.43.992a7.723 7.723 0 010 .255c-.008.378.137.75.43.991l1.004.827c.424.35.534.955.26 1.43l-1.298 2.247a1.125 1.125 0 01-1.369.491l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.47 6.47 0 01-.22.128c-.331.183-.581.495-.644.869l-.213 1.281c-.09.543-.56.94-1.11.94h-2.594c-.55 0-1.019-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52 6.52 0 01-.22-.127c-.325-.196-.72-.257-1.076-.124l-1.217.456a1.125 1.125 0 01-1.369-.49l-1.297-2.247a1.125 1.125 0 01.26-1.431l1.004-.827c.292-.24.437-.613.43-.991a6.932 6.932 0 010-.255c.007-.38-.138-.751-.43-.992l-1.004-.827a1.125 1.125 0 01-.26-1.43l1.297-2.247a1.125 1.125 0 011.37-.491l1.216.456c.356.133.751.072 1.076-.124.072-.044.146-.086.22-.128.332-.183.582-.495.644-.869l.214-1.28z M15 12a3 3 0 11-6 0 3 3 0 016 0z',
};
</script>

<template>
    <div class="min-h-screen bg-surface-1">
        <!-- ══════ Sidebar Desktop ══════ -->
        <aside class="fixed inset-y-0 left-0 z-40 hidden w-64 bg-white border-r border-surface-3 md:flex md:flex-col">
            <div class="flex h-16 items-center gap-3 border-b border-surface-3 px-5">
                <img :src="gs.site_logo_dark || '/images/logo-dark.png'" alt="MANTOTA" class="h-8 w-auto object-contain" />
                <span class="text-xs font-semibold text-grey-2">Espace Vendeur</span>
            </div>

            <nav class="flex-1 space-y-1 overflow-y-auto px-3 py-4">
                <Link
                    v-for="item in navItems"
                    :key="item.route"
                    :href="route(item.route)"
                    :class="[
                        'flex items-center gap-3 rounded-mantota px-3 py-2.5 text-sm font-semibold transition-all',
                        currentUrl.startsWith(route(item.route, {}, false).split('/').slice(0, -1).join('/'))
                            ? 'bg-mantota-teal-pale text-mantota-teal-dark'
                            : 'text-grey-2 hover:bg-surface-1 hover:text-grey-1'
                    ]"
                >
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" :d="icons[item.icon]" />
                    </svg>
                    {{ item.label }}
                </Link>
            </nav>

            <div class="border-t border-surface-3 p-3">
                <Link :href="route('home')" class="flex items-center gap-3 rounded-mantota px-3 py-2.5 text-sm font-semibold text-grey-2 hover:bg-surface-1 hover:text-grey-1 transition-all">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 12l8.954-8.955c.44-.439 1.152-.439 1.591 0L21.75 12M4.5 9.75v10.125c0 .621.504 1.125 1.125 1.125H9.75v-4.875c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21h4.125c.621 0 1.125-.504 1.125-1.125V9.75" />
                    </svg>
                    Retour au site
                </Link>
            </div>
        </aside>

        <!-- ══════ Mobile Header ══════ -->
        <header class="fixed inset-x-0 top-0 z-40 flex h-16 items-center justify-between border-b border-surface-3 bg-white px-4 md:hidden">
            <img :src="gs.site_logo_dark || '/images/logo-dark.png'" alt="MANTOTA" class="h-7 w-auto" />
            <button @click="mobileOpen = !mobileOpen" class="rounded-lg p-2 text-grey-2 hover:bg-surface-1">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                    <path v-if="!mobileOpen" stroke-linecap="round" stroke-linejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5" />
                    <path v-else stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
            </button>
        </header>

        <!-- Mobile drawer -->
        <Transition
            enter-active-class="transition duration-200 ease-out"
            enter-from-class="opacity-0"
            enter-to-class="opacity-100"
            leave-active-class="transition duration-150 ease-in"
            leave-from-class="opacity-100"
            leave-to-class="opacity-0"
        >
            <div v-if="mobileOpen" class="fixed inset-0 z-30 bg-black/30 md:hidden" @click="mobileOpen = false" />
        </Transition>
        <Transition
            enter-active-class="transition duration-200 ease-out"
            enter-from-class="-translate-x-full"
            enter-to-class="translate-x-0"
            leave-active-class="transition duration-150 ease-in"
            leave-from-class="translate-x-0"
            leave-to-class="-translate-x-full"
        >
            <aside v-if="mobileOpen" class="fixed inset-y-0 left-0 z-40 w-64 bg-white md:hidden">
                <div class="flex h-16 items-center gap-3 border-b border-surface-3 px-5">
                    <img :src="gs.site_logo_dark || '/images/logo-dark.png'" alt="MANTOTA" class="h-7 w-auto" />
                </div>
                <nav class="space-y-1 px-3 py-4">
                    <Link
                        v-for="item in navItems"
                        :key="item.route"
                        :href="route(item.route)"
                        @click="mobileOpen = false"
                        class="flex items-center gap-3 rounded-mantota px-3 py-2.5 text-sm font-semibold text-grey-2 hover:bg-surface-1 hover:text-grey-1"
                    >
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" :d="icons[item.icon]" />
                        </svg>
                        {{ item.label }}
                    </Link>
                </nav>
            </aside>
        </Transition>

        <!-- ══════ Main Content ══════ -->
        <div class="md:pl-64">
            <header class="hidden h-16 items-center justify-between border-b border-surface-3 bg-white px-6 md:flex">
                <div class="flex items-center gap-4">
                    <NotificationBell />
                </div>
                <div class="flex items-center gap-3">
                    <button
                        v-if="isImpersonating"
                        @click="stopImpersonating"
                        class="rounded-lg bg-red-50 px-3 py-1.5 text-xs font-semibold text-red-600 hover:bg-red-100"
                    >
                        Stop Ghost Mode
                    </button>
                    <Link :href="route('vendor.settings.index')" class="flex items-center gap-2 rounded-lg px-3 py-1.5 text-sm font-semibold text-grey-2 hover:bg-surface-1">
                        <div class="h-8 w-8 rounded-full bg-mantota-teal-pale flex items-center justify-center text-sm font-bold text-mantota-teal-dark">
                            {{ $page.props.auth?.vendor?.name?.charAt(0).toUpperCase() ?? 'V' }}
                        </div>
                        <span class="hidden lg:inline">{{ $page.props.auth?.vendor?.name ?? 'Vendeur' }}</span>
                    </Link>
                </div>
            </header>

            <main class="min-h-[calc(100vh-4rem)] p-4 pt-20 md:p-6 md:pt-6">
                <slot />
            </main>
        </div>
    </div>
</template>
