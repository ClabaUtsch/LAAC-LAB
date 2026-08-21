<?php

namespace App\Http\Controllers;

use App\Models\BibliotecaUsuario;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Validation\Rule;

class BibliotecaUsuarioController extends Controller
{
    public function index(): JsonResponse
    {
        return response()->json(BibliotecaUsuario::all());
    }

    public function store(Request $request): JsonResponse
    {
        $dados = $request->validate($this->regras($request));

        $item = BibliotecaUsuario::create($dados);

        return response()->json($item, 201);
    }

    public function show(BibliotecaUsuario $bibliotecaUsuario): JsonResponse
    {
        return response()->json($bibliotecaUsuario);
    }

    public function update(Request $request, BibliotecaUsuario $bibliotecaUsuario): JsonResponse
    {
        $this->completaOPar($request, $bibliotecaUsuario);

        $dados = $request->validate($this->regras($request, $bibliotecaUsuario));

        $bibliotecaUsuario->update($dados);

        return response()->json($bibliotecaUsuario);
    }

    public function destroy(BibliotecaUsuario $bibliotecaUsuario): JsonResponse
    {
        $bibliotecaUsuario->delete();

        return response()->json(null, 204);
    }

    /**
     * Regras compartilhadas por store e update.
     *
     * @return array<string, mixed>
     */
    private function regras(Request $request, ?BibliotecaUsuario $existente = null): array
    {
        $obrigatorio = $existente === null ? 'required' : 'sometimes';

        $parUnico = Rule::unique('biblioteca_usuario')
            ->where(fn ($query) => $query->where(
                'usuario_id',
                $request->input('usuario_id', $existente?->usuario_id),
            ))
            ->ignore($existente);

        return [
            'usuario_id' => [$obrigatorio, 'integer', 'exists:usuarios,id'],
            'jogo_id' => [
                $obrigatorio, 'integer', 'exists:jogos,id', $parUnico,
            ],
            'favorito' => 'sometimes|boolean',
        ];
    }

    /**
     * Preenche na request as metades do par que ela nao trouxe, usando o que
     * ja esta gravado.
     *
     * Sem isto, um update que envia so usuario_id nunca dispara a checagem de
     * unicidade: ela vive nas regras de jogo_id, que o "sometimes" pula quando
     * o campo esta ausente. O par duplicado passaria pela validacao e so seria
     * barrado pelo indice unico do banco, virando 500 em vez do 422 que a
     * secao 3.8 da spec exige.
     */
    private function completaOPar(Request $request, BibliotecaUsuario $existente): void
    {
        $request->merge([
            'usuario_id' => $request->input('usuario_id', $existente->usuario_id),
            'jogo_id' => $request->input('jogo_id', $existente->jogo_id),
        ]);
    }
}
