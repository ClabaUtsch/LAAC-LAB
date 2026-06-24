<?php

use Illuminate\Http\Request;
use Illuminate\Support\Facades\Route;
use App\Http\Controllers\Api\AuthController;
use App\Http\Controllers\Api\UserController;
use App\Http\Controllers\Api\PlanController;
use App\Http\Controllers\Api\FileController;

// Rotas públicas
Route::prefix('auth')->group(function () {
    Route::post('register', [AuthController::class, 'register']);
    Route::post('login',    [AuthController::class, 'login']);
});

// Rotas protegidas (precisa de token)
Route::middleware('auth:sanctum')->group(function () {

    Route::post('auth/logout', [AuthController::class, 'logout']);
    Route::get('auth/me',      [AuthController::class, 'me']);

    // Upload
    Route::post('files/upload',        [FileController::class, 'upload']);
    Route::post('files/avatar',        [FileController::class, 'uploadAvatar']);
    Route::delete('files',             [FileController::class, 'delete']);

    // Planos (qualquer usuário autenticado vê)
    Route::get('plans', [PlanController::class, 'index']);
    Route::get('plans/{plan}', [PlanController::class, 'show']);

    // Rotas apenas para admin
    Route::middleware('role:admin')->group(function () {
        Route::apiResource('users', UserController::class);
        Route::apiResource('plans', PlanController::class)->except(['index', 'show']);
    });

});

Route::get('/user', function (Request $request) {
    return $request->user();
})->middleware('auth:sanctum');
