<?php

namespace App\Http\Controllers;

use App\Models\Usuario;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Validation\Rule;

class UsuarioController extends Controller
{
    public function index(): JsonResponse
    {
        return response()->json(Usuario::all());
    }

    public function store(Request $request): JsonResponse
    {
        $dados = $request->validate($this->regras());

        $usuario = Usuario::create($this->trocaSenhaPelaColuna($dados));

        return response()->json($usuario, 201);
    }

    public function show(Usuario $usuario): JsonResponse
    {
        return response()->json($usuario);
    }

    public function update(Request $request, Usuario $usuario): JsonResponse
    {
        $dados = $request->validate($this->regras($usuario));

        $usuario->update($this->trocaSenhaPelaColuna($dados));

        return response()->json($usuario);
    }

    public function destroy(Usuario $usuario): JsonResponse
    {
        $usuario->delete();

        return response()->json(null, 204);
    }

    /**
     * Regras compartilhadas por store e update. Passar $existente troca
     * "required" por "sometimes" e faz as checagens de unicidade ignorarem
     * o proprio registro.
     *
     * @return array<string, mixed>
     */
    private function regras(?Usuario $existente = null): array
    {
        $obrigatorio = $existente === null ? 'required' : 'sometimes';

        return [
            'nome_usuario' => [
                $obrigatorio, 'string', 'max:50',
                Rule::unique('usuarios', 'nome_usuario')->ignore($existente),
            ],
            'email' => [
                $obrigatorio, 'email', 'max:100',
                Rule::unique('usuarios', 'email')->ignore($existente),
            ],
            'senha' => "$obrigatorio|string|min:8",
            'idade' => 'nullable|integer|min:0|max:150',
            'avatar_url' => 'nullable|string|max:2048|url',
            'bio' => 'nullable|string|max:5000',
            'nivel' => 'sometimes|integer|min:1',
        ];
    }

    /**
     * A API recebe "senha" em texto puro; a coluna e "senha_hash".
     * O hash em si e aplicado pelo cast "hashed" do model.
     *
     * @param  array<string, mixed>  $dados
     * @return array<string, mixed>
     */
    private function trocaSenhaPelaColuna(array $dados): array
    {
        if (isset($dados['senha'])) {
            $dados['senha_hash'] = $dados['senha'];
            unset($dados['senha']);
        }

        return $dados;
    }
}
