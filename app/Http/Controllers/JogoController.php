<?php

namespace App\Http\Controllers;

use App\Models\Jogo;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;

class JogoController extends Controller
{
    public function index(): JsonResponse
    {
        return response()->json(Jogo::all());
    }

    public function store(Request $request): JsonResponse
    {
        $dados = $request->validate($this->regras());

        $jogo = Jogo::create($dados);

        return response()->json($jogo, 201);
    }

    public function show(Jogo $jogo): JsonResponse
    {
        return response()->json($jogo);
    }

    public function update(Request $request, Jogo $jogo): JsonResponse
    {
        $dados = $request->validate($this->regras($jogo));

        $jogo->update($dados);

        return response()->json($jogo);
    }

    public function destroy(Jogo $jogo): JsonResponse
    {
        $jogo->delete();

        return response()->json(null, 204);
    }

    /**
     * Regras compartilhadas por store e update.
     *
     * @return array<string, mixed>
     */
    private function regras(?Jogo $existente = null): array
    {
        $obrigatorio = $existente === null ? 'required' : 'sometimes';

        return [
            'nome' => "$obrigatorio|string|max:100",
            'descricao' => 'nullable|string|max:5000',
            'genero' => 'nullable|string|max:50',
            'classificacao' => 'nullable|string|max:10',
            'desenvolvedora' => 'nullable|string|max:100',
            'data_lancamento' => 'nullable|date_format:Y-m-d',
            'capa_url' => 'nullable|string|max:2048|url',
        ];
    }
}
