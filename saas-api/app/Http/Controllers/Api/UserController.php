<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use Illuminate\Http\Request;

class UserController extends Controller
{
    /**
     * Display a listing of the resource.
     */
    public function index()
    {
         $users = User::query()
            // Filtro por nome ou email
            ->when($request->search, fn($q) =>
                $q->where('name', 'like', "%{$request->search}%")
                  ->orWhere('email', 'like', "%{$request->search}%")
            )
            // Filtro por role
            ->when($request->role, fn($q) =>
                $q->role($request->role)
            )
            // Filtro por status
            ->when($request->filled('active'), fn($q) =>
                $q->where('active', $request->boolean('active'))
            )
            ->with('subscription.plan')
            ->paginate($request->per_page ?? 15);

        return response()->json([
            'data'  => UserResource::collection($users),
            'meta'  => [
                'total'        => $users->total(),
                'current_page' => $users->currentPage(),
                'last_page'    => $users->lastPage(),
                'per_page'     => $users->perPage(),
            ],
        ]);
    }

    /**
     * Store a newly created resource in storage.
     */
    public function store(Request $request)
    {
        //
    }

    /**
     * Display the specified resource.
     */
    public function show(string $id)
    {
         return response()->json(new UserResource($user->load('subscription.plan')));
    }

    public function update(Request $request, User $user): JsonResponse
    {
        $user->update($request->only('name', 'active'));

        if ($request->role) {
            $user->syncRoles($request->role);
        }

        return response()->json(new UserResource($user));
    }

    /**
     * Remove the specified resource from storage.
     */
    public function destroy(string $id)
    {
        
        $user->delete();
        return response()->json(['message' => 'Usuário removido.']);
    }
    }

