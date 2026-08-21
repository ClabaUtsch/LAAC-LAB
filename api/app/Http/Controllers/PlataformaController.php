<?php

namespace App\Http\Controllers;

use App\Models\Plataforma;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;

class PlataformaController extends Controller
{
    public function index(): JsonResponse
    {
        return response()->json(Plataforma::all());
    }

    public function store(Request $request): JsonResponse
    {
        $dados = $request->validate($this->regras());

        $plataforma = Plataforma::create($dados);

        return response()->json($plataforma, 201);
    }

    public function show(Plataforma $plataforma): JsonResponse
    {
        return response()->json($plataforma);
    }

    public function update(Request $request, Plataforma $plataforma): JsonResponse
    {
        $dados = $request->validate($this->regras($plataforma));

        $plataforma->update($dados);

        return response()->json($plataforma);
    }

    public function destroy(Plataforma $plataforma): JsonResponse
    {
        $plataforma->delete();

        return response()->json(null, 204);
    }

    /**
     * Regras compartilhadas por store e update.
     *
     * @return array<string, mixed>
     */
    private function regras(?Plataforma $existente = null): array
    {
        $obrigatorio = $existente === null ? 'required' : 'sometimes';

        return [
            'nome' => "$obrigatorio|string|max:50",
        ];
    }
}
