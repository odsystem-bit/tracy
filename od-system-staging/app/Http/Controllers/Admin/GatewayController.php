<?php

declare(strict_types=1);

namespace App\Http\Controllers\Admin;

use App\Http\Controllers\Controller;
use App\Models\Gateway;
use Illuminate\Http\RedirectResponse;
use Illuminate\Http\Request;
use Inertia\Inertia;
use Inertia\Response as InertiaResponse;

class GatewayController extends Controller
{
    /**
     * Champs sensibles jamais renvoyes au navigateur.
     */
    private const SECRET_FIELDS = ['public_key', 'secret_key', 'webhook_secret'];

    public function index(): InertiaResponse
    {
        // Seule Moneroo est supportee par le code applicatif : les anciennes
        // passerelles restent en base pour l'historique mais ne sont plus
        // exposees ici afin d'eviter une reactivation accidentelle.
        $gateways = Gateway::where('slug', 'moneroo')->orderBy('priority')->orderBy('name')->get()
            ->map(function (Gateway $gateway): array {
                return [
                    'id'                 => $gateway->id,
                    'name'               => $gateway->name,
                    'slug'               => $gateway->slug,
                    'is_active'          => $gateway->is_active,
                    'environment'        => $gateway->environment,
                    'countries'          => $gateway->countries ?? [],
                    'payin_fee'          => $gateway->payin_fee,
                    'payout_fee'         => $gateway->payout_fee,
                    'priority'           => $gateway->priority,
                    'supports_refund'    => $gateway->supports_refund,
                    'supports_payout'    => $gateway->supports_payout,
                    'has_public_key'     => filled($gateway->public_key),
                    'has_secret_key'     => filled($gateway->secret_key),
                    'has_webhook_secret' => filled($gateway->webhook_secret),
                ];
            })
            ->values();

        return Inertia::render('Gateways/Index', [
            'gateways'   => $gateways,
            'webhookUrl' => url('/webhooks/moneroo'),
        ]);
    }

    public function update(Request $request, Gateway $gateway): RedirectResponse
    {
        // Seule Moneroo est configurable : refuser toute tentative de
        // reactivation d'une passerelle legacy non supportee par le code.
        abort_unless($gateway->slug === 'moneroo', 404);

        $validated = $request->validate([
            'is_active'        => ['required', 'boolean'],
            'public_key'       => ['nullable', 'string', 'max:500'],
            'secret_key'       => ['nullable', 'string', 'max:500'],
            'webhook_secret'   => ['nullable', 'string', 'max:500'],
            'environment'      => ['required', 'string', 'in:sandbox,live'],
            'countries'        => ['nullable', 'array'],
            'countries.*'      => ['string', 'size:2'],
            'payin_fee'        => ['nullable', 'numeric', 'min:0', 'max:99'],
            'payout_fee'       => ['nullable', 'numeric', 'min:0', 'max:99'],
            'priority'         => ['nullable', 'integer', 'min:1', 'max:100'],
            'supports_refund'  => ['nullable', 'boolean'],
            'supports_payout'  => ['nullable', 'boolean'],
        ]);

        // Un champ secret laisse vide signifie « ne pas changer » : on evite
        // d'ecraser une cle deja enregistree par une valeur nulle.
        foreach (self::SECRET_FIELDS as $field) {
            if (blank($validated[$field] ?? null)) {
                unset($validated[$field]);
            }
        }

        $gateway->update($validated);

        return back()->with('success', "Passerelle {$gateway->name} mise à jour.");
    }
}
