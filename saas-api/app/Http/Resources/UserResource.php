<?php

namespace App\Http\Resources;

use Illuminate\Http\Request;
use Illuminate\Http\Resources\Json\JsonResource;

class UserResource extends JsonResource
{

    public function toArray($request): array
    {
        return [
            'id'           => $this->id,
            'name'         => $this->name,
            'email'        => $this->email,
            'avatar'       => $this->avatar ? asset('storage/' . $this->avatar) : null,
            'active'       => $this->active,
            'roles'        => $this->getRoleNames(),
            'subscription' => new SubscriptionResource($this->whenLoaded('subscription')),
            'created_at'   => $this->created_at->format('d/m/Y'),
        ];
    }
}
