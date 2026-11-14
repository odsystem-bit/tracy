<?php

declare(strict_types=1);

namespace App\Console\Commands;

use App\Services\Payment\PaymentService;
use Illuminate\Console\Command;

class MonerooTestCommand extends Command
{
    protected $signature = 'moneroo:test {--amount=100} {--phone=} {--email=} {--api=} {--payout : Tester un payout au lieu d\'un paiement}';

    protected $description = 'Teste la connectivité et la configuration Moneroo';

    public function handle(): int
    {
        $config = PaymentService::resolveApiConfig();

        $this->info('URL API : ' . $config['api_url']);
        $this->info('Clé publique : ' . ($config['public_key'] ? substr($config['public_key'], 0, 8) . '...' : 'NON DÉFINIE'));
        $this->info('Clé secrète : ' . ($config['secret_key'] ? substr($config['secret_key'], 0, 8) . '...' : 'NON DÉFINIE'));
        $this->info('Webhook secret : ' . ($config['webhook_secret'] ? substr($config['webhook_secret'], 0, 8) . '...' : 'NON DÉFINI'));

        if (empty($config['secret_key'])) {
            $this->error('La clé secrète Moneroo est manquante.');
            return self::FAILURE;
        }

        if ($this->option('payout')) {
            if (! $this->option('phone')) {
                $this->error('Précisez --phone pour tester un payout.');
                return self::FAILURE;
            }

            $phone = $this->option('phone');
            $result = PaymentService::initializePayout(
                phone: $phone,
                amount: (int) $this->option('amount'),
                currency: config('services.moneroo.currency', 'XOF'),
                reference: 'TEST-PAYOUT-' . time(),
                description: 'Test payout Mantota',
                country: 'BJ',
            );

            if (! $result['success']) {
                $this->error('Payout test échoué : ' . ($result['message'] ?? 'réponse invalide'));
                dump($result['response'] ?? null);
                return self::FAILURE;
            }

            $this->info('Payout test initié avec succès.');
            dump($result['response'] ?? $result);
            return self::SUCCESS;
        }

        $result = PaymentService::initializePayment([
            'amount'      => (int) $this->option('amount'),
            'description' => 'Test de connectivité Mantota',
            'customer'    => [
                'first_name' => 'Test',
                'email'      => $this->option('email') ?: 'test@example.com',
                'phone'      => $this->option('phone') ?: '0000000000',
            ],
            'return_url'  => config('app.url') . '/moneroo/test-return',
            'metadata'    => [
                'type'      => 'test',
                'reference' => 'TEST-' . time(),
            ],
        ]);

        if (! $result['success']) {
            $this->error('Paiement test échoué : ' . ($result['message'] ?? 'réponse invalide'));
            dump($result['response'] ?? null);
            return self::FAILURE;
        }

        $this->info('Paiement test initié avec succès.');
        dump($result['response'] ?? $result);

        return self::SUCCESS;
    }
}
