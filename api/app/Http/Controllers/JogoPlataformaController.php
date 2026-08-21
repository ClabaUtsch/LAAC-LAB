<?php

namespace App\Http\Controllers;

use App\Models\JogoPlataforma;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Validation\Rule;

class JogoPlataformaController extends Controller
{
    public function index(): JsonResponse
    {
        return response()->json(JogoPlataforma::all());
    }

    public function store(Request $request): JsonResponse
    {
        $dados = $request->validate($this->regras($request));

        $vinculo = JogoPlataforma::create($dados);

        return response()->json($vinculo, 201);
    }

    public function show(JogoPlataforma $jogoPlataforma): JsonResponse
    {
        return response()->json($jogoPlataforma);
    }

    public function update(Request $request, JogoPlataforma $jogoPlataforma): JsonResponse
    {
        $this->completaOPar($request, $jogoPlataforma);

        $dados = $request->validate($this->regras($request, $jogoPlataforma));

        $jogoPlataforma->update($dados);

        return response()->json($jogoPlataforma);
    }

    public function destroy(JogoPlataforma $jogoPlataforma): JsonResponse
    {
        $jogoPlataforma->delete();

        return response()->json(null, 204);
    }

    /**
     * Regras compartilhadas por store e update. Passar $existente troca
     * "required" por "sometimes" e faz a checagem de unicidade ignorar o
     * proprio registro.
     *
     * @return array<string, mixed>
     */
    private function regras(Request $request, ?JogoPlataforma $existente = null): array
    {
        $obrigatorio = $existente === null ? 'required' : 'sometimes';

        // O par (jogo_id, plataforma_id) e unico. A regra pendura a checagem
        // em plataforma_id, comparando contra o jogo_id que veio na request
        // (ou o ja gravado, num update parcial).
        $parUnico = Rule::unique('jogos_plataformas')
            ->where(fn ($query) => $query->where(
                'jogo_id',
                $request->input('jogo_id', $existente?->jogo_id),
            ))
            ->ignore($existente);

        return [
            'jogo_id' => [$obrigatorio, 'integer', 'exists:jogos,id'],
            'plataforma_id' => [
                $obrigatorio, 'integer', 'exists:plataformas,id', $parUnico,
            ],
        ];
    }

    /**
     * Preenche na request as metades do par que ela nao trouxe, usando o que
     * ja esta gravado.
     *
     * Sem isto, um update que envia so jogo_id nunca dispara a checagem de
     * unicidade: ela vive nas regras de plataforma_id, que o "sometimes" pula
     * quando o campo esta ausente. O par duplicado passaria pela validacao e
     * so seria barrado pelo indice unico do banco, virando 500 em vez do 422
     * que a secao 3.8 da spec exige.
     */
    private function completaOPar(Request $request, JogoPlataforma $existente): void
    {
        $request->merge([
            'jogo_id' => $request->input('jogo_id', $existente->jogo_id),
            'plataforma_id' => $request->input('plataforma_id', $existente->plataforma_id),
        ]);
    }
}
