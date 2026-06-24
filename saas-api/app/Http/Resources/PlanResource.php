<?php

namespace App\Http\Resources;

use Illuminate\Http\Request;
use Illuminate\Http\Resources\Json\JsonResource;

class PlanResource extends JsonResource
{
    /**
     * Transform the resource into an array.
     *
     * @return array<string, mixed>
     */
    public function toArray(Request $request): array
    {
        return [
            'id'               => $this->id,
            'name'             => $this->name,
            'description'      => $this->description,
            'price'            => 'R$ ' . number_format($this->price, 2, ',', '.'),
            'max_users'        => $this->max_users,
            'storage_limit_mb' => $this->storage_limit_mb,
            'active'           => $this->active,
        ];
    }
}
