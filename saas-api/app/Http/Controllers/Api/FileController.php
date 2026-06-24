<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use Illuminate\Http\Request;

class FileController extends Controller
{
    
    public function upload(Request $request): JsonResponse
    {
        $request->validate([
            'file' => 'required|file|max:10240', // máx 10MB
            'type' => 'in:avatar,document,image',
        ]);

        $path = $request->file('file')->store(
            'uploads/' . ($request->type ?? 'general'),
            'public'
        );

        return response()->json([
            'message' => 'Upload realizado com sucesso.',
            'url'     => asset('storage/' . $path),
            'path'    => $path,
        ], 201);
    }

    public function uploadAvatar(Request $request): JsonResponse
    {
        $request->validate([
            'avatar' => 'required|image|mimes:jpg,jpeg,png,webp|max:2048',
        ]);

        $user = $request->user();

        // Remove avatar antigo
        if ($user->avatar) {
            Storage::disk('public')->delete($user->avatar);
        }

        $path = $request->file('avatar')->store('avatars', 'public');
        $user->update(['avatar' => $path]);

        return response()->json([
            'message' => 'Avatar atualizado.',
            'url'     => asset('storage/' . $path),
        ]);
    }

    public function delete(Request $request): JsonResponse
    {
        $request->validate(['path' => 'required|string']);

        Storage::disk('public')->delete($request->path);

        return response()->json(['message' => 'Arquivo removido.']);
    }
}
