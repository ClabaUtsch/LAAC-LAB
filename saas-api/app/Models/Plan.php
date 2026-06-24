<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class Plan extends Model
{
    protected $fillable = [
        'name', 'description', 'price', 'max_users', 'storage_limit_mb', 'active',
    ];

    protected $casts = [
        'active' => 'boolean',
        'price'  => 'decimal:2',
    ];

    public function subscriptions()
    {
        return $this->hasMany(Subscription::class);
    }
}