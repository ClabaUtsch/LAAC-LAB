<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{

    public function up(): void
{
    Schema::create('plans', function (Blueprint $table) {
        $table->id();
        $table->string('name');                        // ex: Basic, Pro, Enterprise
        $table->text('description')->nullable();
        $table->decimal('price', 8, 2);
        $table->integer('max_users')->default(1);
        $table->integer('storage_limit_mb')->default(500);
        $table->boolean('active')->default(true);
        $table->timestamps();
    });
}
    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('plans');
    }
};
