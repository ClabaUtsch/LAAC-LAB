<?php

namespace App\Http\Controllers;

use App\Models\Avaliacao;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;

class AvaliacaoController extends Controller
{
    public function index(): JsonResponse
    {
        return response()->json(Avaliacao::all());
    }

    public function store(Request $request): JsonResponse
    {
        $dados = $request->validate($this->regras());

        $avaliacao = Avaliacao::create($dados);

        return response()->json($avaliacao, 201);
    }

    public function show(Avaliacao $avaliacao): JsonResponse
    {
        return response()->json($avaliacao);
    }

    public function update(Request $request, Avaliacao $avaliacao): JsonResponse
    {
        $dados = $request->validate($this->regras($avaliacao));

        $avaliacao->update($dados);

        return response()->json($avaliacao);
    }

    public function destroy(Avaliacao $avaliacao): JsonResponse
    {
        $avaliacao->delete();

        return response()->json(null, 204);
    }

    /**
     * Regras compartilhadas por store e update. Esta tabela nao tem
     * constraint de unicidade, entao nao precisa da Request.
     *
     * @return array<string, mixed>
     */
    private function regras(?Avaliacao $existente = null): array
    {
        $obrigatorio = $existente === null ? 'required' : 'sometimes';

        return [
            'usuario_id' => "$obrigatorio|integer|exists:usuarios,id",
            'jogo_id' => "$obrigatorio|integer|exists:jogos,id",
            // decimal(2,1) representa no maximo 9.9.
            'nota' => 'nullable|numeric|min:0|max:9.9|decimal:0,1',
            'comentario' => 'nullable|string|max:5000',
        ];
    }
}
