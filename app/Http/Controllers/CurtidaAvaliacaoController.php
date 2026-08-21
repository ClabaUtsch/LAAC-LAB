<?php

namespace App\Http\Controllers;

use App\Models\CurtidaAvaliacao;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Validation\Rule;

class CurtidaAvaliacaoController extends Controller
{
    public function index(): JsonResponse
    {
        return response()->json(CurtidaAvaliacao::all());
    }

    public function store(Request $request): JsonResponse
    {
        $dados = $request->validate($this->regras($request));

        $curtida = CurtidaAvaliacao::create($dados);

        return response()->json($curtida, 201);
    }

    public function show(CurtidaAvaliacao $curtidaAvaliacao): JsonResponse
    {
        return response()->json($curtidaAvaliacao);
    }

    public function update(Request $request, CurtidaAvaliacao $curtidaAvaliacao): JsonResponse
    {
        $this->completaOPar($request, $curtidaAvaliacao);

        $dados = $request->validate($this->regras($request, $curtidaAvaliacao));

        $curtidaAvaliacao->update($dados);

        return response()->json($curtidaAvaliacao);
    }

    public function destroy(CurtidaAvaliacao $curtidaAvaliacao): JsonResponse
    {
        $curtidaAvaliacao->delete();

        return response()->json(null, 204);
    }

    /**
     * Regras compartilhadas por store e update.
     *
     * @return array<string, mixed>
     */
    private function regras(Request $request, ?CurtidaAvaliacao $existente = null): array
    {
        $obrigatorio = $existente === null ? 'required' : 'sometimes';

        $parUnico = Rule::unique('curtidas_avaliacoes')
            ->where(fn ($query) => $query->where(
                'avaliacao_id',
                $request->input('avaliacao_id', $existente?->avaliacao_id),
            ))
            ->ignore($existente);

        return [
            'avaliacao_id' => [$obrigatorio, 'integer', 'exists:avaliacoes,id'],
            'usuario_id' => [
                $obrigatorio, 'integer', 'exists:usuarios,id', $parUnico,
            ],
        ];
    }

    /**
     * Preenche na request as metades do par que ela nao trouxe, usando o que
     * ja esta gravado.
     *
     * Sem isto, um update que envia so avaliacao_id nunca dispara a checagem
     * de unicidade: ela vive nas regras de usuario_id, que o "sometimes" pula
     * quando o campo esta ausente. O par duplicado passaria pela validacao e
     * so seria barrado pelo indice unico do banco, virando 500 em vez do 422
     * que a secao 3.8 da spec exige.
     */
    private function completaOPar(Request $request, CurtidaAvaliacao $existente): void
    {
        $request->merge([
            'avaliacao_id' => $request->input('avaliacao_id', $existente->avaliacao_id),
            'usuario_id' => $request->input('usuario_id', $existente->usuario_id),
        ]);
    }
}
